---
sidebar_position: 1
---

# Fast Autoscaler

A modular, extensible autoscaling solution for AWS ECS services based on queue metrics.

## Overview

Fast Autoscaler is a production-ready solution that dynamically adjusts ECS task counts based on SQS queue depths and other metrics. Our approach enables precise resource scaling to optimize both performance and cost.

## Key Features

- **Intelligent Queue-based Scaling**: Dynamically adjusts ECS service capacity based on SQS queue metrics
- **Priority Scale-up**: Override cooldown periods when rapid scaling is needed
- **Configurable Thresholds**: Customizable scaling thresholds and cooldown periods
- **Comprehensive Metrics**: Support for both visible and in-flight message-based scaling
- **Provider-agnostic Architecture**: Extensible design supporting different queue providers (SQS, AMQ, etc.)
- **State Management**: S3-based tracking for cooldown periods and scaling history
- **Production-ready Observability**: Detailed logging with JSON formatting for CloudWatch integration

## Architecture

The autoscaler follows a modular architecture to support different message queue providers and deployment models:

- **Core Scaling Logic**: Centralized scaling decision logic in `scaler.py`
- **Queue Metrics**: Abstracted queue metric collection with provider-specific implementations
- **State Management**: S3-based state tracking for scaling events and cooldowns
- **AWS Integration**: Lightweight wrapper around AWS services