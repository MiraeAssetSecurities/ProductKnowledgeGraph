import os
import boto3
from botocore.exceptions import ClientError


def upload_directory_to_s3(
    local_dir: str,
    bucket_name: str,
    s3_prefix: str = ""
):
    """
    로컬 디렉토리의 모든 파일을 디렉토리 구조 그대로 S3에 업로드한다.

    :param local_dir: 업로드할 로컬 디렉토리 경로
    :param bucket_name: S3 버킷명
    :param s3_prefix: S3 내 저장될 루트 경로 (선택)
                      예: "raw-data/" 로 주면 해당 경로 아래 업로드됨
    """

    s3 = boto3.client("s3")

    for root, dirs, files in os.walk(local_dir):
        for file in files:
            local_path = os.path.join(root, file)

            # 로컬 기준 상대경로 계산
            relative_path = os.path.relpath(local_path, local_dir)

            # S3 Key 생성 (윈도우 대응 포함)
            s3_key = os.path.join(s3_prefix, relative_path).replace("\\", "/")

            try:
                s3.upload_file(local_path, bucket_name, s3_key)
                print(f"업로드 완료: {local_path} → s3://{bucket_name}/{s3_key}")
            except ClientError as e:
                print(f"에러 발생: {local_path} → {e}")
                raise


# 사용 예시
upload_directory_to_s3(
    local_dir="/home/ubuntu/ProductKnowledgeGraph/temp/zeroin",
    bucket_name="miraeasset-product-knowledge-graph",
    s3_prefix="zeroin"
)