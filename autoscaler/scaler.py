import logging
import time
from datetime import datetime
from autoscaler.state.s3_state import get_last_scaling_time


def calculate_new_task_count(
        current_task_count,
        total_messages,
        messages_per_task,
        total_messages_combined,
        min_tasks,
        max_tasks,
        scale_up_threshold,
        scale_down_threshold,
        tasks_per_message,
        max_scale_down_factor
):
    """Calculate the new task count based on scaling rules."""
    logging.info(
        f"Calculating new task count with current_task_count={current_task_count}, total_messages={total_messages}, "
        f"messages_per_task={messages_per_task}, total_messages_combined={total_messages_combined}")
    logging.info(
        f"Using parameters: SCALE_UP_THRESHOLD={scale_up_threshold}, SCALE_DOWN_THRESHOLD={scale_down_threshold}, "
        f"TASKS_PER_MESSAGE={tasks_per_message}, MAX_SCALE_DOWN_FACTOR={max_scale_down_factor}")

    # If messages per task is above scale up threshold
    if total_messages > scale_up_threshold:
        # Calculate additional tasks needed based on total messages
        additional_tasks_needed = int(total_messages * tasks_per_message)

        # If we have messages, ensure we add at least one task
        if total_messages > 0 and additional_tasks_needed == 0:
            additional_tasks_needed = 1
            logging.info(f"Ensuring minimum scaling of at least 1 task since we have {total_messages} messages")

        # Add the additional tasks to current count
        new_task_count = current_task_count + additional_tasks_needed
        logging.info(f"Scaling up: Messages ({total_messages}) > threshold ({scale_up_threshold}). "
                     f"Adding {additional_tasks_needed} tasks. New count: {new_task_count}")

        # Apply MAX_TASKS constraint
        return min(max_tasks, new_task_count)

    # If messages per task is below scale down threshold
    elif total_messages < scale_down_threshold:
        # Calculate based on message count
        target_tasks = max(min_tasks, int(total_messages * tasks_per_message))

        # Don't scale down by more than the configurable factor at once
        min_tasks_after_scaling = int(current_task_count * max_scale_down_factor)
        final_task_count = max(target_tasks, min_tasks_after_scaling)

        logging.info(f"Scaling down: Messages ({total_messages}) < threshold ({scale_down_threshold}). "
                     f"Target based on messages: {target_tasks}, minimum after scaling: {min_tasks_after_scaling}, "
                     f"final count: {final_task_count}")

        return final_task_count

    # No scaling needed
    logging.info(f"No scaling needed. Current tasks: {current_task_count}, messages: {total_messages}")
    return current_task_count


def can_scale(
        aws_wrapper,
        action_type,
        current_task_count,
        new_task_count,
        s3_config_bucket,
        ecs_cluster,
        service_name,
        scale_out_cooldown,
        scale_in_cooldown
):
    """
    Check if we can scale based on cooldown period.

    Args:
        aws_wrapper: AWS wrapper instance
        action_type: 'up' or 'down' scaling action
        current_task_count: Current number of tasks
        new_task_count: Proposed new number of tasks
        s3_config_bucket: S3 bucket for state storage
        ecs_cluster: ECS cluster name
        service_name: ECS service name
        scale_out_cooldown: Cooldown period for scaling out
        scale_in_cooldown: Cooldown period for scaling in

    Returns:
        bool: Whether scaling action is allowed
    """
    # Get the last scaling times for both directions
    try:
        last_scale_up_time, up_count = get_last_scaling_time(aws_wrapper, 'up', s3_config_bucket, ecs_cluster,
                                                             service_name)
        last_scale_down_time, down_count = get_last_scaling_time(aws_wrapper, 'down', s3_config_bucket, ecs_cluster,
                                                                 service_name)

        # Define cooldowns for each scaling direction
        cooldown = scale_out_cooldown if action_type == 'up' else scale_in_cooldown

        # Calculate elapsed time since last action of requested type
        last_time = last_scale_up_time if action_type == 'up' else last_scale_down_time
        elapsed_time = time.time() - last_time
        time_remaining = max(0, cooldown - elapsed_time)

        # Format readable times for logging
        last_time_readable = datetime.fromtimestamp(last_time).strftime('%Y-%m-%d %H:%M:%S')
        current_time_readable = datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')

        # Default behavior - check if enough time has passed
        can_perform_scaling = elapsed_time > cooldown

        # ALWAYS allow scaling up regardless of cooldown period
        # This is the key change - if we need to scale up, we do it regardless of cooldown
        if action_type == 'up' and new_task_count > current_task_count:
            # Calculate task increase as a percentage
            increase_percentage = ((new_task_count - current_task_count) / current_task_count) * 100

            # Log the override with detailed information
            logging.info(f"PRIORITY OVERRIDE: Bypassing up scaling cooldown. "
                         f"Current: {current_task_count}, New: {new_task_count}, "
                         f"Increase: {new_task_count - current_task_count} tasks ({increase_percentage:.1f}%)")
            return True

        # For scale-down actions, respect the cooldown
        # Log the normal cooldown status
        if can_perform_scaling:
            logging.info(f"Cooldown period passed for {action_type} scaling. Last action: {last_time_readable}, "
                         f"Now: {current_time_readable}, Elapsed: {elapsed_time:.2f}s")
        else:
            logging.info(f"In cooldown period for {action_type} scaling. Last action: {last_time_readable}, "
                         f"Now: {current_time_readable}, Remaining: {time_remaining:.2f}s")

        return can_perform_scaling
    except Exception as e:
        logging.error(f"Error in can_scale function: {e}")
        # For scaling down, fail closed (don't scale if there's an error)
        if action_type == 'down':
            return False
        # For scaling up, fail open (allow scaling if there's an error)
        return True