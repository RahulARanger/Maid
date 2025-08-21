import boto3
from json import dumps
from loguru import logger
from contextlib import closing
from maid.utils import BUCKET_NAME


def main():
    with closing(boto3.client('s3')) as bucket:
        resp = bucket.create_bucket(
            ACL="private",
            Bucket=BUCKET_NAME,
            CreateBucketConfiguration={
                "LocationConstraint": "eu-north-1"
            },
            ObjectLockEnabledForBucket=False
        )
        logger.info(resp)

        resp = bucket.put_public_access_block(
            Bucket=BUCKET_NAME,
            PublicAccessBlockConfiguration={
                'BlockPublicAcls': True,
                'IgnorePublicAcls': True,
                'BlockPublicPolicy': True,
                'RestrictPublicBuckets': True
            }
        )

        logger.info(resp)

        bucket_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "DenyAllPublicAccess",
                    "Effect": "Deny",
                    "Principal": "*",
                    "Action": "s3:*",
                    "Resource": [
                        f"arn:aws:s3:::{BUCKET_NAME}",
                        f"arn:aws:s3:::{BUCKET_NAME}/*"
                    ],
                    "Condition": {
                        "Bool": {
                            "aws:SecureTransport": "false"
                        }
                    }
                }
            ]
        }

        bucket.put_bucket_policy(
            Bucket=BUCKET_NAME,
            Policy=dumps(bucket_policy)
        )

        bucket.put_bucket_encryption(
            Bucket=BUCKET_NAME,
            ServerSideEncryptionConfiguration={
                'Rules': [
                    {
                        'ApplyServerSideEncryptionByDefault': {
                            'SSEAlgorithm': 'AES256'
                        },
                        'BucketKeyEnabled': True
                    }
                ]
            }
        )



if __name__ == "__main__":
    main()
