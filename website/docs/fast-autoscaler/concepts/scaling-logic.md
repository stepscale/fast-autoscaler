---
sidebar_position: 2
---

# Scaling Logic

The core scaling logic in Fast Autoscaler determines when and how to adjust the number of ECS tasks based on queue metrics and configuration parameters.

## Key Principles

Fast Autoscaler follows these key principles:

1. **Responsive Scale-Up**: Scale up quickly when queue depth increases
2. **Gradual Scale-Down**: Scale down more conservatively to avoid oscillation
3. **Cooldown Periods**: Respect cooldown periods to prevent rapid fluctuations
4. **Priority Override**: Bypass cooldown for critical scale-up operations
5. **Safety Bounds**: Always respect minimum and maximum task constraints

## Scaling Decision Flow

The scaling process follows this flow:

1. Collect current queue metrics (visible and optionally in-flight messages)
2. Calculate the ratio of messages per task
3. Determine if scaling is needed based on thresholds
4. If scaling up, calculate additional tasks needed
5. If scaling down, ensure we don't scale down too rapidly
6. Apply min/max task constraints
7. Check cooldown periods (always allowing scale-up operations)
8. Execute the scaling action if approved

## Scale-Up Logic

When queue depth exceeds the configured threshold:

```python
if total_messages > scale_up_threshold:
    # Calculate additional tasks needed based on total messages
    additional_tasks_needed = int(total_messages * tasks_per_message)
    
    # Ensure we add at least one task if needed
    if total_messages > 0 and additional_tasks_needed == 0:
        additional_tasks_needed = 1
    
    # Add the additional tasks to current count
    new_task_count = current_task_count + additional_tasks_needed
```

## Scale-Down Logic

When queue depth falls below the configured threshold:

```python
elif total_messages < scale_down_threshold:
    # Calculate based on message count
    target_tasks = max(min_tasks, int(total_messages * tasks_per_message))
    
    # Don't scale down by more than the configurable factor at once
    min_tasks_after_scaling = int(current_task_count * max_scale_down_factor)
    final_task_count = max(target_tasks, min_tasks_after_scaling)
```

## Cooldown Management

The autoscaler maintains separate cooldown periods for scaling up and scaling down. However, scale-up operations can bypass cooldown when queue depth increases significantly:

```python
if action_type == 'up' and new_task_count > current_task_count:
    # Calculate task increase as a percentage
    increase_percentage = ((new_task_count - current_task_count) / current_task_count) * 100
    
    # Log the override with detailed information
    logging.info(f"PRIORITY OVERRIDE: Bypassing up scaling cooldown...")
    return True
```

This ensures rapid response to growing queue depths even when in a cooldown period.