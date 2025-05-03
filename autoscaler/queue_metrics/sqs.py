import logging


def get_queue_metrics(aws_wrapper, queue_url):
    """
    Get the current metrics for the SQS queue.

    Args:
        aws_wrapper: AWS wrapper instance
        queue_url: SQS queue URL

    Returns:
        dict: Dictionary containing queue metrics (visible and in-flight messages)
    """
    try:
        sqs_client = aws_wrapper.create_aws_client('sqs')

        # Get queue attributes directly using the URL
        response = sqs_client.get_queue_attributes(
            QueueUrl=queue_url,
            AttributeNames=[
                'ApproximateNumberOfMessages',
                'ApproximateNumberOfMessagesNotVisible'
            ]
        )

        return {
            'visible': int(response['Attributes'].get('ApproximateNumberOfMessages', 0)),
            'in_flight': int(response['Attributes'].get('ApproximateNumberOfMessagesNotVisible', 0))
        }
    except Exception as e:
        logging.error(f"Error getting queue metrics: {e}", exc_info=True)
        return {'visible': 0, 'in_flight': 0}