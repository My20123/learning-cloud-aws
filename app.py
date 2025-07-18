from flask import Flask, request, jsonify, send_file
import boto3, uuid, datetime, io

app = Flask(__name__)

# Cấu hình AWS
S3_BUCKET = 'tramy-example'
DYNAMODB_TABLE = 'common-dynamodb'
SNS_TOPIC_ARN = 'arn:aws:sns:ap-northeast-1:007730611294:tramy-upload'

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')
table = dynamodb.Table(DYNAMODB_TABLE)

# Upload file
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

# List files
@app.route('/files', methods=['GET'])
def list_files():
    response = s3.list_objects_v2(Bucket=S3_BUCKET, Prefix='uploads/')
    files = []
    if 'Contents' in response:
        for obj in response['Contents']:
            files.append(obj['Key'])
    return jsonify({'files': files})

# Download file
@app.route('/download', methods=['GET'])
def download_file():
    file_key = request.args.get('file_key')
    if not file_key:
        return jsonify({'error': 'Missing file_key parameter'}), 400

    try:
        s3_response = s3.get_object(Bucket=S3_BUCKET, Key=file_key)
        file_stream = s3_response['Body'].read()

        return send_file(
            io.BytesIO(file_stream),
            download_name=file_key.split('/')[-1],
            as_attachment=True
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Show file content (text files)
@app.route('/show', methods=['GET'])
def show_file_content():
    file_key = request.args.get('file_key')
    if not file_key:
        return jsonify({'error': 'Missing file_key parameter'}), 400

    try:
        s3_response = s3.get_object(Bucket=S3_BUCKET, Key=file_key)
        file_stream = s3_response['Body'].read()
        content = file_stream.decode('utf-8')  # Giả sử file text

        return jsonify({'file_key': file_key, 'content': content})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Trang index hiển thị danh sách file và nút Download/Show
@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>File List</title>
    </head>
    <body>
        <h1>File List</h1>
        <div id="file-list"></div>
        <pre id="file-content" style="white-space: pre-wrap; border:1px solid #ccc; padding:10px; margin-top:20px;"></pre>

        <script>
        async function fetchFiles() {
            const res = await fetch('/files');
            const data = await res.json();
            const fileListDiv = document.getElementById('file-list');
            fileListDiv.innerHTML = '';

            data.files.forEach(fileKey => {
                const div = document.createElement('div');
                div.style.marginBottom = '10px';

                const fileName = fileKey.split('/').pop();

                const span = document.createElement('span');
                span.textContent = fileName + ' ';

                // nút download
                const btnDownload = document.createElement('button');
                btnDownload.textContent = 'Download';
                btnDownload.onclick = () => {
                    window.location.href = `/download?file_key=${encodeURIComponent(fileKey)}`;
                };

                // nút show
                const btnShow = document.createElement('button');
                btnShow.textContent = 'Show';
                btnShow.onclick = async () => {
                    const resShow = await fetch(`/show?file_key=${encodeURIComponent(fileKey)}`);
                    if(resShow.ok) {
                        const dataShow = await resShow.json();
                        if(dataShow.content) {
                            document.getElementById('file-content').textContent = `Content of ${fileName}:\n\n` + dataShow.content;
                        } else {
                            document.getElementById('file-content').textContent = 'No content available or binary file.';
                        }
                    } else {
                        document.getElementById('file-content').textContent = 'Error fetching file content.';
                    }
                };

                div.appendChild(span);
                div.appendChild(btnDownload);
                div.appendChild(btnShow);

                fileListDiv.appendChild(div);
            });
        }

        fetchFiles();
        </script>
    </body>
    </html>
    '''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
