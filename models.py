from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Initialize the database object
db = SQLAlchemy()

class Project(db.Model):
    """A Project groups one source image with multiple results."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship: One Project can have many ResultImages
    results = db.relationship('ResultImage', backref='project', lazy=True)

class ResultImage(db.Model):
    """Stores paths to the final harmonized image."""
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    
    source_path = db.Column(db.String(255), nullable=False) # Path to original
    target_path = db.Column(db.String(255), nullable=False) # Path to style image
    output_path = db.Column(db.String(255), nullable=False) # Path to result
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)