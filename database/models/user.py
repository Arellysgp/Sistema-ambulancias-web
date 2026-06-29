from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'usuarios'
    __table_args__ = {'schema': 'public'}
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    rol = db.Column(db.String(50), default='operador')
    activo        = db.Column(db.Boolean, default=True)
    # Roles válidos: 'operador', 'conductor'  (admin solo vía SQL)
    
    # Nuevas columnas (ya en Supabase gracias al ALTER TABLE)
    telefono      = db.Column(db.String(20), nullable=True)
    foto_url      = db.Column(db.Text, nullable=True)
    fecha_registro= db.Column(db.DateTime, nullable=True)