import logging
import pika
import ssl


def get_queue_metrics(aws_wrapper, rabbitmq_config):
    """
    Get the current metrics for a RabbitMQ queue.

    Args:
        aws_wrapper: AWS wrapper instance
        rabbitmq_config: Dict containing RabbitMQ configuration with:
                        - host: RabbitMQ host
                        - port: RabbitMQ port
                        - vhost: Virtual host (default '/')
                        - queue: Queue name
                        - username: RabbitMQ username
                        - password: RabbitMQ password
                        - use_ssl: Whether to use SSL (default True)

    Returns:
        dict: Dictionary containing queue metrics (visible and in-flight messages)
    """
    try:
        # Prepare connection parameters
        credentials = pika.PlainCredentials(
            username=rabbitmq_config.get('username', 'guest'),
            password=rabbitmq_config.get('password', 'guest')
        )
        
        # Set up SSL context if needed
        ssl_options = None
        if rabbitmq_config.get('use_ssl', True):
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            ssl_options = pika.SSLOptions(context)
        
        # Create connection parameters
        params = pika.ConnectionParameters(
            host=rabbitmq_config['host'],
            port=rabbitmq_config.get('port', 5672),
            virtual_host=rabbitmq_config.get('vhost', '/'),
            credentials=credentials,
            ssl_options=ssl_options
        )
        
        # Connect to RabbitMQ
        connection = pika.BlockingConnection(params)
        channel = connection.channel()
        
        # Declare the queue passively to check if it exists and get metrics
        queue_info = channel.queue_declare(
            queue=rabbitmq_config['queue'],
            passive=True  # Don't create the queue, just check it
        )
        
        # Get queue metrics
        message_count = queue_info.method.message_count
        consumer_count = queue_info.method.consumer_count
        
        # Calculate in-flight messages - this is an approximation
        # In RabbitMQ, we don't have a direct "in_flight" count, but can estimate based on consumers
        # Assuming each consumer has at least one message in processing if there are messages
        in_flight_estimate = min(message_count, consumer_count) if consumer_count > 0 else 0
        
        connection.close()
        
        logging.info(f"RabbitMQ queue {rabbitmq_config['queue']} has {message_count} ready messages "
                    f"and approximately {in_flight_estimate} in-flight messages with {consumer_count} consumers")
        
        return {
            'visible': message_count,
            'in_flight': in_flight_estimate
        }
    except Exception as e:
        logging.error(f"Error getting RabbitMQ metrics: {e}", exc_info=True)
        return {'visible': 0, 'in_flight': 0}