from flask import Flask, request, jsonify
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

app = Flask(__name__)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    # Generate unique filename
    file_id = str(uuid.uuid4())
    s3_key = f"uploads/{file_id}_{file.filename}"

    # Upload to S3
    s3.put_object(Bucket=S3_BUCKET, Key=s3_key, Body=file)

    # Save metadata to DynamoDB
    item = {
        'FileId': file_id,
        'Filename': file.filename,
        'S3Key': s3_key,
        'UploadedAt': datetime.datetime.utcnow().isoformat()
    }
    table.put_item(Item=item)

    # Optionally publish to SNS
    sns.publish(
        TopicArn=SNS_TOPIC_ARN,
        Message=f"New file uploaded: {file.filename} (ID: {file_id})",
        Subject="File Upload Notification"
    )

    return jsonify({'message': 'File uploaded successfully', 'FileId': file_id})

@app.route('/list', methods=['GET'])
def list_files():
    response = s3.list_objects_v2(Bucket=S3_BUCKET, Prefix='uploads/')
    objects = response.get('Contents', [])
    files = [{'Key': obj['Key'], 'Size': obj['Size']} for obj in objects]
    return jsonify(files)

@app.route('/download/<path:key>', methods=['GET'])
def download_file(key):
    file_obj = s3.get_object(Bucket=S3_BUCKET, Key=key)
    content = file_obj['Body'].read().decode('utf-8')
    return jsonify({'content': content})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
