from database.models.user import db
from datetime import datetime, timezone

class Emergencia(db.Model):
    __tablename__ = 'emergencia'
    __table_args__ = {'schema': 'public'}
    
    id              = db.Column(db.Integer, primary_key=True)
    nombre_paciente = db.Column(db.String(100), nullable=False)
    edad            = db.Column(db.Integer, nullable=False)
    descripcion     = db.Column(db.Text, nullable=False)
    direccion       = db.Column(db.String(200), nullable=False)
    distrito        = db.Column(db.String(100), nullable=True)
    provincia       = db.Column(db.String(100), nullable=True)
    latitud         = db.Column(db.Float, nullable=True)
    longitud        = db.Column(db.Float, nullable=True)
    prioridad       = db.Column(db.Integer, nullable=False)
    estado          = db.Column(db.String(20), default='pendiente')
    fecha_registro  = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    conductor_id    = db.Column(db.Integer, db.ForeignKey('public.usuarios.id'), nullable=True)  # ← nueva
    conductor       = db.relationship('User', backref='emergencias', lazy=True)                  # ← nueva