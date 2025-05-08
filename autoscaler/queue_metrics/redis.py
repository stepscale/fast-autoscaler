import logging
import redis
import json


def get_queue_metrics(aws_wrapper, redis_config):
    """
    Get the current metrics for a Redis-based queue.
    
    Supports both Redis Lists and Redis Streams as queue implementations.

    Args:
        aws_wrapper: AWS wrapper instance
        redis_config: Dict containing Redis configuration with:
                     - host: Redis host
                     - port: Redis port
                     - password: Redis password
                     - queue_key: Key name for the queue
                     - queue_type: 'list' or 'stream'
                     - processing_key: Key used to track processing items (for list-based queues)
                     - consumer_group: Consumer group name (for stream-based queues)

    Returns:
        dict: Dictionary containing queue metrics (visible and in-flight messages)
    """
    try:
        # Connect to Redis
        r = redis.Redis(
            host=redis_config['host'],
            port=redis_config.get('port', 6379),
            password=redis_config.get('password'),
            ssl=redis_config.get('use_ssl', True),
            decode_responses=True
        )
        
        queue_type = redis_config.get('queue_type', 'list')
        queue_key = redis_config['queue_key']
        
        if queue_type == 'list':
            # For Redis list-based queues
            # Get the number of items in the queue
            queue_length = r.llen(queue_key)
            
            # Get in-flight count from processing set/list if available
            processing_key = redis_config.get('processing_key')
            in_flight = 0
            if processing_key:
                # Check if it's a set, list, or hash
                key_type = r.type(processing_key)
                if key_type == 'set':
                    in_flight = r.scard(processing_key)
                elif key_type == 'list':
                    in_flight = r.llen(processing_key)
                elif key_type == 'hash':
                    in_flight = len(r.hkeys(processing_key))
            
            logging.info(f"Redis list queue {queue_key} has {queue_length} pending messages "
                        f"and {in_flight} in-flight messages")
            
            return {
                'visible': queue_length,
                'in_flight': in_flight
            }
        
        elif queue_type == 'stream':
            # For Redis stream-based queues
            # Get information about the stream
            stream_info = r.xinfo_stream(queue_key)
            
            # Get total number of messages in the stream
            total_messages = stream_info['length']
            
            # Get consumer group information
            consumer_group = redis_config.get('consumer_group')
            in_flight = 0
            
            if consumer_group:
                try:
                    # Get consumer group information
                    group_info = r.xinfo_groups(queue_key)
                    
                    # Find our consumer group
                    for group in group_info:
                        if group['name'] == consumer_group:
                            # Pending messages are those that are being processed
                            in_flight = group['pending']
                            break
                except redis.exceptions.ResponseError:
                    # Consumer group might not exist yet
                    pass
            
            # Calculate visible messages (those not yet being processed)
            visible = total_messages - in_flight
            
            logging.info(f"Redis stream {queue_key} has {visible} pending messages "
                        f"and {in_flight} in-flight messages")
            
            return {
                'visible': max(0, visible),  # Ensure we don't return negative values
                'in_flight': in_flight
            }
        
        else:
            logging.error(f"Unsupported Redis queue type: {queue_type}")
            return {'visible': 0, 'in_flight': 0}
        
    except Exception as e:
        logging.error(f"Error getting Redis metrics: {e}", exc_info=True)
        return {'visible': 0, 'in_flight': 0}