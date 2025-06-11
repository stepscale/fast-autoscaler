# Changelog

All notable changes to this project will be documented in this file.

## [0.2.0] - 2024-06-11
### Added
- Support for additional queue types: Kafka (MSK), Kinesis, RabbitMQ, Redis, and SNS.
- Expanded configuration options for each queue type.
- Improved modularity and extensibility for adding new queue providers.
- Updated documentation and examples for new queue types.
- Added a "What's New" section to the README.
- Added company website and documentation link to the README.

### Changed
- Refactored core logic for better maintainability and extensibility.
- Improved error handling and logging across modules.

### Fixed
- Minor bug fixes and code clean-up.

---

## [0.1.0] - 2024-05-03
### Added
- Initial release.
- Core autoscaling logic for AWS ECS services based on queue metrics.
- Support for Amazon SQS and Amazon MQ (ActiveMQ) as queue providers.
- S3-based state management for cooldown tracking.
- Configurable scaling thresholds, cooldowns, and task limits.
- Lambda deployment instructions and example CloudFormation templates.
- Basic test coverage for scaling logic.
- Documentation for setup, configuration, and deployment.

--- 