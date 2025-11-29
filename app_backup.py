from flask import Flask, request, render_template, redirect, url_for, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from pathlib import Path

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'photos'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
ITEMS = ['Yoga Mat', 'Binoculars', 'Fitness Band', 'Chime', 'Foam Roller']

# Ensure upload folder exists
Path(UPLOAD_FOLDER).mkdir(exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_item_photos(item_name):
    """Get all photos for a specific item, sorted newest first"""
    item_folder = os.path.join(UPLOAD_FOLDER, item_name.replace(' ', '-').lower())
    
    if not os.path.exists(item_folder):
        return []
    
    photos = []
    for filename in os.listdir(item_folder):
        if allowed_file(filename):
            filepath = os.path.join(item_folder, filename)
            # Get file modification time
            mtime = os.path.getmtime(filepath)
            photos.append({
                'filename': filename,
                'path': filepath,
                'timestamp': mtime,
                'date': datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
            })
    
    # Sort by timestamp, newest first
    photos.sort(key=lambda x: x['timestamp'], reverse=True)
    return photos

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        # Check if item was selected
        item = request.form.get('item')
        if not item or item not in ITEMS:
            return render_template('upload.html', items=ITEMS, error='Please select a valid item')
        
        # Check if file was uploaded
        if 'file' not in request.files:
            return render_template('upload.html', items=ITEMS, error='No file uploaded')
        
        file = request.files['file']
        if file.filename == '':
            return render_template('upload.html', items=ITEMS, error='No file selected')
        
        if file and allowed_file(file.filename):
            # Create folder for this item if it doesn't exist
            item_folder_name = item.replace(' ', '-').lower()
            item_folder = os.path.join(UPLOAD_FOLDER, item_folder_name)
            Path(item_folder).mkdir(parents=True, exist_ok=True)
            
            # Create unique filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
            original_filename = secure_filename(file.filename)
            filename = f"{timestamp}-{original_filename}"
            
            # Save file
            filepath = os.path.join(item_folder, filename)
            file.save(filepath)
            
            return render_template('success.html', item=item)
        else:
            return render_template('upload.html', items=ITEMS, error='Invalid file type. Please upload an image.')
    
    return render_template('upload.html', items=ITEMS, error=None)

@app.route('/gallery-select')
def gallery_select():
    # Get photo counts for each item
    item_counts = {}
    for item in ITEMS:
        photos = get_item_photos(item)
        item_counts[item] = len(photos)
    
    return render_template('gallery_select.html', items=ITEMS, item_counts=item_counts)

@app.route('/gallery/<item_name>')
def gallery(item_name):
    if item_name not in ITEMS:
        return redirect(url_for('gallery_select'))
    
    photos = get_item_photos(item_name)
    return render_template('gallery.html', item=item_name, photos=photos)

@app.route('/photos/<path:filename>')
def serve_photo(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'message': 'Equipment Tracker is running'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)