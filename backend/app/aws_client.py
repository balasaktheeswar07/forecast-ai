import os
import logging
import boto3
from botocore.exceptions import ClientError, EndpointConnectionError

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("forecast-ai-aws")

# Configuration variables
USE_LOCALSTACK = os.getenv("USE_LOCALSTACK", "true").lower() == "true"
LOCALSTACK_HOST = os.getenv("LOCALSTACK_HOST", "localhost")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

DATASETS_BUCKET = "forecast-ai-datasets"
REPORTS_BUCKET = "forecast-ai-reports"
CAMPAIGNS_TABLE = "forecast-ai-campaigns"

_localstack_endpoint = f"http://{LOCALSTACK_HOST}:4566"

def get_boto3_session():
    """Create a boto3 session with fallback/localstack credentials if needed."""
    if USE_LOCALSTACK:
        return boto3.Session(
            aws_access_key_id="test",
            aws_secret_access_key="test",
            region_name=AWS_REGION
        )
    return boto3.Session()

def get_s3_client():
    """Retrieve S3 client depending on the environment configuration."""
    session = get_boto3_session()
    if USE_LOCALSTACK:
        return session.client("s3", endpoint_url=_localstack_endpoint)
    return session.client("s3")

def get_dynamodb_resource():
    """Retrieve DynamoDB resource depending on the environment configuration."""
    session = get_boto3_session()
    if USE_LOCALSTACK:
        return session.resource("dynamodb", endpoint_url=_localstack_endpoint)
    return session.resource("dynamodb")

def get_dynamodb_client():
    """Retrieve DynamoDB client depending on the environment configuration."""
    session = get_boto3_session()
    if USE_LOCALSTACK:
        return session.client("dynamodb", endpoint_url=_localstack_endpoint)
    return session.client("dynamodb")

def check_aws_connection():
    """Check if LocalStack or AWS is online and accessible."""
    try:
        s3 = get_s3_client()
        s3.list_buckets()
        return True
    except (EndpointConnectionError, ClientError) as e:
        logger.warning(f"Failed to connect to cloud services (LocalStack/AWS): {e}")
        return False

def init_resources():
    """Bootstrap AWS/LocalStack resources (buckets, DynamoDB tables)."""
    if not check_aws_connection():
        logger.info("Cloud services unreachable. Falling back to local storage.")
        # Ensure local folders exist
        os.makedirs("data/datasets", exist_ok=True)
        os.makedirs("data/reports", exist_ok=True)
        os.makedirs("data/models", exist_ok=True)
        return False

    s3 = get_s3_client()
    db_client = get_dynamodb_client()
    db_resource = get_dynamodb_resource()

    # Create S3 buckets
    for bucket in [DATASETS_BUCKET, REPORTS_BUCKET]:
        try:
            s3.head_bucket(Bucket=bucket)
            logger.info(f"S3 Bucket '{bucket}' already exists.")
        except ClientError:
            try:
                if AWS_REGION == "us-east-1":
                    s3.create_bucket(Bucket=bucket)
                else:
                    s3.create_bucket(
                        Bucket=bucket,
                        CreateBucketConfiguration={"LocationConstraint": AWS_REGION}
                    )
                logger.info(f"S3 Bucket '{bucket}' created successfully.")
            except Exception as e:
                logger.error(f"Failed to create S3 bucket '{bucket}': {e}")

    # Create DynamoDB table
    try:
        db_client.describe_table(TableName=CAMPAIGNS_TABLE)
        logger.info(f"DynamoDB table '{CAMPAIGNS_TABLE}' already exists.")
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceNotFoundException":
            try:
                db_resource.create_table(
                    TableName=CAMPAIGNS_TABLE,
                    KeySchema=[
                        {"AttributeName": "campaign_id", "KeyType": "HASH"},
                    ],
                    AttributeDefinitions=[
                        {"AttributeName": "campaign_id", "AttributeType": "S"},
                    ],
                    ProvisionedThroughput={
                        "ReadCapacityUnits": 5,
                        "WriteCapacityUnits": 5
                    }
                )
                logger.info(f"DynamoDB table '{CAMPAIGNS_TABLE}' created successfully.")
            except Exception as ex:
                logger.error(f"Failed to create DynamoDB table: {ex}")
        else:
            logger.error(f"Error checking DynamoDB table: {e}")
    
    return True
