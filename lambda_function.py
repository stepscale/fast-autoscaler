"""
Lambda function entry point for AWS Lambda deployments.
"""

# Configure logging first
from autoscaler.common.logger import setup_logging

setup_logging()

# Import handler from main module
from autoscaler.main import lambda_handler


# This is the entry point for AWS Lambda
# The handler is specified in the Lambda configuration as "lambda_function.handler"
def handler(event, context):
    """
    AWS Lambda function handler that delegates to the main lambda_handler.

    Args:
        event: AWS Lambda event object
        context: AWS Lambda context object

    Returns:
        Response from the main lambda_handler
    """
    return lambda_handler(event, context)