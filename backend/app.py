import os, sys
from flask import Flask
from dotenv import load_dotenv
from flask_cors import CORS

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

from database.models.user import db
from backend.emergencias.emergencia_routes import emergencias_bp
from backend.auth.auth_routes import auth_bp
from backend.admin.admin_routes import admin_bp
from backend.routes.reportes import reportes_bp   # ← ruta correcta en tu proyecto
from backend.routes.perfil   import perfil_bp     # ← ruta correcta en tu proyecto

app = Flask(__name__)
app.config['SECRET_KEY']                     = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI']        = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_COOKIE_SAMESITE']        = 'Lax'
app.config['SESSION_COOKIE_HTTPONLY']        = True

CORS(app, supports_credentials=True,
     origins=[
         'http://localhost:5173',
         'http://127.0.0.1:5173',
         'http://127.0.0.1:5501',   # ← agrega esta línea
         'http://localhost:5501',    # ← y esta
     ],
     allow_headers=['Content-Type', 'X-User-Id'],
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])


db.init_app(app)
app.register_blueprint(auth_bp,        url_prefix='/api')
app.register_blueprint(emergencias_bp, url_prefix='/api')
app.register_blueprint(admin_bp,       url_prefix='/api')
app.register_blueprint(reportes_bp)   # ya tienen /api en sus rutas internas
app.register_blueprint(perfil_bp)     # igual

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)