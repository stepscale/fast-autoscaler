---
sidebar_position: 2
---

# Getting Started

This guide will help you get started with Fast Autoscaler.

## Prerequisites

Before deploying the Fast Autoscaler, ensure you have:

1. An AWS account with appropriate permissions
2. An ECS cluster with at least one service to scale
3. An SQS queue that the service processes
4. An S3 bucket for state storage

Required IAM permissions:
- `sqs:GetQueueAttributes` - To read queue metrics
- `ecs:DescribeServices` - To get current service state
- `ecs:UpdateService` - To update service desired count
- `s3:GetObject` and `s3:PutObject` - For state management

## Quick Start

### Lambda Deployment (Recommended)

1. Clone the repository:
   ```bash
   git clone https://github.com/stepscale/fast-autoscaler.git
   cd fast-autoscaler
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt -t package/
   cp -r autoscaler package/
   cp lambda_function.py package/
   cd package && zip -r ../lambda_deployment.zip .
   ```

3. Create a Lambda function using the AWS CLI:
   ```bash
   aws lambda create-function \
     --function-name ecs-fast-autoscaler \
     --runtime python3.9 \
     --handler lambda_function.handler \
     --role arn:aws:iam::<account-id>:role/your-lambda-role \
     --zip-file fileb://lambda_deployment.zip \
     --timeout 60 \
     --environment "Variables={ECS_CLUSTER=your-cluster,SERVICE_NAME=your-service,SQS_QUEUE_URL=your-queue-url}"
   ```

4. Set up a CloudWatch Event Rule to trigger the Lambda function:
   ```bash
   aws events put-rule \
     --name ecs-autoscaling-trigger \
     --schedule-expression "rate(1 minute)"

   aws events put-targets \
     --rule ecs-autoscaling-trigger \
     --targets "Id"="1","Arn"="arn:aws:lambda:<region>:<account-id>:function:ecs-fast-autoscaler"
   ```

## Next Steps

- [Learn about configuration options](./configuration)
- [Explore example deployments](./examples/basic-sqs)