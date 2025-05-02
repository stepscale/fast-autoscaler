import json
import logging
import os.path
import time
import boto3
import pickle
from botocore.exceptions import ClientError
from botocore.config import Config
from retry import retry

# Define constants - these would typically come from a config file
RETRIES_NUMBER = 3
REGION = 'us-east-1'


class AWSWrapper:
    """
    Wrapper class for AWS operations with retry capabilities and caching
    """

    def __init__(self, aws_access_key_id: str = None, aws_secret_access_key: str = None,
                 aws_session_token: str = None, sso_profile_name: str = None,
                 region_name: str = REGION):
        self._region_name = region_name
        self._session = self._create_boto_session(aws_access_key_id, aws_secret_access_key,
                                                  aws_session_token, sso_profile_name)

    @retry(exceptions=ClientError, tries=RETRIES_NUMBER, delay=3)
    def _create_boto_session(self, aws_access_key_id: str = None, aws_secret_access_key: str = None,
                             aws_session_token: str = None, sso_profile_name: str = None):
        logging.debug("Creating boto3 session via " + ("SSO profile name" if sso_profile_name else "AWS access key"))
        return boto3.session.Session(profile_name=sso_profile_name, region_name=self._region_name) \
            if sso_profile_name else boto3.session.Session(aws_access_key_id, aws_secret_access_key,
                                                           aws_session_token, region_name=self._region_name)

    @retry(exceptions=ClientError, tries=RETRIES_NUMBER, delay=3)
    def create_aws_client(self, service_name: str, region_name: str = None, config=None):
        """
        Create a boto3 client with retry capability.

        Args:
            service_name: AWS service name ('ecs', 's3', 'sqs', etc.)
            region_name: Optional AWS region override
            config: Optional boto3 configuration

        Returns:
            Boto3 client for the requested service
        """
        logging.debug(f'creating aws client for: {service_name}')

        default_config = Config(
            max_pool_connections=5000
        )
        return self._session.client(service_name=service_name, region_name=region_name,
                                    config=config or default_config)

    def get_file_content_from_s3_bucket(self, bucket_name: str, file_key: str, no_cache: bool = False):
        """
        Get file content from an S3 bucket with optional caching.

        Args:
            bucket_name: S3 bucket name
            file_key: Path to the file in the bucket
            no_cache: If True, bypasses cache and retrieves directly from S3

        Returns:
            bytes: The file content
        """
        s3_client = self.create_aws_client('s3')

        if no_cache:
            # Bypass cache and get directly from S3
            response = s3_client.get_object(Bucket=bucket_name, Key=file_key)
            if not response:
                raise Exception(
                    f"Didn't manage to get file's content of this file: {file_key}, from the bucket: {bucket_name}")
            file_content = response['Body'].read()
        else:
            # Use cache as before
            response = AWSWrapper.cache_get_object(s3_client, bucket_name, file_key)
            if not response:
                raise Exception(
                    f"Didn't manage to get file's content of this file: {file_key}, from the bucket: {bucket_name}")
            file_content = response['Content']

        return file_content

    @staticmethod
    def cache_get_object(s3_client, bucket_name, file_key):
        """
        Get object from S3 with local caching for improved performance.

        Args:
            s3_client: Boto3 S3 client
            bucket_name: S3 bucket name
            file_key: Path to the file in the bucket

        Returns:
            dict: Response data including file content
        """
        cache_dir = "/tmp"
        file_dir = os.path.dirname(file_key)
        full_cache_dir = os.path.join(cache_dir, file_dir)
        basename_file_key = f"{os.path.basename(file_key)}.pkl"
        cache_file_path = os.path.join(full_cache_dir, basename_file_key)

        logging.debug(
            f"inside cache_get_object | file_dir: {file_dir} | full_cache_dir: {full_cache_dir} | basename_file_key: {basename_file_key} | cache_file_path: {cache_file_path}")

        if not os.path.exists(full_cache_dir):
            os.makedirs(full_cache_dir, exist_ok=True)

        if os.path.exists(cache_file_path) and os.path.getsize(cache_file_path) > 0:
            try:
                with open(cache_file_path, 'rb') as f:
                    cached_response = pickle.load(f)
                    logging.debug("cache hit, loaded from file.")
            except (EOFError, pickle.UnpicklingError) as e:
                logging.warning(f"Cache file is corrupt: {str(e)}. Reloading from S3.")
                cached_response = None
            except Exception as e:
                logging.error(f"Unexpected error loading cache: {e}")
                cached_response = None
        else:
            logging.debug("Cache file does not exist or is empty, loading from S3.")
            cached_response = None

        if cached_response is None:
            try:
                response = s3_client.get_object(Bucket=bucket_name, Key=file_key)
                file_content = response['Body'].read()

                cached_response = {
                    'Content': file_content,
                    'ContentType': response.get('ContentType', 'application/octet-stream'),
                    'Metadata': response.get('Metadata', {}),
                    'HTTPStatusCode': response.get('ResponseMetadata', {}).get('HTTPStatusCode', 200),
                    'CachedTime': time.time()
                }

                with open(cache_file_path, 'wb') as f:
                    pickle.dump(cached_response, f)

                logging.debug("Downloaded and cached new file from S3.")
            except Exception as e:
                logging.error(
                    f"Failed to download file from S3: bucket_name: {bucket_name} | file_key: {file_key} Error: {e}",
                    exc_info=True)
                cached_response = None

        return cached_response

    @retry(exceptions=ClientError, tries=RETRIES_NUMBER, delay=3)
    def upload_bytes_to_s3(self, bucket: str, file_path: str, content: bytes, metadata: dict = None):
        """
        Upload bytes directly to an S3 bucket

        Args:
            bucket: The name of the S3 bucket
            file_path: The path where the file should be stored in the bucket
            content: The bytes to upload
            metadata: Optional metadata for the S3 object
        """
        s3_client = self.create_aws_client('s3')

        try:
            s3_client.put_object(
                Bucket=bucket,
                Key=file_path,
                Body=content,
                Metadata=metadata or {}
            )
            logging.debug(f"Successfully uploaded bytes to s3://{bucket}/{file_path}")
        except ClientError as e:
            logging.error(f"Error uploading bytes to s3://{bucket}/{file_path}: {e}")
            raise