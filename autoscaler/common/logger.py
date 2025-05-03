import os
import logging
import json


def setup_logging(level=None):
    """
    Set up logging with JSON formatting for better integration with CloudWatch.

    Args:
        level: Optional log level override (default: uses LOG_LEVEL env var or INFO)
    """
    # Get log level from environment or use default
    if level is None:
        level = os.environ.get('LOG_LEVEL', 'INFO').upper()

    # Convert string level to logging constant
    numeric_level = getattr(logging, level, logging.INFO)

    # Configure root logger
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s [%(levelname)s] %(name)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Add JSON formatter for production environments
    if os.environ.get('AWS_EXECUTION_ENV') is not None:
        # Running in Lambda or other AWS service
        root_logger = logging.getLogger()
        for handler in root_logger.handlers:
            handler.setFormatter(JsonFormatter())

    # Silence noisy loggers
    logging.getLogger('boto3').setLevel(logging.WARNING)
    logging.getLogger('botocore').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)

    logging.debug("Logging initialized")


class JsonFormatter(logging.Formatter):
    """
    Format logs as JSON for better integration with CloudWatch Logs Insights.
    """

    def format(self, record):
        log_record = {
            'timestamp': self.formatTime(record, self.datefmt),
            'level': record.levelname,
            'name': record.name,
            'message': record.getMessage(),
            'file': record.pathname,
            'line': record.lineno,
            'function': record.funcName
        }

        # Add exception info if present
        if record.exc_info:
            log_record['exception'] = self.formatException(record.exc_info)

        # Add extra fields from record
        for key, value in record.__dict__.items():
            if key not in {
                'args', 'asctime', 'created', 'exc_info', 'exc_text', 'filename',
                'funcName', 'id', 'levelname', 'levelno', 'lineno', 'module',
                'msecs', 'message', 'msg', 'name', 'pathname', 'process',
                'processName', 'relativeCreated', 'stack_info', 'thread', 'threadName'
            }:
                log_record[key] = value

        return json.dumps(log_record)