---
sidebar_position: 2
---

# High Frequency Scaling Example

This example demonstrates an advanced deployment of Fast Autoscaler using AWS Step Functions to achieve high-frequency scaling checks (every 5-10 seconds instead of once per minute).

## Why High Frequency?

For workloads with rapid queue growth or stringent processing time requirements, the standard 1-minute CloudWatch Events trigger may not provide sufficient responsiveness. This approach, inspired by Zac Charles' article on [triggering Lambda functions at sub-minute intervals](https://zaccharles.medium.com/another-way-to-trigger-a-lambda-function-every-5-10-seconds-41cb5bc3fa80), provides more frequent scaling decisions.

## Architecture

This approach uses:

1. A Step Function state machine triggered every minute
2. Within the state machine, a Map state with controlled concurrency
3. Wait states that trigger the autoscaler Lambda at 10-second intervals

## CloudFormation Template

You can use the CloudFormation template in [examples/high_frequency_step_function.yaml](https://github.com/stepscale/fast-autoscaler/blob/main/examples/high_frequency_step_function.yaml) to deploy this solution.

Key components:

```yaml
# Sample snippet - see full template in repository
AutoscalerStateMachine:
  Type: AWS::StepFunctions::StateMachine
  Properties:
    StateMachineType: EXPRESS
    RoleArn: !GetAtt StepFunctionRole.Arn
    DefinitionString: !Sub |
      {
        "Comment": "High-frequency autoscaler using Step Functions",
        "StartAt": "Initialize",
        "States": {
          "Initialize": {
            "Type": "Pass",
            "Result": {
              "index": 0,
              "checks": ${ChecksPerExecution},
              "timestamps": []
            },
            "Next": "CheckLoop"
          },
          # Additional states defined here
```

## Performance and Cost Considerations

This approach provides better responsiveness but comes with trade-offs:

- **Cost**: Slightly higher due to Step Functions Express Workflow execution costs
- **Accuracy**: Sub-minute scaling decisions with ~500ms precision
- **Complexity**: More components to monitor and maintain

For most use cases, the standard deployment is sufficient. Consider this approach only for workloads with specific high-frequency scaling requirements.