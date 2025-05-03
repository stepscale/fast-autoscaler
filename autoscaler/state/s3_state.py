import json
import logging
import time
from datetime import datetime


def get_last_scaling_time(aws_wrapper, action_type, s3_config_bucket, ecs_cluster, service_name):
    """
    Get the time of the last scaling action from S3.

    Args:
        aws_wrapper: AWS wrapper instance
        action_type: 'up' or 'down' scaling action
        s3_config_bucket: S3 bucket name for state storage
        ecs_cluster: ECS cluster name
        service_name: ECS service name

    Returns:
        tuple: (timestamp, count) of the last scaling action
    """
    try:
        # Create a state file path for this specific service and action
        state_key = f"autoscaling-state/{ecs_cluster}/{service_name}/{action_type}-last-action.json"
        logging.info(f"Retrieving last scaling time for {action_type} from {s3_config_bucket}/{state_key}")

        try:
            # Use the aws_wrapper to get the file content
            file_content = aws_wrapper.get_file_content_from_s3_bucket(s3_config_bucket, state_key, no_cache=True)

            if file_content:
                try:
                    state_data = json.loads(file_content.decode('utf-8'))
                    timestamp = state_data.get('timestamp')
                    count = state_data.get('count', 0)

                    if timestamp:
                        try:
                            # First try to parse as float timestamp (epoch time)
                            ts = float(timestamp)
                            readable_time = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
                            logging.info(
                                f"Retrieved last {action_type} scaling timestamp: {ts} ({readable_time}), count: {count}")
                            return ts, count
                        except ValueError:
                            # If it's not a numeric timestamp, try to parse as ISO format
                            try:
                                # Convert ISO format to timestamp
                                dt = datetime.fromisoformat(timestamp)
                                ts = dt.timestamp()
                                readable_time = dt.strftime('%Y-%m-%d %H:%M:%S')
                                logging.info(
                                    f"Converted legacy datetime format to timestamp: {timestamp} -> {ts} ({readable_time}), count: {count}")
                                return ts, count
                            except ValueError:
                                # If we can't parse it at all, use a default
                                logging.warning(f"Invalid timestamp format in scaling state: {timestamp}")
                                return 0.0, count
                    else:
                        logging.info(f"No timestamp found in state data for {action_type}")
                except json.JSONDecodeError as e:
                    logging.warning(f"Error parsing JSON state data: {e}")

        except Exception as e:
            error_message = str(e)
            if "NoSuchKey" in error_message:
                logging.info(f"No previous scaling state found for {action_type}")
            else:
                logging.warning(f"Error getting scaling state from S3: {e}")

    except Exception as e:
        logging.warning(f"Error reading last scaling time from S3: {e}")

    # Default to a very old time if no record exists
    logging.info(f"Using default timestamp 0.0 (1970-01-01 00:00:00) for {action_type} scaling action")
    return 0.0, 0


def set_last_scaling_time(aws_wrapper, action_type, s3_config_bucket, ecs_cluster, service_name, count=None):
    """
    Set the time of the last scaling action in S3.

    Args:
        aws_wrapper: AWS wrapper instance
        action_type: 'up' or 'down' scaling action
        s3_config_bucket: S3 bucket name for state storage
        ecs_cluster: ECS cluster name
        service_name: ECS service name
        count: Optional count to set (will increment current count if not provided)
    """
    try:
        # Create a state file path for this specific service and action
        state_key = f"autoscaling-state/{ecs_cluster}/{service_name}/{action_type}-last-action.json"

        # Get the current count if none provided
        if count is None:
            _, current_count = get_last_scaling_time(aws_wrapper, action_type, s3_config_bucket, ecs_cluster,
                                                     service_name)
            count = current_count + 1

        # Use current Unix timestamp
        now = time.time()
        readable_time = datetime.fromtimestamp(now).strftime('%Y-%m-%d %H:%M:%S')

        # Create state object
        state_data = {
            'timestamp': now,
            'cluster': ecs_cluster,
            'service': service_name,
            'action_type': action_type,
            'count': count
        }

        # Convert to JSON and then to bytes
        state_json = json.dumps(state_data)
        state_bytes = state_json.encode('utf-8')

        logging.info(f"Setting last {action_type} scaling timestamp to {now} ({readable_time}), count: {count}")

        # Use the aws_wrapper to upload bytes to S3
        aws_wrapper.upload_bytes_to_s3(
            bucket=s3_config_bucket,
            file_path=state_key,
            content=state_bytes,
            metadata={'ContentType': 'application/json'}
        )

        logging.info(
            f"Successfully saved {action_type} scaling state to S3 with timestamp {now} ({readable_time}), count {count}")

    except Exception as e:
        logging.warning(f"Error writing last scaling time to S3: {e}")