import os
from flask import Flask, request, send_from_directory, render_template_string, redirect, url_for, flash
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = '/apps'  # 请替换为您的上传文件夹路径
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = "secret key"  # Required for session management and flash messages

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def index(path):
    abs_path = os.path.join(UPLOAD_FOLDER, path)
    if not os.path.exists(abs_path):
        return "Path does not exist", 404

    if os.path.isdir(abs_path):
        raw_items = os.listdir(abs_path)
        dirs = sorted([item for item in raw_items if os.path.isdir(os.path.join(abs_path, item))])
        files = sorted([item for item in raw_items if os.path.isfile(os.path.join(abs_path, item))])
        items = dirs + files

        return render_template_string('''
<!doctype html>
<title>Files and Directories</title>
{% if path %}
<h2>Contents of {{ path }}</h2>
{% else %}
<h2>Root Directory</h2>
{% endif %}
<ul>
    {% for item in items %}
        {% set item_path = path + '/' + item if path else item %}
        {% if os.path.isdir(os.path.join(UPLOAD_FOLDER, item_path)) %}
            <li><a href="{{ url_for('index', path=item_path) }}">{{ item }}/</a></li>
        {% else %}
            {% set file_size = os.path.getsize(os.path.join(UPLOAD_FOLDER, item_path)) // 1024 %}
            <li>{{ item }} ({{ file_size }} KB) <a href="{{ url_for('download_file', path=item_path) }}">Download</a></li>
        {% endif %}
    {% endfor %}
</ul>
<a href="{{ url_for('upload_file', path=path) }}">Upload new File</a>
{% if path %}<a href="{{ url_for('index', path='/'.join(path.split('/')[:-1])) }}">Back</a>{% endif %}
''', items=items, path=path, os=os, UPLOAD_FOLDER=UPLOAD_FOLDER)
    else:
        return "Not a directory", 400

@app.route('/download/<path:path>')
def download_file(path):
    directory = os.path.join(UPLOAD_FOLDER, os.path.dirname(path))
    filename = os.path.basename(path)
    return send_from_directory(directory=directory, path=filename, as_attachment=True)

@app.route('/upload/', defaults={'path': ''})
@app.route('/upload/<path:path>', methods=['GET', 'POST'])
def upload_file(path):
    if path == '':
        upload_path = UPLOAD_FOLDER
    else:
        upload_path = os.path.join(UPLOAD_FOLDER, path)
    if not os.path.exists(upload_path):
        os.makedirs(upload_path)
    
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(upload_path, filename))
            return redirect(url_for('index', path=path))
    return render_template_string('''
<!doctype html>
<title>Upload new File</title>
<h1>Upload new File</h1>
<form method=post enctype=multipart/form-data>
  <input type=file name=file>
  <input type=submit value=Upload>
</form>
<a href="{{ url_for('index', path=path) }}">Back</a>
''', path=path)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
