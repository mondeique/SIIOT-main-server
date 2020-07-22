import boto3

from siiot.loader import load_credential

ACCESS_KEY = load_credential("_AWS_ACCESS_KEY_ID","")
SECRET_ACCESS_KEY = load_credential("_AWS_SECRET_ACCESS_KEY","")

# s3 client 생성
def upload_s3(file, name):
    s3 = boto3.client('s3', aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_ACCESS_KEY)
    s3.upload_fileobj(file, 'siiot-media-storage', name, ExtraArgs={
        "ContentType": 'image/jpeg'
    })