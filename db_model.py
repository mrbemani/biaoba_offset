# use flask sql-alchemy to create a database model

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Camera(db.Model):
    __tablename__ = 'cameras'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    device_id = db.Column(db.Integer, unique=True, nullable=False)
    reference_image = db.Column(db.String(80), unique=True, nullable=False)
    markers = db.relationship('Marker', backref='camera', lazy=True)

    def __repr__(self):
        return '<Camera %r>' % self.name
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "device_id": self.device_id,
            "reference_image": self.reference_image,
            "markers": [marker.to_dict() for marker in self.markers]
        }
    

class Marker(db.Model):
    __tablename__ = 'markers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    camera_id = db.Column(db.Integer, db.ForeignKey('cameras.id'), nullable=False)
    x = db.Column(db.Integer, nullable=False)
    y = db.Column(db.Integer, nullable=False)
    width = db.Column(db.Integer, nullable=False)
    height = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return '<Marker %r>' % self.name
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "camera_id": self.camera_id,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height
        }