---
sidebar_position: 3
---

# Configuration

The Fast Autoscaler can be configured using environment variables to customize its behavior.

## Environment Variables

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

## Configuration Examples

### Basic Configuration

```bash
# Required variables
ECS_CLUSTER=production-cluster
SERVICE_NAME=worker-service
SQS_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/123456789012/worker-queue

# Optional tuning
MIN_TASKS=5
MAX_TASKS=100
SCALE_UP_THRESHOLD=50
SCALE_DOWN_THRESHOLD=10
```

### Advanced Configuration

```bash
# Required variables
ECS_CLUSTER=production-cluster
SERVICE_NAME=worker-service
SQS_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/123456789012/worker-queue

# Task constraints
MIN_TASKS=5
MAX_TASKS=100

# Scaling behavior
SCALE_UP_THRESHOLD=50
SCALE_DOWN_THRESHOLD=10
TASKS_PER_MESSAGE=0.025
MAX_SCALE_DOWN_FACTOR=0.8

# Cooldown periods
SCALE_OUT_COOLDOWN=60
SCALE_IN_COOLDOWN=300

# Use combined (visible + in-flight) messages for scaling decisions
USE_COMBINED_MESSAGES=True
```