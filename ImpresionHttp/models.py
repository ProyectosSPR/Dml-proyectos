from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import JSON

db = SQLAlchemy()

class Printer(db.Model):
    """Modelo para impresoras configuradas"""
    __tablename__ = 'printers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    printer_type = db.Column(db.String(50), default='label')  # label, receipt, etc.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relación con trabajos de impresión
    print_jobs = db.relationship('PrintJob', backref='printer', lazy=True)
    
    def __repr__(self):
        return f'<Printer {self.name}>'

class PrintJob(db.Model):
    """Modelo para trabajos de impresión"""
    __tablename__ = 'print_jobs'
    
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.String(100), unique=True, nullable=False)
    printer_id = db.Column(db.Integer, db.ForeignKey('printers.id'), nullable=False)
    
    # Datos de impresión
    content = db.Column(db.Text, nullable=False)
    print_data = db.Column(JSON)  # Datos estructurados para la impresión
    copies = db.Column(db.Integer, default=1)
    
    # Estado del trabajo
    status = db.Column(db.String(20), default='pending')  # pending, printing, completed, failed, cancelled
    priority = db.Column(db.Integer, default=1)  # 1=low, 2=normal, 3=high, 4=urgent
    
    # Información de seguimiento
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    
    # Información de error
    error_message = db.Column(db.Text)
    retry_count = db.Column(db.Integer, default=0)
    max_retries = db.Column(db.Integer, default=3)
    
    # Información de la solicitud HTTP
    request_ip = db.Column(db.String(45))
    request_user_agent = db.Column(db.String(500))
    request_data = db.Column(JSON)
    
    def __repr__(self):
        return f'<PrintJob {self.job_id}>'
    
    def to_dict(self):
        """Convertir a diccionario para API"""
        return {
            'id': self.id,
            'job_id': self.job_id,
            'printer_name': self.printer.name if self.printer else None,
            'content': self.content,
            'status': self.status,
            'priority': self.priority,
            'copies': self.copies,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'error_message': self.error_message,
            'retry_count': self.retry_count
        }

class PrintJobLog(db.Model):
    """Modelo para logs de trabajos de impresión"""
    __tablename__ = 'print_job_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    print_job_id = db.Column(db.Integer, db.ForeignKey('print_jobs.id'), nullable=False)
    
    # Información del log
    level = db.Column(db.String(20), default='info')  # info, warning, error, debug
    message = db.Column(db.Text, nullable=False)
    details = db.Column(JSON)
    
    # Timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<PrintJobLog {self.id}>'

class PrinterConfig(db.Model):
    """Modelo para configuraciones de impresoras"""
    __tablename__ = 'printer_configs'
    
    id = db.Column(db.Integer, primary_key=True)
    printer_id = db.Column(db.Integer, db.ForeignKey('printers.id'), nullable=False)
    
    # Configuraciones
    config_key = db.Column(db.String(100), nullable=False)
    config_value = db.Column(db.Text)
    config_type = db.Column(db.String(20), default='string')  # string, int, float, bool, json
    
    # Timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Índice único para evitar duplicados
    __table_args__ = (db.UniqueConstraint('printer_id', 'config_key', name='_printer_config_uc'),)
    
    def __repr__(self):
        return f'<PrinterConfig {self.printer_id}:{self.config_key}>' 