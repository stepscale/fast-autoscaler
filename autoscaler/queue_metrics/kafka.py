import logging
from kafka import KafkaAdminClient, KafkaConsumer
import json


def get_queue_metrics(aws_wrapper, msk_config):
    """
    Get the current metrics for Amazon MSK (Managed Streaming for Kafka).

    Args:
        aws_wrapper: AWS wrapper instance
        msk_config: Dict containing MSK configuration with:
                   - cluster_arn: ARN of the MSK cluster
                   - topic: Kafka topic name
                   - bootstrap_servers: Comma separated list of broker URLs
                   - security_protocol: Security protocol to use (PLAINTEXT, SSL, etc.)
                   - ssl_config: SSL configuration if security_protocol is SSL

    Returns:
        dict: Dictionary containing queue metrics (visible and in-flight messages)
    """
    try:
        # First try to get broker information from AWS API
        kafka_client = aws_wrapper.create_aws_client('kafka')
        
        # Get the MSK cluster information
        cluster_info = kafka_client.describe_cluster(
            ClusterArn=msk_config['cluster_arn']
        )
        
        # Prepare Kafka client configuration
        bootstrap_servers = msk_config.get('bootstrap_servers')
        if not bootstrap_servers and 'ZookeeperConnectString' in cluster_info:
            # In a real implementation, we'd resolve bootstrap servers from ZooKeeper
            # This is simplified for example purposes
            logging.info(f"Using ZooKeeper connection string: {cluster_info['ZookeeperConnectString']}")
            bootstrap_servers = "broker_url_would_be_resolved"  # Placeholder
        
        # Fall back to the provided bootstrap servers if not resolved
        if not bootstrap_servers:
            logging.error("No bootstrap servers available for Kafka connection")
            return {'visible': 0, 'in_flight': 0}
        
        # Connect to Kafka and get topic metrics
        # Note: In a real implementation, you would need to handle authentication properly
        admin_client = KafkaAdminClient(
            bootstrap_servers=bootstrap_servers,
            security_protocol=msk_config.get('security_protocol', 'PLAINTEXT'),
            **msk_config.get('ssl_config', {})
        )
        
        # Get topic lag information - would need a consumer group ID in real implementation
        consumer = KafkaConsumer(
            msk_config['topic'],
            bootstrap_servers=bootstrap_servers,
            group_id=msk_config.get('consumer_group', 'autoscaler-monitor'),
            security_protocol=msk_config.get('security_protocol', 'PLAINTEXT'),
            **msk_config.get('ssl_config', {})
        )
        
        # Get end offsets for all partitions
        topic_partitions = consumer.partitions_for_topic(msk_config['topic'])
        if not topic_partitions:
            logging.warning(f"No partitions found for topic {msk_config['topic']}")
            return {'visible': 0, 'in_flight': 0}
        
        # Calculate lag by comparing current consumer position to end offsets
        total_messages = 0
        total_lag = 0
        
        for partition in topic_partitions:
            # Get end offset (newest message)
            end_offset = consumer.end_offsets([consumer.TopicPartition(msk_config['topic'], partition)])
            
            # Get committed offset (last processed)
            committed = consumer.committed(consumer.TopicPartition(msk_config['topic'], partition))
            
            partition_lag = end_offset - (committed or 0)
            total_lag += partition_lag
            total_messages += end_offset
        
        consumer.close()
        admin_client.close()
        
        logging.info(f"Kafka topic {msk_config['topic']} has {total_messages} total messages with {total_lag} lag")
        
        return {
            'visible': int(total_messages),
            'in_flight': int(total_lag)
        }
    except Exception as e:
        logging.error(f"Error getting Kafka metrics: {e}", exc_info=True)
        return {'visible': 0, 'in_flight': 0}