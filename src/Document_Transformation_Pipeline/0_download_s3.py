import boto3
from botocore.exceptions import ClientError

def download_file_from_s3(bucket_name: str, s3_key: str, local_path: str):
    """
    S3에서 파일을 다운로드하여 로컬에 저장한다.
    
    :param bucket_name: S3 버킷명
    :param s3_key: S3 내 파일 경로 (예: folder/data.csv)
    :param local_path: 로컬 저장 경로
    """
    s3 = boto3.client("s3")

    try:
        s3.download_file(bucket_name, s3_key, local_path)
        print(f"다운로드 완료: {local_path}")
    except ClientError as e:
        print(f"에러 발생: {e}")
        raise

# 사용 예시
download_file_from_s3(
    bucket_name="miraeasset-product-knowledge-graph",
    s3_key="zeroin.tar",
    local_path="./zeroin.tar"
)