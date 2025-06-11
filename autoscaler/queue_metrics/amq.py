import logging
import stomp
import json
import time
import uuid
from urllib.parse import urlparse


def get_queue_metrics(aws_wrapper, amq_config):
    """
    Get the current metrics for an Amazon MQ (ActiveMQ) queue.

    Args:
        aws_wrapper: AWS wrapper instance
        amq_config: Dict containing Amazon MQ configuration with:
                  - broker_id: ID of the Amazon MQ broker
                  - queue_name: Queue name
                  - username: ActiveMQ username
                  - password: ActiveMQ password
                  - use_ssl: Whether to use SSL (default True)
                  - region: AWS region (default is from aws_wrapper)
                  - connection_timeout: Timeout for STOMP connection in seconds (default 5)
                  - read_timeout: Timeout for reading data in seconds (default 15)
                  - retry_attempts: Number of retry attempts for STOMP (default 1)
                  - stats_destination_prefix: Prefix for stats topic (default 'ActiveMQ.Statistics.Destination')

    Returns:
        dict: Dictionary containing queue metrics (visible and in-flight messages)
    """
    # Set defaults for timeouts and retries
    connection_timeout = amq_config.get('connection_timeout', 5)
    read_timeout = amq_config.get('read_timeout', 15)
    retry_attempts = amq_config.get('retry_attempts', 1)
    stats_prefix = amq_config.get('stats_destination_prefix', 'ActiveMQ.Statistics.Destination')
    
    try:
        # First get broker information from AWS API
        mq_client = aws_wrapper.create_aws_client('mq', 
                                                 region_name=amq_config.get('region'))
        
        # Get the broker details
        broker_response = mq_client.describe_broker(
            BrokerId=amq_config['broker_id']
        )
        
        # Extract broker host information
        if not broker_response or 'BrokerInstances' not in broker_response:
            logging.error(f"Unable to get broker information for {amq_config['broker_id']}")
            return {'visible': 0, 'in_flight': 0}
        
        # Get broker endpoints
        endpoints = broker_response.get('BrokerInstances', [{}])[0].get('Endpoints', [])
        if not endpoints:
            logging.error(f"No endpoints found for broker {amq_config['broker_id']}")
            return {'visible': 0, 'in_flight': 0}
        
        # Get the STOMP endpoint
        # ActiveMQ typically uses STOMP protocol for management operations
        stomp_endpoint = None
        for endpoint in endpoints:
            if 'stomp' in endpoint.lower():
                stomp_endpoint = endpoint
                break
        
        if not stomp_endpoint:
            # Fall back to the first endpoint if no STOMP endpoint found
            stomp_endpoint = endpoints[0]
            logging.warning(f"No STOMP endpoint found, using {stomp_endpoint}")
        
        # Parse host and port from endpoint using urlparse for better reliability
        parsed_url = urlparse(stomp_endpoint)
        host = parsed_url.hostname or parsed_url.path  # If no hostname, use path
        
        # Default ports based on protocol
        default_port = 61613  # Default STOMP port
        if 'stomp+ssl' in stomp_endpoint:
            default_port = 61614  # Default STOMP SSL port
            
        port = parsed_url.port or default_port
        
        logging.info(f"Connecting to ActiveMQ broker at {host}:{port}")
        
        # Start with direct STOMP approach and retry if needed
        for attempt in range(retry_attempts + 1):
            try:
                stats = get_stats_via_stomp(
                    host, port, 
                    amq_config.get('username', 'admin'),
                    amq_config.get('password', 'admin'),
                    amq_config['queue_name'],
                    use_ssl=amq_config.get('use_ssl', True),
                    connection_timeout=connection_timeout,
                    read_timeout=read_timeout,
                    stats_prefix=stats_prefix
                )
                
                if stats:
                    # Successfully got stats via STOMP
                    return stats
                else:
                    logging.warning(
                        f"STOMP attempt {attempt+1}/{retry_attempts+1} failed to get queue statistics")
            except Exception as e:
                logging.warning(
                    f"STOMP attempt {attempt+1}/{retry_attempts+1} failed with error: {e}")
        
        # If we reached here, STOMP approaches failed after all retries
        # Fall back to CloudWatch metrics
        logging.info("Direct STOMP access failed after all retries, falling back to CloudWatch metrics")
        return get_cloudwatch_metrics(aws_wrapper, amq_config)
        
    except Exception as e:
        logging.error(f"Error getting ActiveMQ metrics: {e}", exc_info=True)
        return {'visible': 0, 'in_flight': 0}


def get_stats_via_stomp(host, port, username, password, queue_name, use_ssl=True, 
                       connection_timeout=5, read_timeout=15, stats_prefix='ActiveMQ.Statistics.Destination'):
    """
    Get queue statistics via direct STOMP connection to ActiveMQ.
    
    Args:
        host: ActiveMQ host
        port: ActiveMQ STOMP port
        username: ActiveMQ username
        password: ActiveMQ password
        queue_name: Queue name to get statistics for
        use_ssl: Whether to use SSL connection
        connection_timeout: Timeout for initial connection
        read_timeout: Timeout for reading response
        stats_prefix: Prefix for statistics topic
        
    Returns:
        dict: Queue metrics or None if failed
    """
    # Prepare connection
    conn = stomp.Connection(
        host_and_ports=[(host, port)],
        use_ssl=use_ssl,
        reconnect_attempts_max=1
    )
    
    # Create a unique subscription ID
    subscription_id = str(uuid.uuid4())
    
    # Set up a listener to receive the queue statistics
    class QueueStatsListener(stomp.ConnectionListener):
        def __init__(self):
            self.queue_stats = None
            self.error = None
            self.received = False
        
        def on_message(self, frame):
            try:
                logging.debug(f"Received STOMP message: {frame.body[:100]}...")
                self.queue_stats = json.loads(frame.body)
                self.received = True
            except Exception as e:
                self.error = f"Error parsing queue stats: {e}"
                self.received = True
        
        def on_error(self, frame):
            self.error = frame.body
            self.received = True
            
        def on_disconnected(self):
            if not self.received:
                self.error = "Connection disconnected before receiving response"
                self.received = True

    listener = QueueStatsListener()
    conn.set_listener('queue_stats_listener', listener)
    
    try:
        # Connect to the broker with timeout
        conn.connect(
            username=username,
            password=password,
            wait=True,
            headers={'client-id': f'autoscaler-{uuid.uuid4()}'},
            timeout=connection_timeout
        )
        
        # Explicitly start the connection to ensure we receive messages
        conn.start()
        
        # Set up the topic name for statistics
        # Different ActiveMQ versions and configurations may use different paths
        query_destination = f"/topic/{stats_prefix}.{queue_name}"
        logging.debug(f"Subscribing to statistics topic: {query_destination}")
        
        # Subscribe to receive the statistics
        conn.subscribe(destination=query_destination, id=subscription_id, ack='auto')
        
        # Request the statistics by sending a message
        # This might trigger StatisticsPlugin to publish stats
        destination = f"/queue/{queue_name}"
        conn.send(body='{"command":"stats"}', destination=destination)
        
        # Wait for response (with timeout)
        start_time = time.time()
        timeout = start_time + read_timeout
        
        # Wait loop with periodic logging
        last_log_time = start_time
        while not listener.received and time.time() < timeout:
            time.sleep(0.1)
            
            # Log every 3 seconds for visibility
            if time.time() - last_log_time > 3:
                logging.debug("Still waiting for ActiveMQ statistics response...")
                last_log_time = time.time()
        
        # Check if we got a response
        if not listener.received:
            logging.warning(f"Timeout waiting for ActiveMQ statistics after {read_timeout} seconds")
            return None
            
        # Check for errors
        if listener.error:
            logging.warning(f"Error in ActiveMQ statistics response: {listener.error}")
            return None
            
        # If we didn't get statistics
        if not listener.queue_stats:
            logging.warning(f"No statistics received from STOMP topic for queue {queue_name}")
            return None
            
        # Extract queue metrics from the statistics
        stats = listener.queue_stats
        logging.debug(f"Received statistics: {stats}")
        
        # Different versions of ActiveMQ return different statistics formats
        # Handle both common formats
        if 'size' in stats:
            # Newer format
            queue_size = stats.get('size', 0)
            in_flight = stats.get('inflightCount', 0)
        elif 'QueueSize' in stats:
            # Older format
            queue_size = stats.get('QueueSize', 0)
            in_flight = stats.get('InFlightCount', 0)
        else:
            # Unknown format, try to find relevant keys
            queue_size = 0
            in_flight = 0
            for key, value in stats.items():
                if isinstance(value, (int, float)):
                    if 'size' in key.lower() or 'count' in key.lower():
                        if 'inflight' in key.lower() or 'in_flight' in key.lower():
                            in_flight = stats.get(key, 0)
                        else:
                            queue_size = stats.get(key, 0)
        
        logging.info(f"ActiveMQ queue {queue_name} has {queue_size} pending messages "
                    f"and {in_flight} in-flight messages")
        
        return {
            'visible': int(queue_size),
            'in_flight': int(in_flight)
        }
    
    except Exception as e:
        logging.warning(f"Error in STOMP connection to ActiveMQ: {e}", exc_info=True)
        return None
    finally:
        # Always ensure we disconnect properly
        try:
            # Only disconnect if we were connected
            if conn.is_connected():
                conn.disconnect()
                logging.debug("Disconnected from STOMP")
        except Exception as e:
            logging.warning(f"Error disconnecting from STOMP: {e}")


def get_cloudwatch_metrics(aws_wrapper, amq_config):
    """
    Fallback method to get Amazon MQ metrics from CloudWatch.

    Args:
        aws_wrapper: AWS wrapper instance
        amq_config: Amazon MQ configuration dict

    Returns:
        dict: Dictionary containing queue metrics
    """
    try:
        logging.info(f"Getting CloudWatch metrics for ActiveMQ queue {amq_config['queue_name']}")
        cloudwatch_client = aws_wrapper.create_aws_client('cloudwatch', 
                                                        region_name=amq_config.get('region'))
        
        # Get queue size metric
        queue_size_response = cloudwatch_client.get_metric_statistics(
            Namespace='AWS/AmazonMQ',
            MetricName='QueueSize',
            Dimensions=[
                {
                    'Name': 'Broker',
                    'Value': amq_config['broker_id']
                },
                {
                    'Name': 'Queue',
                    'Value': amq_config['queue_name']
                }
            ],
            StartTime=aws_wrapper.get_time_minus_minutes(5),
            EndTime=aws_wrapper.get_time_now(),
            Period=60,
            Statistics=['Maximum']
        )
        
        # Extract the most recent/maximum queue size
        datapoints = queue_size_response.get('Datapoints', [])
        queue_size = max([dp['Maximum'] for dp in datapoints]) if datapoints else 0
        
        # For Amazon MQ, there's no direct "in-flight" metric in CloudWatch
        # We could approximate it by looking at enqueue/dequeue rates
        enqueue_response = cloudwatch_client.get_metric_statistics(
            Namespace='AWS/AmazonMQ',
            MetricName='EnqueueCount',
            Dimensions=[
                {
                    'Name': 'Broker',
                    'Value': amq_config['broker_id']
                },
                {
                    'Name': 'Queue',
                    'Value': amq_config['queue_name']
                }
            ],
            StartTime=aws_wrapper.get_time_minus_minutes(5),
            EndTime=aws_wrapper.get_time_now(),
            Period=300,  # 5 minutes
            Statistics=['Sum']
        )
        
        dequeue_response = cloudwatch_client.get_metric_statistics(
            Namespace='AWS/AmazonMQ',
            MetricName='DequeueCount',
            Dimensions=[
                {
                    'Name': 'Broker',
                    'Value': amq_config['broker_id']
                },
                {
                    'Name': 'Queue',
                    'Value': amq_config['queue_name']
                }
            ],
            StartTime=aws_wrapper.get_time_minus_minutes(5),
            EndTime=aws_wrapper.get_time_now(),
            Period=300,  # 5 minutes
            Statistics=['Sum']
        )
        
        # Calculate enqueue and dequeue counts
        enqueue_datapoints = enqueue_response.get('Datapoints', [])
        dequeue_datapoints = dequeue_response.get('Datapoints', [])
        
        enqueue_count = sum([dp['Sum'] for dp in enqueue_datapoints]) if enqueue_datapoints else 0
        dequeue_count = sum([dp['Sum'] for dp in dequeue_datapoints]) if dequeue_datapoints else 0
        
        # Rough estimate of in-flight messages (messages that have been consumed but not acknowledged)
        # This is a heuristic based on the difference between enqueued and dequeued messages
        estimated_in_flight = max(0, enqueue_count - dequeue_count - queue_size)
        
        logging.info(f"CloudWatch metrics for ActiveMQ queue {amq_config['queue_name']}: "
                    f"size={queue_size}, estimated in-flight={estimated_in_flight}")
        
        return {
            'visible': int(queue_size),
            'in_flight': int(estimated_in_flight)
        }
    except Exception as e:
        logging.error(f"Error getting CloudWatch metrics for ActiveMQ: {e}", exc_info=True)
        return {'visible': 0, 'in_flight': 0}