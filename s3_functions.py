import boto3
from botocore.exceptions import ClientError


def upload_file(file_name, bucket):
    object_name = file_name
    s3_client = boto3.client('s3')
    presigned_url = ""

    try:
        response = s3_client.upload_file(file_name, bucket, object_name)

        presigned_url = s3_client.generate_presigned_url('get_object', Params={'Bucket': bucket, 'Key': object_name},
                                                         ExpiresIn=100)

    except ClientError as e:
        pass
    return presigned_url


def get_urls(bucket):
    s3_client = boto3.client('s3')
    public_urls = []
    try:
        for item in s3_client.list_objects(Bucket=bucket)['Contents']:
            presigned_url = s3_client.generate_presigned_url('get_object',
                                                             Params={'Bucket': bucket, 'Key': item['Key']},
                                                             ExpiresIn=100)
            public_urls.append(presigned_url)

        print(public_urls)
    except Exception as e:
        pass
    return public_urls
