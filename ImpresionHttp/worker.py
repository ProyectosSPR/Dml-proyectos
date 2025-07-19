import sys
import time
import os

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))

DB_PATH = os.path.abspath(os.path.join(BASE_DIR, 'printjobs.sqlite3'))

# Configurar las rutas antes de importar app
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')

# Crear carpeta de uploads si no existe
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# El resto de los imports
from app import app, db, PrintJob, PrintingService, FileService
from datetime import datetime

CHECK_INTERVAL = 5  # segundos entre revisiones de la cola

printer = PrintingService()

print('Worker de impresión iniciado. Presiona Ctrl+C para detener.')
print(f'Base directory: {BASE_DIR}')
print(f'Database path: {DB_PATH}')

while True:
    try:
        with app.app_context():
            job = PrintJob.query.filter_by(status='pending').order_by(PrintJob.created_at).first()
            if job:
                print(f'Procesando trabajo {job.id}: {job.filename}')
                job.status = 'processing'
                db.session.commit()
                try:
                    ext = os.path.splitext(job.file_path)[1].lower()
                    if ext == '.pdf':
                        result = printer.print_pdf_as_image(job.printer_name, job.file_path, job.copies)
                    elif ext in ['.png', '.jpg', '.jpeg', '.bmp']:
                        result = printer.print_image(job.printer_name, job.file_path, job.copies)
                    else:
                        raise Exception('Tipo de archivo no soportado para impresión de etiquetas')
                    if result.get('success'):
                        job.status = 'completed'
                        job.completed_at = datetime.utcnow()
                        print(f'Trabajo {job.id} completado')
                    else:
                        job.status = 'failed'
                        job.error_message = result.get('error', 'Error en la impresión')
                        job.completed_at = datetime.utcnow()
                        print(f"Trabajo {job.id} falló: {result.get('error')}")
                except Exception as e:
                    job.status = 'failed'
                    job.error_message = str(e)
                    job.completed_at = datetime.utcnow()
                    print(f'Trabajo {job.id} falló: {e}')
                db.session.commit()
            else:
                time.sleep(CHECK_INTERVAL)
    except KeyboardInterrupt:
        print('Worker detenido por el usuario.')
        break
    except Exception as e:
        print(f'Error en el worker: {e}')
        time.sleep(CHECK_INTERVAL) 