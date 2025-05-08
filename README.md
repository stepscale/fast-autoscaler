# Fast Autoscaler

A modular, extensible autoscaling solution for AWS ECS services based on queue metrics.

## Features

- Dynamic scaling of ECS services based on multiple queue metrics sources
- Configurable scaling thresholds and cooldown periods
- Priority override for scale-up operations
- Support for scaling based on visible and/or in-flight messages
- Extensible architecture with support for different queue providers:
  - Amazon SQS
  - Amazon MQ (ActiveMQ)
  - Amazon Kinesis Data Streams
  - Amazon MSK (Kafka)
  - RabbitMQ
  - Redis-based queues
- S3-based state management for cooldown tracking
- Detailed logging with JSON formatting for CloudWatch integration
- Configuration via environment variables or event payload

## Inspiration

This project was inspired by Zac Charles' article [Another Way to Trigger a Lambda Function Every 5–10 Seconds](https://zaccharles.medium.com/another-way-to-trigger-a-lambda-function-every-5-10-seconds-41cb5bc3fa80), which describes creative approaches for high-frequency serverless processing. While our implementation focuses on autoscaling rather than high-frequency triggering, the article's insights about AWS service integration and precision timing were valuable in designing our solution.

## Architecture

The autoscaler follows a modular architecture to support different message queue providers and deployment models:

- **Core Scaling Logic**: Centralized scaling decision logic in `scaler.py`
- **Queue Metrics**: Abstracted queue metric collection with provider-specific implementations
- **State Management**: S3-based state tracking for scaling events and cooldowns
- **AWS Integration**: Lightweight wrapper around AWS services
- **Configuration**: Flexible configuration from environment variables or event payload

## Usage

### Basic Configuration

Configure the autoscaler using these environment variables or by providing them in the Lambda event payload:

| Variable | Description | Default |
|----------|-------------|---------|
| `QUEUE_TYPE` | Type of queue (sqs, amq, kinesis, kafka, rabbitmq, redis) | sqs |
| `ECS_CLUSTER` | ECS cluster name | (required) |
| `SERVICE_NAME` | ECS service name | (required) |
| `MIN_TASKS` | Minimum number of tasks | 10 |
| `MAX_TASKS` | Maximum number of tasks | 300 |
| `SCALE_UP_THRESHOLD` | Queue size threshold for scaling up | 100.0 |
| `SCALE_DOWN_THRESHOLD` | Queue size threshold for scaling down | 99.0 |
| `SCALE_OUT_COOLDOWN` | Cooldown period for scaling out (seconds) | 120 |
| `SCALE_IN_COOLDOWN` | Cooldown period for scaling in (seconds) | 120 |
| `SCALING_STEP_COUNT` | Step count for scaling operations | 5 |
| `TASKS_PER_MESSAGE` | Task-to-message ratio for scaling calculations | 0.01 |
| `MAX_SCALE_DOWN_FACTOR` | Maximum scale down percentage | 0.99 |
| `USE_COMBINED_MESSAGES` | Include in-flight messages in scaling decisions | False |
| `S3_CONFIG_BUCKET` | S3 bucket for state storage | tf-configuration-bucket-test |
| `LOG_LEVEL` | Logging level | INFO |

### Queue-Specific Configuration

#### SQS
```
QUEUE_TYPE=sqs
SQS_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/123456789012/my-queue
```

#### Amazon MQ (ActiveMQ)
```
QUEUE_TYPE=amq
AMQ_BROKER_ID=b-1234a5b6-78cd-901e-2fgh-3i45j6k178l9
AMQ_QUEUE_NAME=my-queue
AMQ_USERNAME=admin
AMQ_PASSWORD=password
```

#### Kinesis Data Streams
```
QUEUE_TYPE=kinesis
KINESIS_STREAM_NAME=my-stream
```

#### Amazon MSK (Kafka)
```
QUEUE_TYPE=kafka
MSK_CLUSTER_ARN=arn:aws:kafka:us-east-1:123456789012:cluster/my-cluster/abcdefgh-1234-5678-9ijklmno
KAFKA_TOPIC=my-topic
KAFKA_BOOTSTRAP_SERVERS=b-1.my-cluster.abcdef.c1.kafka.us-east-1.amazonaws.com:9092,b-2.my-cluster.abcdef.c1.kafka.us-east-1.amazonaws.com:9092
KAFKA_CONSUMER_GROUP=autoscaler-monitor
```

#### RabbitMQ
```
QUEUE_TYPE=rabbitmq
RABBITMQ_HOST=rabbitmq.example.com
RABBITMQ_PORT=5672
RABBITMQ_VHOST=/
RABBITMQ_QUEUE=my-queue
RABBITMQ_USERNAME=guest
RABBITMQ_PASSWORD=guest
```

#### Redis
```
QUEUE_TYPE=redis
REDIS_HOST=redis.example.com
REDIS_PORT=6379
REDIS_PASSWORD=password
REDIS_QUEUE_KEY=my-queue
REDIS_QUEUE_TYPE=list  # or 'stream'
```

### Event Payload Configuration

You can also configure the autoscaler by passing a configuration object in the Lambda event:

```json
{
  "config": {
    "queue_type": "sqs",
    "queue_config": {
      "queue_url": "https://sqs.us-east-1.amazonaws.com/123456789012/my-queue"
    },
    "cluster_name": "my-cluster",
    "service_name": "my-service",
    "min_tasks": 10,
    "max_tasks": 300,
    "scale_up_threshold": 100.0,
    "scale_down_threshold": 99.0,
    "tasks_per_message": 0.01
  }
}
```

## Deployment

### AWS Lambda

To deploy as an AWS Lambda function:

1. Build the package:
   ```
   pip install -r requirements.txt -t package/
   cp -r autoscaler package/
   cp lambda_function.py package/
   cd package && zip -r ../lambda_deployment.zip .
   ```

2. Deploy to AWS Lambda using the AWS CLI:
   ```
   aws lambda create-function \
     --function-name ecs-fast-autoscaler \
     --runtime python3.9 \
     --handler lambda_function.handler \
     --role arn:aws:iam::<account-id>:role/your-lambda-role \
     --zip-file fileb://lambda_deployment.zip \
     --timeout 60 \
     --environment "Variables={QUEUE_TYPE=sqs,ECS_CLUSTER=your-cluster,SERVICE_NAME=your-service,SQS_QUEUE_URL=your-queue-url}"
   ```

### CloudWatch Event Rule

Set up a CloudWatch Event Rule to trigger the Lambda function periodically:

```
aws events put-rule \
  --name ecs-autoscaling-trigger \
  --schedule-expression "rate(1 minute)"

aws events put-targets \
  --rule ecs-autoscaling-trigger \
  --targets "Id"="1","Arn"="arn:aws:lambda:<region>:<account-id>:function:ecs-fast-autoscaler"
```

## IAM Permissions

The Lambda function requires these permissions:

- **Queue Access**:
  - `sqs:GetQueueAttributes` - For SQS queues
  - `kafka:DescribeCluster`, `kafka:GetBootstrapBrokers` - For MSK
  - `kinesis:DescribeStream`, `kinesis:GetRecords` - For Kinesis
  - `mq:DescribeBroker` - For Amazon MQ
- **ECS Access**:
  - `ecs:DescribeServices` - To get current service state
  - `ecs:UpdateService` - To update service desired count
- **State Management**:
  - `s3:GetObject` and `s3:PutObject` - For state management in S3
- **Monitoring (Optional)**:
  - `cloudwatch:GetMetricStatistics` - For fallback metrics gathering

## Future Extensions

- Support for more queue providers and metrics sources
- Container-based deployment option
- Multi-service orchestration
- Predictive scaling based on historical patterns
- Custom scaling algorithms

## License

Apache License 2.0