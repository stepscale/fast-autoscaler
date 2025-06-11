import os
import logging
import json
from typing import Dict, Any, Optional

from autoscaler.scaler import calculate_new_task_count, can_scale
from autoscaler.state.s3_state import set_last_scaling_time
from autoscaler.aws.wrapper import AWSWrapper

# Queue metric providers
from autoscaler.queue_metrics import sqs, amq, kinesis, kafka, rabbitmq, redis

# Common configuration loader
from autoscaler.config import load_config, Config


def update_service(aws_wrapper: AWSWrapper, cluster: str, service_name: str, new_task_count: int) -> Dict[str, Any]:
    """
    Update the ECS service with a new desired count.
    
    Args:
        aws_wrapper: AWS API wrapper instance
        cluster: ECS cluster name
        service_name: ECS service name
        new_task_count: New desired task count
        
    Returns:
        dict: ECS update_service response
        
    Raises:
        Exception: If service update fails
    """
    try:
        ecs_client = aws_wrapper.create_aws_client('ecs')

        response = ecs_client.update_service(
            cluster=cluster,
            service=service_name,
            desiredCount=new_task_count
        )

        logging.info(f"Updated service {service_name} to {new_task_count} tasks")
        return response
    except Exception as e:
        logging.error(f"Error updating service: {e}", exc_info=True)
        raise


def get_queue_metrics(aws_wrapper: AWSWrapper, config: Config) -> Dict[str, int]:
    """
    Get queue metrics from the configured queue provider.
    
    Args:
        aws_wrapper: AWS API wrapper instance
        config: Configuration object
        
    Returns:
        dict: Queue metrics with 'visible' and 'in_flight' counts
        
    Raises:
        ValueError: If queue type is not supported
    """
    queue_type = config.queue_type.lower()
    
    # Map queue types to their respective modules
    queue_providers = {
        'sqs': sqs,
        'amq': amq,
        'kinesis': kinesis,
        'kafka': kafka,
        'rabbitmq': rabbitmq,
        'redis': redis
    }
    
    if queue_type not in queue_providers:
        supported = ', '.join(queue_providers.keys())
        raise ValueError(f"Unsupported queue type: {queue_type}. Supported types: {supported}")
    
    provider = queue_providers[queue_type]
    
    # Each provider implements the same get_queue_metrics interface
    queue_metrics = provider.get_queue_metrics(aws_wrapper, config.queue_config)
    
    logging.info(f"Retrieved {queue_type} metrics: {queue_metrics}")
    return queue_metrics


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler function for auto-scaling ECS service based on queue metrics.
    
    Supports multiple queue types (SQS, AMQ, Kinesis, Kafka, RabbitMQ, Redis).
    Configuration can be provided via environment variables or in the event payload.
    
    Args:
        event: AWS Lambda event object, can contain configuration overrides
        context: AWS Lambda context object
        
    Returns:
        dict: Scaling result with queue size, current and new task counts
    """
    # Load configuration from environment variables and event payload
    config = load_config(event)
    
    logging.info(f"Starting auto-scaling check for service {config.service_name} in cluster {config.cluster_name}")

    # Validate required configuration
    if not config.queue_config:
        logging.error("Queue configuration is missing")
        return {"statusCode": 500, "error": "Queue configuration is missing"}

    if not config.cluster_name or not config.service_name:
        logging.error("ECS_CLUSTER and SERVICE_NAME must be configured")
        return {"statusCode": 500, "error": "ECS_CLUSTER and SERVICE_NAME must be configured"}

    # Initialize AWS Wrapper
    aws_wrapper = AWSWrapper(
        sso_profile_name=config.sso_profile, 
        region_name=config.region
    )

    try:
        # Get current queue metrics
        queue_metrics = get_queue_metrics(aws_wrapper, config)
        messages_visible = queue_metrics.get('visible', 0)
        messages_in_flight = queue_metrics.get('in_flight', 0)

        # Calculate total messages - combined for both calculations and zero check
        total_messages_combined = messages_visible + messages_in_flight

        # Use either visible messages only or combined based on configuration
        total_messages = total_messages_combined if config.use_combined_messages else messages_visible

        logging.info(f"Current queue metrics - visible: {messages_visible}, in_flight: {messages_in_flight}, " +
                     f"using {'combined' if config.use_combined_messages else 'visible only'}: {total_messages}")

        # Get current service details
        ecs_client = aws_wrapper.create_aws_client('ecs')
        service_response = ecs_client.describe_services(
            cluster=config.cluster_name,
            services=[config.service_name]
        )

        if not service_response['services']:
            logging.error(f"Service {config.service_name} not found in cluster {config.cluster_name}")
            return {"statusCode": 404, "error": f"Service {config.service_name} not found"}

        service = service_response['services'][0]
        current_task_count = service.get('desiredCount', 0)
        running_task_count = service.get('runningCount', 0)

        logging.info(f"Current ECS state - desired: {current_task_count}, running: {running_task_count}")

        # Calculate messages per task ratio
        messages_per_task = total_messages / max(current_task_count, 1)
        logging.info(f"Current messages per task: {messages_per_task}")

        # Determine if scaling is needed
        new_task_count = calculate_new_task_count(
            current_task_count,
            total_messages,
            messages_per_task,
            total_messages_combined,
            config.min_tasks,
            config.max_tasks,
            config.scale_up_threshold,
            config.scale_down_threshold,
            config.tasks_per_message,
            config.max_scale_down_factor
        )

        # Apply bounds
        new_task_count = max(config.min_tasks, min(config.max_tasks, new_task_count))

        # Determine scaling direction
        scaling_direction = None
        if new_task_count > current_task_count:
            scaling_direction = 'up'
        elif new_task_count < current_task_count:
            scaling_direction = 'down'

        # Check if we need to scale and if we can scale based on cooldown rules
        if scaling_direction and can_scale(
                aws_wrapper,
                scaling_direction,
                current_task_count,
                new_task_count,
                config.s3_config_bucket,
                config.cluster_name,
                config.service_name,
                config.scale_out_cooldown,
                config.scale_in_cooldown
        ):
            logging.info(f"Scaling {scaling_direction} from {current_task_count} to {new_task_count} tasks")
            update_service(aws_wrapper, config.cluster_name, config.service_name, new_task_count)
            set_last_scaling_time(aws_wrapper, scaling_direction, 
                                 config.s3_config_bucket, config.cluster_name, config.service_name)

            # Reset the consecutive scale-down counter when scaling up
            if scaling_direction == 'up':
                set_last_scaling_time(aws_wrapper, 'down', 
                                     config.s3_config_bucket, config.cluster_name, config.service_name, 0)
        elif scaling_direction:
            logging.info(
                f"Scaling action needed (from {current_task_count} to {new_task_count}) but in cooldown period")
        else:
            logging.info(f"No scaling action needed, maintaining {current_task_count} tasks")

        return {
            'queue_size': total_messages,
            'current_tasks': current_task_count,
            'new_tasks': new_task_count,
            'messages_per_task': messages_per_task
        }

    except Exception as e:
        logging.error(f"Error in auto-scaling lambda: {e}", exc_info=True)
        return {"statusCode": 500, "error": str(e)}