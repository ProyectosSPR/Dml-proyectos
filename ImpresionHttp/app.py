import sys
import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from datetime import datetime
from file_service import FileService
from printing_service import PrintingService

# Configuración
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))

DB_PATH = os.path.abspath(os.path.join(BASE_DIR, 'printjobs.sqlite3'))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_PATH}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = 'super-secret-key'

db = SQLAlchemy(app)

# Crear la base de datos y las tablas siempre que se inicie la app
with app.app_context():
    db.create_all()

# Modelos
class PrintJob(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(256), nullable=False)
    file_path = db.Column(db.String(512), nullable=False)
    printer_name = db.Column(db.String(128), nullable=False)
    copies = db.Column(db.Integer, default=1)
    status = db.Column(db.String(32), default='pending')  # pending, processing, completed, failed
    error_message = db.Column(db.String(512))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)

# Crear carpeta de uploads si no existe
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Rutas Web
@app.route('/')
def index():
    total_jobs = PrintJob.query.count()
    pending_jobs = PrintJob.query.filter_by(status='pending').count()
    completed_jobs = PrintJob.query.filter_by(status='completed').count()
    failed_jobs = PrintJob.query.filter_by(status='failed').count()
    recent_jobs = PrintJob.query.order_by(PrintJob.created_at.desc()).limit(5).all()
    return render_template('dashboard.html',
        total_printers=1,  # Solo una impresora local
        total_jobs=total_jobs,
        pending_jobs=pending_jobs,
        completed_jobs=completed_jobs,
        failed_jobs=failed_jobs,
        recent_jobs=recent_jobs,
        printers=[{'name': 'Impresora Local', 'is_default': True, 'description': 'Impresora configurada en Windows'}]
    )

@app.route('/jobs')
def jobs():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    status_filter = request.args.get('status')
    query = PrintJob.query

    if status_filter:
        query = query.filter_by(status=status_filter)

    jobs = query.order_by(PrintJob.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return render_template('jobs.html', jobs=jobs, status_filter=status_filter)

@app.route('/upload', methods=['GET', 'POST'])
def upload_page():
    if request.method == 'POST':
        file = request.files.get('file')
        if not file or file.filename == '':
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'error': 'No se seleccionó archivo'}), 400
            flash('No se seleccionó archivo', 'error')
            return redirect(request.url)
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        is_valid, file_type, mime_type = FileService.validate_file(file_path)
        if not is_valid:
            os.remove(file_path)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'error': file_type}), 400
            flash(file_type, 'error')
            return redirect(request.url)
        printer_name = request.form.get('printer_name', 'Impresora Local')
        copies = int(request.form.get('copies', 1))
        job = PrintJob(filename=filename, file_path=file_path, printer_name=printer_name, copies=copies)
        db.session.add(job)
        db.session.commit()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'job_id': job.id, 'message': 'Trabajo de impresión agregado a la cola'})
        flash('Trabajo de impresión agregado a la cola', 'success')
        return redirect(url_for('jobs'))
    printers = PrintingService().get_available_printers()
    return render_template('upload.html', printers=printers)

@app.route('/logs')
def logs():
    failed_jobs = PrintJob.query.filter_by(status='failed').order_by(PrintJob.created_at.desc()).limit(50).all()
    return render_template('logs.html', failed_jobs=failed_jobs)

# API HTTP
@app.route('/api/print', methods=['POST'])
def api_print():
    file = request.files.get('file')
    if not file or file.filename == '':
        return jsonify({'error': 'No file provided'}), 400
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)
    is_valid, file_type, mime_type = FileService.validate_file(file_path)
    if not is_valid:
        os.remove(file_path)
        return jsonify({'error': file_type}), 400
    printer_name = request.form.get('printer', 'Impresora Local')
    copies = int(request.form.get('copies', 1))
    job = PrintJob(filename=filename, file_path=file_path, printer_name=printer_name, copies=copies)
    db.session.add(job)
    db.session.commit()
    return jsonify({'success': True, 'job_id': job.id, 'message': 'Print job queued successfully'})

@app.route('/api/jobs/<int:job_id>')
def api_job_status(job_id):
    job = PrintJob.query.get_or_404(job_id)
    return jsonify({
        'id': job.id,
        'status': job.status,
        'filename': job.filename,
        'printer_name': job.printer_name,
        'copies': job.copies,
        'created_at': job.created_at.isoformat(),
        'completed_at': job.completed_at.isoformat() if job.completed_at else None,
        'error_message': job.error_message
    })

@app.route('/api/retry/<int:job_id>', methods=['POST'])
def api_retry_job(job_id):
    job = PrintJob.query.get_or_404(job_id)
    if job.status != 'failed':
        return jsonify({'error': 'Job is not in failed status'}), 400
    job.status = 'pending'
    job.error_message = None
    job.completed_at = None
    db.session.commit()
    return jsonify({'success': True, 'message': 'Job set to pending'})

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 