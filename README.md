# Fast Autoscaler

A modular, extensible autoscaling solution for AWS ECS services based on queue metrics.

## Features

- Dynamic scaling of ECS services based on SQS queue metrics
- Configurable scaling thresholds and cooldown periods
- Priority override for scale-up operations
- Support for scaling based on visible and/or in-flight messages
- Extensible architecture with support for different queue providers (SQS, AMQ, etc.)
- S3-based state management for cooldown tracking
- Detailed logging with JSON formatting for CloudWatch integration

## Inspiration

This project was inspired by Zac Charles' article [Another Way to Trigger a Lambda Function Every 5–10 Seconds](https://zaccharles.medium.com/another-way-to-trigger-a-lambda-function-every-5-10-seconds-41cb5bc3fa80), which describes creative approaches for high-frequency serverless processing. While our implementation focuses on autoscaling rather than high-frequency triggering, the article's insights about AWS service integration and precision timing were valuable in designing our solution.

## Architecture

The autoscaler follows a modular architecture to support different message queue providers and deployment models:

- **Core Scaling Logic**: Centralized scaling decision logic in `scaler.py`
- **Queue Metrics**: Abstracted queue metric collection with provider-specific implementations
- **State Management**: S3-based state tracking for scaling events and cooldowns
- **AWS Integration**: Lightweight wrapper around AWS services

## Usage

### Environment Variables

Configure the autoscaler using these environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `ECS_CLUSTER` | ECS cluster name | (required) |
| `SERVICE_NAME` | ECS service name | (required) |
| `SQS_QUEUE_URL` | URL of the SQS queue to monitor | (required) |
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
     --environment "Variables={ECS_CLUSTER=your-cluster,SERVICE_NAME=your-service,SQS_QUEUE_URL=your-queue-url}"
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

- `sqs:GetQueueAttributes` - To read queue metrics
- `ecs:DescribeServices` - To get current service state
- `ecs:UpdateService` - To update service desired count
- `s3:GetObject` and `s3:PutObject` - For state management

## Future Extensions

- Support for Amazon MQ (ActiveMQ/RabbitMQ)
- Custom metric sources beyond queues
- Container-based deployment option
- Multi-service orchestration
- Predictive scaling based on historical patterns

## License

Apache License 2.0