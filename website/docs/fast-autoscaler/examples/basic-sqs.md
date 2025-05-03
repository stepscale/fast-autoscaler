---
sidebar_position: 1
---

# Basic SQS Example

This example demonstrates how to deploy the Fast Autoscaler for a basic ECS service that processes messages from an SQS queue.

## CloudFormation Template

You can use the following CloudFormation template to deploy a complete setup including:
- The autoscaler Lambda function
- IAM permissions
- CloudWatch Event trigger

```yaml
# Example snippet from the full template
AWSTemplateFormatVersion: '2010-09-09'
Description: 'Fast Autoscaler for ECS with SQS Queue'

Parameters:
  ECSClusterName:
    Type: String
    Description: Name of the ECS cluster
    
  ECSServiceName:
    Type: String
    Description: Name of the ECS service to autoscale
    
  SQSQueueURL:
    Type: String
    Description: URL of the SQS queue to monitor
```

The full template is available in the [examples/ecs-sqs-basic.yaml](https://github.com/stepscale/fast-autoscaler/blob/main/examples/ecs-sqs-basic.yaml) file in the repository.

## Manual Deployment

If you prefer to deploy manually, follow these steps:

1. Create an IAM role with the required permissions
2. Deploy the Lambda function using the AWS CLI or console
3. Set up the CloudWatch Event trigger

See the [Getting Started](../getting-started) guide for detailed instructions.

## Verification

After deployment, you can verify the autoscaler is working by:

1. Check CloudWatch Logs for the Lambda function
2. Monitor the ECS service's desired count
3. Add messages to the SQS queue and observe scaling behavior