from flask import Flask, request, render_template, redirect, url_for, jsonify, send_from_directory, session
from werkzeug.utils import secure_filename
from pymongo import MongoClient
from dotenv import load_dotenv
import os
from datetime import datetime
from pathlib import Path
from bson import ObjectId

# Load environment variables
load_dotenv()

# MongoDB connection
client = MongoClient(os.getenv('MONGODB_URI'), tlsAllowInvalidCertificates=True)
db = client['equipment_tracker']
employees_collection = db['employees']
uploads_collection = db['uploads']

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-change-this-in-production')

# Configuration
UPLOAD_FOLDER = 'photos'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
ITEMS = ['Yoga Mat', 'Binoculars', 'Fitness Band', 'Chime', 'Foam Roller']

# Ensure upload folder exists
Path(UPLOAD_FOLDER).mkdir(exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_current_user():
    """Get currently logged in employee"""
    employee_id = session.get('employee_id')
    if employee_id:
        try:
            return employees_collection.find_one({"_id": ObjectId(employee_id)})
        except:
            return None
    return None

def login_required(f):
    """Decorator to require login for routes"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not get_current_user():
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        pin = request.form.get('pin')
        employee = employees_collection.find_one({"pin": pin})
        
        if employee:
            session['employee_id'] = str(employee['_id'])
            session['employee_name'] = employee['name']
            return redirect(url_for('home'))
        else:
            return render_template('login.html', error='Invalid PIN. Please try again.')
    
    # If already logged in, go to home
    if get_current_user():
        return redirect(url_for('home'))
    
    return render_template('login.html', error=None)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def home():
    user = get_current_user()
    return render_template('home.html', user=user)

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    user = get_current_user()
    
    if request.method == 'POST':
        # Check if item was selected
        item = request.form.get('item')
        condition = request.form.get('condition')
        
        if not item or item not in ITEMS:
            return render_template('upload.html', items=ITEMS, user=user, error='Please select a valid item')
        
        if not condition or condition not in ['Clear', 'Damaged']:
            return render_template('upload.html', items=ITEMS, user=user, error='Please select a condition')
        
        # Check if file was uploaded
        if 'file' not in request.files:
            return render_template('upload.html', items=ITEMS, user=user, error='No file uploaded')
        
        file = request.files['file']
        if file.filename == '':
            return render_template('upload.html', items=ITEMS, user=user, error='No file selected')
        
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
            
            # Save metadata to MongoDB
            upload_doc = {
                "item": item,
                "condition": condition,
                "employee_name": user['name'],
                "employee_id": str(user['_id']),
                "filename": filename,
                "filepath": filepath,
                "uploaded_at": datetime.now()
            }
            uploads_collection.insert_one(upload_doc)
            
            return render_template('success.html', item=item, user=user)
        else:
            return render_template('upload.html', items=ITEMS, user=user, error='Invalid file type. Please upload an image.')
    
    return render_template('upload.html', items=ITEMS, user=user, error=None)

@app.route('/gallery-select')
@login_required
def gallery_select():
    user = get_current_user()
    
    # Get photo counts for each item from MongoDB
    item_counts = {}
    for item in ITEMS:
        count = uploads_collection.count_documents({"item": item})
        item_counts[item] = count
    
    return render_template('gallery_select.html', items=ITEMS, item_counts=item_counts, user=user)

@app.route('/gallery/<item_name>')
@login_required
def gallery(item_name):
    user = get_current_user()
    
    if item_name not in ITEMS:
        return redirect(url_for('gallery_select'))
    
    # Get photos from MongoDB instead of file system
    photos = list(uploads_collection.find({"item": item_name}).sort("uploaded_at", -1))
    
    # Format for template
    formatted_photos = []
    for photo in photos:
        formatted_photos.append({
            'filename': photo['filename'],
            'path': photo['filepath'],
            'date': photo['uploaded_at'].strftime('%Y-%m-%d %H:%M:%S'),
            'employee_name': photo['employee_name'],
            'condition': photo['condition']
        })
    
    return render_template('gallery.html', item=item_name, photos=formatted_photos, user=user)

@app.route('/photos/<path:filename>')
@login_required
def serve_photo(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'message': 'Equipment Tracker is running'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4321, debug=True)