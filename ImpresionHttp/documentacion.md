# Documentación Técnica - Sistema de Impresión HTTP

Esta documentación explica **línea por línea** y con detalle el funcionamiento del sistema de impresión HTTP, para que puedas entender, modificar y mantener el código aunque no seas experto en Python.

---

## 1. Estructura General del Proyecto

- `app.py`: Servidor web Flask, API y portal de impresión.
- `worker.py`: Proceso que toma trabajos de la base de datos y los imprime.
- `printing_service.py`: Lógica de impresión y conversión de PDF a imagen.
- `models.py`: (si existe) Modelos de base de datos.
- `uploads/`: Carpeta donde se guardan los archivos subidos.
- `printjobs.sqlite3`: Base de datos SQLite.
- `poppler/`: Herramientas para convertir PDF a imagen.

---

## 2. Explicación de Código Clave

### 2.1. `app.py` (Servidor Flask)

#### Importaciones
```python
import sys, os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from datetime import datetime
from file_service import FileService
from printing_service import PrintingService
```
- **`import`**: Palabra clave para importar módulos en Python.
- **`from ... import ...`**: Importa funciones/clases específicas de un módulo.
- **`Flask`**: Framework web ligero para Python.
- **`SQLAlchemy`**: ORM para manejar bases de datos relacionales.

#### Configuración de rutas y base de datos
```python
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.abspath(os.path.join(BASE_DIR, 'printjobs.sqlite3'))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
```
- **`getattr(sys, 'frozen', False)`**: Detecta si el script está corriendo como ejecutable (PyInstaller).
- **`os.path.dirname(sys.executable)`**: Carpeta donde está el EXE.
- **`__file__`**: Nombre del archivo Python actual.
- **`os.path.join`**: Une partes de una ruta de forma segura.

#### Inicialización de Flask y SQLAlchemy
```python
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_PATH}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = 'super-secret-key'
db = SQLAlchemy(app)
```
- **`Flask(__name__)`**: Crea la app web.
- **`app.config[...]`**: Configura opciones de Flask.
- **`SQLAlchemy(app)`**: Inicializa la base de datos.

#### Creación de la base de datos
```python
with app.app_context():
    db.create_all()
```
- **`with app.app_context()`**: Contexto necesario para operaciones de base de datos en Flask.
- **`db.create_all()`**: Crea las tablas si no existen.

#### Modelo de trabajo de impresión
```python
class PrintJob(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(256), nullable=False)
    file_path = db.Column(db.String(512), nullable=False)
    printer_name = db.Column(db.String(128), nullable=False)
    copies = db.Column(db.Integer, default=1)
    status = db.Column(db.String(32), default='pending')
    error_message = db.Column(db.String(512))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
```
- **`class`**: Define una clase (objeto) en Python.
- **`db.Column`**: Define una columna de la tabla.
- **`primary_key=True`**: Clave primaria.
- **`default=...`**: Valor por defecto.

#### Rutas principales (ejemplo)
```python
@app.route('/')
def index():
    total_jobs = PrintJob.query.count()
    ...
    return render_template('dashboard.html', ...)
```
- **`@app.route`**: Decorador que define una URL en Flask.
- **`render_template`**: Renderiza una plantilla HTML.

#### Subida de archivos
```python
@app.route('/upload', methods=['GET', 'POST'])
def upload_page():
    if request.method == 'POST':
        file = request.files.get('file')
        ...
        file.save(file_path)
        ...
        db.session.add(job)
        db.session.commit()
        ...
```
- **`request.files.get('file')`**: Obtiene el archivo subido.
- **`file.save(file_path)`**: Guarda el archivo.
- **`db.session.add`/`commit`**: Guarda el trabajo en la base de datos.

---

### 2.2. `worker.py` (Procesador de trabajos)

- Importa la app y los modelos igual que `app.py`.
- Usa un bucle infinito para buscar trabajos pendientes:

```python
while True:
    with app.app_context():
        job = PrintJob.query.filter_by(status='pending').order_by(PrintJob.created_at).first()
        if job:
            ...
            # Llama a PrintingService para imprimir
            ...
        else:
            time.sleep(CHECK_INTERVAL)
```
- **`while True`**: Bucle infinito.
- **`filter_by`**: Filtra trabajos por estado.
- **`order_by`**: Ordena por fecha de creación.
- **`time.sleep`**: Espera unos segundos antes de volver a revisar.

---

### 2.3. `printing_service.py` (Lógica de impresión)

#### Importaciones
```python
import win32print, win32ui, win32con
from pdf2image import convert_from_path
from PIL import Image, ImageWin
```
- **`win32print`**: Acceso a impresoras en Windows.
- **`pdf2image`**: Convierte PDF a imágenes.
- **`PIL`**: Manipulación de imágenes.

#### Conversión de PDF a imagen
```python
def print_pdf_as_image(self, printer_name, pdf_path, copies=1):
    ...
    pages = convert_from_path(pdf_path, dpi=203, poppler_path=poppler_path)
    for i in range(copies):
        for page in pages:
            img = page.convert('RGB')
            ...
            self.print_image_direct(printer_name, temp_file, 1)
            ...
```
- **`convert_from_path`**: Convierte cada página del PDF a una imagen.
- **`dpi=203`**: Resolución típica de impresoras de etiquetas.
- **`poppler_path`**: Ruta a los ejecutables de Poppler.

#### Impresión de imagen (ajuste proporcional)
```python
def print_image_direct(self, printer_name, image_path, copies=1):
    ...
    printable_area = hdc.GetDeviceCaps(win32con.HORZRES), hdc.GetDeviceCaps(win32con.VERTRES)
    img_width, img_height = img.size
    scale = min(printable_area[0] / img_width, printable_area[1] / img_height)
    new_width = int(img_width * scale)
    new_height = int(img_height * scale)
    img = img.resize((new_width, new_height), Image.LANCZOS)
    x = (printable_area[0] - new_width) // 2
    y = (printable_area[1] - new_height) // 2
    dib = ImageWin.Dib(img)
    ...
    dib.draw(hdc.GetHandleOutput(), (x, y, x + new_width, y + new_height))
    ...
```
- **`GetDeviceCaps`**: Obtiene el tamaño imprimible de la impresora.
- **`scale = min(...)`**: Escala la imagen para que quepa sin distorsionar.
- **`Image.LANCZOS`**: Algoritmo de alta calidad para redimensionar.
- **`dib.draw(...)`**: Dibuja la imagen en la página de impresión.

---

## 3. Conceptos de Python usados

- **Clases y métodos**: `class Nombre: ... def metodo(self, ...): ...`
- **Decoradores**: `@app.route` para asociar funciones a rutas web.
- **Contextos**: `with ...:` para manejar recursos (archivos, base de datos).
- **Listas y diccionarios**: `[1, 2, 3]`, `{'clave': valor}`
- **F-strings**: `f"Texto {variable}"` para formatear cadenas.
- **Manejo de errores**: `try: ... except Exception as e: ...`

---

## 4. ¿De dónde salen los datos?
- **Trabajos de impresión**: Se crean al subir archivos vía web o API.
- **Base de datos**: Todos los trabajos y su estado se guardan en `printjobs.sqlite3`.
- **Configuración de impresora**: Se obtiene del driver de Windows en tiempo real.

---

## 5. ¿Por qué se hace así?
- **Compatibilidad**: Usar rutas absolutas y PyInstaller permite que funcione en cualquier PC sin instalar Python.
- **Escalado proporcional**: Evita distorsión y aprovecha el área de impresión de cada impresora.
- **Separación de procesos**: El worker permite que la web sea rápida y la impresión no bloquee la interfaz.

---

## 6. Recursos útiles
- [Documentación de Flask](https://flask.palletsprojects.com/)
- [Documentación de SQLAlchemy](https://docs.sqlalchemy.org/)
- [Documentación de PyWin32](https://github.com/mhammond/pywin32)
- [Documentación de Pillow (PIL)](https://pillow.readthedocs.io/)
- [pdf2image](https://github.com/Belval/pdf2image)

---

¿Quieres que documente alguna función o archivo en particular con más detalle? ¿O necesitas ejemplos de cómo modificar alguna parte del flujo? 