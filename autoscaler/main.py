import os
import logging

from autoscaler.scaler import calculate_new_task_count, can_scale
from autoscaler.queue_metrics.sqs import get_queue_metrics
from autoscaler.state.s3_state import set_last_scaling_time
from autoscaler.aws.wrapper import AWSWrapper

# Environment variables
ECS_CLUSTER = os.environ.get('ECS_CLUSTER')
SERVICE_NAME = os.environ.get('SERVICE_NAME')
SQS_QUEUE_URL = os.environ.get('SQS_QUEUE_URL')
MIN_TASKS = int(os.environ.get('MIN_TASKS', '10'))
MAX_TASKS = int(os.environ.get('MAX_TASKS', '300'))
SCALE_UP_THRESHOLD = float(os.environ.get('SCALE_UP_THRESHOLD', '100.0'))
SCALE_DOWN_THRESHOLD = float(os.environ.get('SCALE_DOWN_THRESHOLD', '99.0'))
SCALE_OUT_COOLDOWN = int(os.environ.get('SCALE_OUT_COOLDOWN', '120'))
SCALE_IN_COOLDOWN = int(os.environ.get('SCALE_IN_COOLDOWN', '120'))
SCALING_STEP_COUNT = int(os.environ.get('SCALING_STEP_COUNT', '5'))
TASKS_PER_MESSAGE = float(os.environ.get('TASKS_PER_MESSAGE', '0.01'))  # Default: 1 task per 100 messages
DEFAULT_REGION = os.environ.get('AWS_REGION', 'us-east-1')
SSO_PROFILE = os.environ.get('SSO_PROFILE', None)
S3_CONFIG_BUCKET = os.environ.get('S3_CONFIG_BUCKET', 'tf-configuration-bucket-test')
MAX_SCALE_DOWN_FACTOR = float(os.environ.get('MAX_SCALE_DOWN_FACTOR', '0.99'))  # Configurable scale-down factor
# Configure whether to include in-flight messages in scaling decisions
USE_COMBINED_MESSAGES = os.environ.get('USE_COMBINED_MESSAGES', 'False').lower() in ('true', '1', 't', 'yes')
# We no longer need this environment variable since we're always bypassing for scale-up
# But we'll keep it for backward compatibility
COOLDOWN_OVERRIDE_THRESHOLD = int(os.environ.get('COOLDOWN_OVERRIDE_THRESHOLD', str(SCALING_STEP_COUNT)))


def update_service(aws_wrapper, new_task_count):
    """Update the ECS service with a new desired count."""
    try:
        ecs_client = aws_wrapper.create_aws_client('ecs')

        response = ecs_client.update_service(
            cluster=ECS_CLUSTER,
            service=SERVICE_NAME,
            desiredCount=new_task_count
        )

        logging.info(f"Updated service {SERVICE_NAME} to {new_task_count} tasks")
        return response
    except Exception as e:
        logging.error(f"Error updating service: {e}", exc_info=True)
        raise e


def lambda_handler(event, context):
    """Lambda handler function for auto-scaling ECS service based on SQS queue metrics."""
    logging.info(f"Starting auto-scaling check for service {SERVICE_NAME} in cluster {ECS_CLUSTER}")

    # Validate required environment variables
    if not SQS_QUEUE_URL:
        logging.error("SQS_QUEUE_URL environment variable is not set")
        return {"statusCode": 500, "error": "SQS_QUEUE_URL environment variable is not set"}

    if not ECS_CLUSTER or not SERVICE_NAME:
        logging.error("ECS_CLUSTER and SERVICE_NAME environment variables must be set")
        return {"statusCode": 500, "error": "ECS_CLUSTER and SERVICE_NAME environment variables must be set"}

    # Initialize AWS Wrapper
    aws_wrapper = AWSWrapper(sso_profile_name=SSO_PROFILE, region_name=DEFAULT_REGION)

    try:
        # Get current queue metrics
        queue_metrics = get_queue_metrics(aws_wrapper, SQS_QUEUE_URL)
        messages_visible = queue_metrics.get('visible', 0)
        messages_in_flight = queue_metrics.get('in_flight', 0)

        # Calculate total messages - combined for both calculations and zero check
        total_messages_combined = messages_visible + messages_in_flight

        # Use either visible messages only or combined based on configuration
        total_messages = total_messages_combined if USE_COMBINED_MESSAGES else messages_visible

        logging.info(f"Current queue metrics - visible: {messages_visible}, in_flight: {messages_in_flight}, " +
                     f"using {'combined' if USE_COMBINED_MESSAGES else 'visible only'}: {total_messages}")

        # Get current service details
        ecs_client = aws_wrapper.create_aws_client('ecs')
        service_response = ecs_client.describe_services(
            cluster=ECS_CLUSTER,
            services=[SERVICE_NAME]
        )

        if not service_response['services']:
            logging.error(f"Service {SERVICE_NAME} not found in cluster {ECS_CLUSTER}")
            return {"statusCode": 404, "error": f"Service {SERVICE_NAME} not found"}

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
            MIN_TASKS,
            MAX_TASKS,
            SCALE_UP_THRESHOLD,
            SCALE_DOWN_THRESHOLD,
            TASKS_PER_MESSAGE,
            MAX_SCALE_DOWN_FACTOR
        )

        # Apply bounds
        new_task_count = max(MIN_TASKS, min(MAX_TASKS, new_task_count))

        # Determine scaling direction
        scaling_direction = 'up' if new_task_count > current_task_count else 'down' if new_task_count < current_task_count else None

        # Check if we need to scale and if we can scale based on cooldown rules
        if scaling_direction and can_scale(
                aws_wrapper,
                scaling_direction,
                current_task_count,
                new_task_count,
                S3_CONFIG_BUCKET,
                ECS_CLUSTER,
                SERVICE_NAME,
                SCALE_OUT_COOLDOWN,
                SCALE_IN_COOLDOWN
        ):
            logging.info(f"Scaling {scaling_direction} from {current_task_count} to {new_task_count} tasks")
            update_service(aws_wrapper, new_task_count)
            set_last_scaling_time(aws_wrapper, scaling_direction, S3_CONFIG_BUCKET, ECS_CLUSTER, SERVICE_NAME)

            # Reset the consecutive scale-down counter when scaling up
            if scaling_direction == 'up':
                set_last_scaling_time(aws_wrapper, 'down', S3_CONFIG_BUCKET, ECS_CLUSTER, SERVICE_NAME, 0)
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