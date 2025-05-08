import logging


def get_queue_metrics(aws_wrapper, stream_name):
    """
    Get the current metrics for the Kinesis Data Stream.

    Args:
        aws_wrapper: AWS wrapper instance
        stream_name: Kinesis stream name

    Returns:
        dict: Dictionary containing queue metrics (visible and in-flight messages)
    """
    try:
        kinesis_client = aws_wrapper.create_aws_client('kinesis')
        
        # Get stream description which includes shard info
        response = kinesis_client.describe_stream_summary(
            StreamName=stream_name
        )
        
        # Get enhanced monitoring metrics if available
        cloudwatch_client = aws_wrapper.create_aws_client('cloudwatch')
        metrics_response = cloudwatch_client.get_metric_statistics(
            Namespace='AWS/Kinesis',
            MetricName='IncomingRecords',
            Dimensions=[
                {
                    'Name': 'StreamName',
                    'Value': stream_name
                },
            ],
            StartTime=aws_wrapper.get_time_minus_minutes(5),
            EndTime=aws_wrapper.get_time_now(),
            Period=60,
            Statistics=['Sum']
        )
        
        # Calculate incoming records in the last 5 minutes
        datapoints = metrics_response.get('Datapoints', [])
        incoming_records = sum(dp['Sum'] for dp in datapoints) if datapoints else 0
        
        # Get GetRecords iterator age to determine processing backlog
        iterator_age_response = cloudwatch_client.get_metric_statistics(
            Namespace='AWS/Kinesis',
            MetricName='GetRecords.IteratorAgeMilliseconds',
            Dimensions=[
                {
                    'Name': 'StreamName',
                    'Value': stream_name
                },
            ],
            StartTime=aws_wrapper.get_time_minus_minutes(5),
            EndTime=aws_wrapper.get_time_now(),
            Period=60,
            Statistics=['Maximum']
        )
        
        # Use iterator age to estimate "in flight" (backlog) - convert to seconds
        age_datapoints = iterator_age_response.get('Datapoints', [])
        max_iterator_age_ms = max([dp['Maximum'] for dp in age_datapoints]) if age_datapoints else 0
        
        # Get approximate number of "in flight" or unprocessed records
        # This is a rough estimate based on incoming rate and processing delay
        estimated_backlog = (max_iterator_age_ms / 1000) * (incoming_records / 300) if incoming_records > 0 else 0
        
        logging.info(f"Kinesis stream {stream_name} has approximately {incoming_records} recent records "
                    f"with max iterator age of {max_iterator_age_ms}ms")
        
        return {
            'visible': int(incoming_records),
            'in_flight': int(estimated_backlog)
        }
    except Exception as e:
        logging.error(f"Error getting Kinesis metrics for stream {stream_name}: {e}", exc_info=True)
        return {'visible': 0, 'in_flight': 0}