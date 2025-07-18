from flask import Flask, request, jsonify
import boto3, uuid, datetime

app = Flask(__name__)

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')

S3_BUCKET = 'tramy-example'
DYNAMODB_TABLE = 'common-dynamodb'
SNS_TOPIC_ARN = 'arn:aws:sns:ap-northeast-1:007730611294:tramy-upload'

table = dynamodb.Table(DYNAMODB_TABLE)

@app.route('/', methods=['GET'])
def list_files():
    response = s3.list_objects_v2(Bucket=S3_BUCKET, Prefix='uploads/')
    files = []
    if 'Contents' in response:
        for obj in response['Contents']:
            files.append(obj['Key'])
    return jsonify({'files': files})
  
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    file_id = str(uuid.uuid4())
    s3_key = f"uploads/{file_id}_{file.filename}"
    s3.put_object(Bucket=S3_BUCKET, Key=s3_key, Body=file)

    item = {
        'FileId': file_id,
        'Filename': file.filename,
        'S3Key': s3_key,
        'UploadedAt': datetime.datetime.utcnow().isoformat()
    }
    table.put_item(Item=item)

    sns.publish(
        TopicArn=SNS_TOPIC_ARN,
        Message=f"New file uploaded: {file.filename} (ID: {file_id})",
        Subject="File Upload Notification"
    )

    return jsonify({'message': 'File uploaded successfully', 'FileId': file_id})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
