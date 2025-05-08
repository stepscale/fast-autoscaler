import os
from typing import Dict, Any, Optional, NamedTuple


class Config(NamedTuple):
    """Configuration for the autoscaler."""
    # ECS configuration
    cluster_name: str
    service_name: str
    min_tasks: int
    max_tasks: int
    
    # Queue configuration
    queue_type: str
    queue_config: Dict[str, Any]
    use_combined_messages: bool
    
    # Scaling parameters
    scale_up_threshold: float
    scale_down_threshold: float
    tasks_per_message: float
    max_scale_down_factor: float
    
    # Cooldown configuration
    scale_out_cooldown: int
    scale_in_cooldown: int
    scaling_step_count: int
    
    # AWS configuration
    region: str
    sso_profile: Optional[str]
    s3_config_bucket: str


def load_config(event: Dict[str, Any] = None) -> Config:
    """
    Load configuration from environment variables and optional event payload.
    
    Event payload values override environment variables when present.
    
    Args:
        event: Optional Lambda event that may contain configuration overrides
        
    Returns:
        Config: Configuration object with all autoscaler settings
    """
    event = event or {}
    config_from_event = event.get('config', {})
    
    # ECS configuration
    cluster_name = config_from_event.get('cluster_name') or os.environ.get('ECS_CLUSTER')
    service_name = config_from_event.get('service_name') or os.environ.get('SERVICE_NAME')
    min_tasks = int(config_from_event.get('min_tasks') or os.environ.get('MIN_TASKS', '10'))
    max_tasks = int(config_from_event.get('max_tasks') or os.environ.get('MAX_TASKS', '300'))
    
    # Queue configuration
    queue_type = config_from_event.get('queue_type') or os.environ.get('QUEUE_TYPE', 'sqs')
    
    # Queue-specific configuration
    queue_config = config_from_event.get('queue_config', {})
    if not queue_config:
        # If not in event, try to load from environment depending on queue type
        if queue_type.lower() == 'sqs':
            queue_config = {'queue_url': os.environ.get('SQS_QUEUE_URL')}
        elif queue_type.lower() == 'kinesis':
            queue_config = {'stream_name': os.environ.get('KINESIS_STREAM_NAME')}
        elif queue_type.lower() == 'amq':
            queue_config = {
                'broker_id': os.environ.get('AMQ_BROKER_ID'),
                'queue_name': os.environ.get('AMQ_QUEUE_NAME'),
                'username': os.environ.get('AMQ_USERNAME'),
                'password': os.environ.get('AMQ_PASSWORD')
            }
        elif queue_type.lower() == 'kafka':
            queue_config = {
                'cluster_arn': os.environ.get('MSK_CLUSTER_ARN'),
                'topic': os.environ.get('KAFKA_TOPIC'),
                'bootstrap_servers': os.environ.get('KAFKA_BOOTSTRAP_SERVERS'),
                'consumer_group': os.environ.get('KAFKA_CONSUMER_GROUP', 'autoscaler-monitor')
            }
        elif queue_type.lower() == 'rabbitmq':
            queue_config = {
                'host': os.environ.get('RABBITMQ_HOST'),
                'port': os.environ.get('RABBITMQ_PORT'),
                'vhost': os.environ.get('RABBITMQ_VHOST', '/'),
                'queue': os.environ.get('RABBITMQ_QUEUE'),
                'username': os.environ.get('RABBITMQ_USERNAME'),
                'password': os.environ.get('RABBITMQ_PASSWORD')
            }
        elif queue_type.lower() == 'redis':
            queue_config = {
                'host': os.environ.get('REDIS_HOST'),
                'port': os.environ.get('REDIS_PORT'),
                'password': os.environ.get('REDIS_PASSWORD'),
                'queue_key': os.environ.get('REDIS_QUEUE_KEY'),
                'queue_type': os.environ.get('REDIS_QUEUE_TYPE', 'list')
            }
    
    # Clean None values from queue_config
    queue_config = {k: v for k, v in queue_config.items() if v is not None}
    
    # Whether to include in-flight messages in scaling decisions
    use_combined_messages_str = config_from_event.get('use_combined_messages') or os.environ.get('USE_COMBINED_MESSAGES', 'False')
    use_combined_messages = use_combined_messages_str.lower() in ('true', '1', 't', 'yes')
    
    # Scaling parameters
    scale_up_threshold = float(config_from_event.get('scale_up_threshold') or 
                             os.environ.get('SCALE_UP_THRESHOLD', '100.0'))
    scale_down_threshold = float(config_from_event.get('scale_down_threshold') or 
                               os.environ.get('SCALE_DOWN_THRESHOLD', '99.0'))
    tasks_per_message = float(config_from_event.get('tasks_per_message') or 
                            os.environ.get('TASKS_PER_MESSAGE', '0.01'))
    max_scale_down_factor = float(config_from_event.get('max_scale_down_factor') or 
                                os.environ.get('MAX_SCALE_DOWN_FACTOR', '0.99'))
    
    # Cooldown configuration
    scale_out_cooldown = int(config_from_event.get('scale_out_cooldown') or 
                           os.environ.get('SCALE_OUT_COOLDOWN', '120'))
    scale_in_cooldown = int(config_from_event.get('scale_in_cooldown') or 
                          os.environ.get('SCALE_IN_COOLDOWN', '120'))
    scaling_step_count = int(config_from_event.get('scaling_step_count') or 
                           os.environ.get('SCALING_STEP_COUNT', '5'))
    
    # AWS configuration
    region = config_from_event.get('region') or os.environ.get('AWS_REGION', 'us-east-1')
    sso_profile = config_from_event.get('sso_profile') or os.environ.get('SSO_PROFILE')
    s3_config_bucket = config_from_event.get('s3_config_bucket') or os.environ.get('S3_CONFIG_BUCKET', 
                                                                                'tf-configuration-bucket-test')
    
    return Config(
        cluster_name=cluster_name,
        service_name=service_name,
        min_tasks=min_tasks,
        max_tasks=max_tasks,
        queue_type=queue_type,
        queue_config=queue_config,
        use_combined_messages=use_combined_messages,
        scale_up_threshold=scale_up_threshold,
        scale_down_threshold=scale_down_threshold,
        tasks_per_message=tasks_per_message,
        max_scale_down_factor=max_scale_down_factor,
        scale_out_cooldown=scale_out_cooldown,
        scale_in_cooldown=scale_in_cooldown,
        scaling_step_count=scaling_step_count,
        region=region,
        sso_profile=sso_profile,
        s3_config_bucket=s3_config_bucket
    )