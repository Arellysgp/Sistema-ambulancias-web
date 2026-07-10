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
    latitud       = db.Column(db.Float, nullable=True)
    longitud      = db.Column(db.Float, nullable=True)

    def __init__(self, nombre, email, password_hash, rol='operador', activo=True, telefono=None, foto_url=None, fecha_registro=None, latitud=None, longitud=None, **kwargs):
        self.nombre = nombre
        self.email = email
        self.password_hash = password_hash
        self.rol = rol
        self.activo = activo
        self.telefono = telefono
        self.foto_url = foto_url
        self.fecha_registro = fecha_registro
        self.latitud = latitud
        self.longitud = longitud
        for key, value in kwargs.items():
            setattr(self, key, value)