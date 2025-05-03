---
sidebar_position: 3
---

# State Management

Fast Autoscaler uses a state management system to track scaling events and enforce cooldown periods between scaling actions.

## Purpose

State management serves several important functions:

1. **Cooldown Enforcement**: Prevent oscillation by limiting how often scaling can occur
2. **History Tracking**: Maintain a record of scaling events for analysis
3. **Continuity**: Maintain state across Lambda function invocations
4. **Distributed Operation**: Support multiple instances or regions if needed

## Implementation

The default implementation uses S3 as a persistent storage mechanism:

1. Each scaling action (up/down) is recorded in a separate S3 object
2. The state includes timestamp, action type, and counter
3. State is namespaced by cluster and service name
4. The S3 implementation includes error handling and fallbacks

## File Structure

State files are stored in S3 with a path structure of:

```
s3://<bucket>/autoscaling-state/<cluster-name>/<service-name>/<action-type>-last-action.json
```

Where:
- `<bucket>` is the configured S3 bucket
- `<cluster-name>` is the ECS cluster name
- `<service-name>` is the ECS service name
- `<action-type>` is either "up" or "down"

## State Data Format

The state data is stored as a JSON object:

```json
{
  "timestamp": 1682341234.567,
  "cluster": "production-cluster",
  "service": "worker-service",
  "action_type": "up",
  "count": 5
}
```

## Error Handling

The state management system is designed to be resilient:

1. Read errors result in conservative defaults (allow scale-up, prevent scale-down)
2. Write errors are logged but don't halt operation
3. JSON parsing issues are handled gracefully
4. Legacy timestamp formats are supported for backwards compatibility

## Extending State Management

The state management system can be extended with alternative storage backends by implementing the same interface provided by the S3 state module.