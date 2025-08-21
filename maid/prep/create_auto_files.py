import boto3
from loguru import logger
from contextlib import closing
from maid.utils import BUCKET_NAME, ARTIFACTS_FOLDER, TEMP_ARTIFACTS_FOLDER


def main():
    with closing(boto3.client('s3')) as bucket:
        resp = bucket.put_object(
            Bucket=BUCKET_NAME,
            Key=ARTIFACTS_FOLDER + '/',
        )
        logger.info(resp)

        resp = bucket.put_object(
            Bucket=BUCKET_NAME,
            Key=TEMP_ARTIFACTS_FOLDER + '/',
        )
        logger.info(resp)

        resp = bucket.put_bucket_lifecycle_configuration(
            Bucket=BUCKET_NAME,
            LifecycleConfiguration={
                'Rules': [
                    {
                        'ID': 'DeleteUploadTasksAfter10Days',
                        'Prefix': TEMP_ARTIFACTS_FOLDER + '/',
                        'Status': 'Enabled',
                        'Expiration': {
                            'Days': 10
                        }
                    }
                ]
            }
        )

        logger.info(resp)


if __name__ == "__main__":
    main()
