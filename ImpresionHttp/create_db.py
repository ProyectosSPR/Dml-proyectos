import sys
import os

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))

print(f"Base directory: {BASE_DIR}")
print(f"Current working directory: {os.getcwd()}")

# Configurar las rutas
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
DB_PATH = os.path.abspath(os.path.join(BASE_DIR, 'printjobs.sqlite3'))

print(f"Database path: {DB_PATH}")
print(f"Upload folder: {UPLOAD_FOLDER}")

# Crear carpetas
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Importar y crear la base de datos
from app import app, db

with app.app_context():
    db.create_all()
    print("Base de datos creada exitosamente!")
    
    # Verificar que la tabla existe
    from app import PrintJob
    count = PrintJob.query.count()
    print(f"Registros en la tabla print_job: {count}") 