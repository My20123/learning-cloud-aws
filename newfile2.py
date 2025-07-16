import boto3
import uuid
import datetime

# Initialize clients
s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')

# Config
S3_BUCKET = 'your-bucket-name'
DYNAMODB_TABLE = 'your-table-name'
SNS_TOPIC_ARN = 'arn:aws:sns:region:account-id:your-topic'

table = dynamodb.Table(DYNAMODB_TABLE)

# Giả sử file local
local_file_path = '/home/ec2-user/test.txt'
filename = 'test.txt'

# Generate unique filename
file_id = str(uuid.uuid4())
s3_key = f"uploads/{file_id}_{filename}"

# Upload to S3
with open(local_file_path, 'rb') as f:
    s3.put_object(Bucket=S3_BUCKET, Key=s3_key, Body=f)

# Save metadata to DynamoDB
item = {
    'FileId': file_id,
    'Filename': filename,
    'S3Key': s3_key,
    'UploadedAt': datetime.datetime.utcnow().isoformat()
}
table.put_item(Item=item)

# Optionally publish to SNS
sns.publish(
    TopicArn=SNS_TOPIC_ARN,
    Message=f"New file uploaded: {filename} (ID: {file_id})",
    Subject="File Upload Notification"
)

print('File uploaded successfully.')
