import logging


def get_queue_metrics(aws_wrapper, topic_arn):
    """
    Get the current metrics for the SNS topic.
    
    Note: SNS is a push-based service without built-in message queuing metrics.
    This implementation uses CloudWatch metrics to estimate load.

    Args:
        aws_wrapper: AWS wrapper instance
        topic_arn: SNS topic ARN

    Returns:
        dict: Dictionary containing queue metrics (visible and in-flight messages)
    """
    try:
        cloudwatch_client = aws_wrapper.create_aws_client('cloudwatch')
        
        # Get the number of messages published to the topic
        # We look at a 5-minute window to get a reasonable view of recent activity
        response = cloudwatch_client.get_metric_statistics(
            Namespace='AWS/SNS',
            MetricName='NumberOfMessagesPublished',
            Dimensions=[
                {
                    'Name': 'TopicName',
                    'Value': topic_arn.split(':')[-1]  # Extract topic name from ARN
                },
            ],
            StartTime=aws_wrapper.get_time_minus_minutes(5),
            EndTime=aws_wrapper.get_time_now(),
            Period=60,
            Statistics=['Sum']
        )
        
        # Calculate the sum of messages in the time period
        datapoints = response.get('Datapoints', [])
        messages_published = sum(dp['Sum'] for dp in datapoints) if datapoints else 0
        
        # For SNS, we don't have a direct "in-flight" metric, so we'll set it to 0
        # We're using the recent publish rate as the primary scaling metric
        
        logging.info(f"SNS topic {topic_arn} has had {messages_published} messages published in the last 5 minutes")
        
        return {
            'visible': int(messages_published),
            'in_flight': 0  # SNS doesn't have in-flight concept like SQS
        }
    except Exception as e:
        logging.error(f"Error getting SNS metrics for topic {topic_arn}: {e}", exc_info=True)
        return {'visible': 0, 'in_flight': 0}