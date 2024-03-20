from flask import Flask, request, send_from_directory, jsonify, render_template_string, redirect, url_for
import os
from werkzeug.utils import secure_filename
import datetime
import urllib.parse

BASE_DIR = '/apps'
ALLOWED_EXTENSIONS = {'jmx', 'txt', 'pdf', 'exe', 'zip', 'tar', 'gz'}  # 可以根据需要添加更多允许的文件类型

app = Flask(__name__)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_files_and_dirs(path):
    files = []
    dirs = []
    for item in os.listdir(path):
        item_path = os.path.join(path, item)
        if os.path.isfile(item_path):
            size = os.path.getsize(item_path)
            files.append((item, size))
        else:
            dirs.append(item)
    return sorted(dirs), sorted(files, key=lambda x: x[0])

@app.route('/', defaults={'req_path': ''})
@app.route('/<path:req_path>')
def index(req_path):
    abs_path = os.path.join(BASE_DIR, req_path)

    # Return 404 if path doesn't exist
    if not os.path.exists(abs_path):
        return "404 Not Found", 404

    # Check if path is a file and serve
    if os.path.isfile(abs_path):
        return send_from_directory(os.path.dirname(abs_path), os.path.basename(abs_path))

    # Show directory contents
    dirs, files = get_files_and_dirs(abs_path)
    return render_template_string(HTML_TEMPLATE, files=files, dirs=dirs, current_path=req_path)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'message': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': 'No selected file'}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(BASE_DIR, filename)
        file.save(file_path)
        return redirect(url_for('index'))
    else:
        return jsonify({'message': 'File type not allowed'}), 400

@app.route('/download/<path:filename>')
def download_file(filename):
    # Make sure the filename is secure
    if '..' in filename or filename.startswith('/'):
        return "400 Bad Request", 400
    abs_file_path = os.path.join(BASE_DIR, filename)
    if os.path.exists(abs_file_path):
        return send_from_directory(directory=os.path.dirname(abs_file_path), filename=os.path.basename(abs_file_path), as_attachment=True)
    else:
        return jsonify({'message': 'File not found'}), 404

@app.route('/delete/<path:filename>')
def delete_file(filename):
    # Make sure the filename is secure
    if '..' in filename or filename.startswith('/'):
        return "400 Bad Request", 400
    abs_file_path = os.path.join(BASE_DIR, filename)
    if os.path.exists(abs_file_path):
        os.remove(abs_file_path)
        return redirect(url_for('index'))
    else:
        return jsonify({'message': 'File not found'}), 404

def format_size(size):
    """Format size to a more readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} PB"

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>File Management</title>
</head>
<body>
    <h2>Upload File</h2>
    <form method="post" action="/upload" enctype="multipart/form-data">
        <input type="file" name="file">
        <input type="submit" value="Upload">
    </form>
    <h2>Directories and Files</h2>
    <ul>
        {% for dir in dirs %}
        <li><a href="{{ request.path }}{{ dir }}">{{ dir }}</a></li>
        {% endfor %}
        {% for file, size in files %}
        <li>{{ file }}
            - {{ format_size(size) }}
            - <a href="/download/{{ request.path }}{{ file }}">Download</a>
            - <a href="/delete/{{ request.path }}{{ file }}" onclick="return confirm('Are you sure?');">Delete</a>
        </li>
        {% endfor %}
    </ul>
</body>
</html>
'''

app.jinja_env.globals.update(format_size=format_size)  # Add format_size function to Jinja environment

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=8000, debug=True)
