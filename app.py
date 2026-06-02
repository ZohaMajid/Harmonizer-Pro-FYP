import os
import uuid
from flask import Flask, render_template, request, redirect, url_for, flash
from models import db, Project, ResultImage
# FIXED 1: Added upscale_image_hd to the imports
from processor import process_harmonization, upscale_to_hd

app = Flask(__name__)
app.secret_key = "super_secret_key_fyp" # Required for flashing messages

# --- 1. WINDOWS 10 PATH CONFIGURATION ---
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'instance', 'harmonizer.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024 #100MB length limit

# Create the upload and instance folders automatically if they don't exist
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])
if not os.path.exists(os.path.join(basedir, 'instance')):
    os.makedirs(os.path.join(basedir, 'instance'))

# Initialize the database with the Flask app
db.init_app(app)

# --- 2. ROUTES ---

@app.route('/')
def index():
    """Main page for uploading images."""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    if 'sources' not in request.files or 'target' not in request.files:
        flash("Missing files!")
        return redirect(request.url)
    
    # 1. Get files (Note: 'sources' is now a list)
    source_files = request.files.getlist('sources')
    target_file = request.files['target']

    # CHECKBOXES: Get SMART mode and HD mode
    use_smart_mode = request.form.get('smart_mode') == 'true'
    # FIXED 2: Actually capture the HD mode toggle from the frontend
    hd_mode = request.form.get('hd_mode') == 'true'

    if target_file.filename == '':
        flash("No Theme Selected")
        return redirect(request.url)

    # 2. Save the single Target Style
    t_ext = os.path.splitext(target_file.filename)[1]
    target_filename = f"theme_{uuid.uuid4().hex}{t_ext}"
    target_path = os.path.join(app.config['UPLOAD_FOLDER'], target_filename)
    target_file.save(target_path)

    # 3. Save all Source Images
    saved_source_paths = []
    saved_source_names = []
    for source in source_files:
        if source.filename != '':
            s_ext = os.path.splitext(source.filename)[1]
            s_name = f"source_{uuid.uuid4().hex}{s_ext}"
            s_path = os.path.join(app.config['UPLOAD_FOLDER'], s_name)
            source.save(s_path)
            saved_source_paths.append(s_path)
            saved_source_names.append(s_name)
        
    try:
        output_paths = process_harmonization(
            saved_source_paths,
            target_path, 
            app.config['UPLOAD_FOLDER'],
            smart_mode=use_smart_mode
        )
    except Exception as e:
        flash(f"Error during processing: {str(e)}")
        return redirect(url_for('index'))
    
    # FIXED 3: Loop through the actual output paths to upscale them if requested
    if hd_mode:
        for out_path in output_paths:
            # We upscale the result of the harmonization to get an HD version
            # This overwrites the previous result with the 4x upscaled version
            upscale_to_hd(out_path, out_path)

    # 5. Save to Database
    new_project = Project(name=f"Batch_{uuid.uuid4().hex[:6]}")
    db.session.add(new_project)
    db.session.commit()

    for i in range(len(output_paths)):
        new_result = ResultImage(
            project_id=new_project.id,
            source_path=saved_source_names[i], # Unique source for each result
            target_path=target_filename,       # Same target for all
            output_path=os.path.basename(output_paths[i])
        )
        db.session.add(new_result)
    
    try:
        db.session.commit()
        print("Database committed successfully...")
    except Exception as e:
        db.session.rollback()
        print(f"Database error: {e}")
        flash("Error saving to database..")
        return redirect(url_for('index'))
        
    return redirect(url_for('results'))


@app.route('/results')
def results():
    """Fetches latest results from the database to display in the gallery."""
    # FIXED 4: Group results by Project so the frontend separate section logic works
    all_projects = Project.query.order_by(Project.created_at.desc()).all()
    
    if not all_projects:
        flash("No results found. Please upload images..")
        return redirect(url_for('index'))
    
    return render_template('results.html', projects=all_projects)

@app.route('/docs')
def documentation():
    return render_template('docs.html')

if __name__ == '__main__':
    # FIXED 5: Added app context to ensure tables exist
    with app.app_context():
        db.create_all()
    app.run(debug=True)

