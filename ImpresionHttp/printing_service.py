import win32print
import win32api
import win32ui
import win32con
import tempfile
import os
import logging
from datetime import datetime
from typing import Dict, Any
from pdf2image import convert_from_path
from PIL import Image, ImageWin

class PrintingService:
    """Servicio para manejar impresión en Windows"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def print_image_direct(self, printer_name, image_path, copies=1):
        hprinter = win32print.OpenPrinter(printer_name)
        try:
            printer_info = win32print.GetPrinter(hprinter, 2)
            pdevmode = printer_info["pDevMode"]
            hdc = win32ui.CreateDC()
            hdc.CreatePrinterDC(printer_name)
            img = Image.open(image_path)
            if img.mode != "RGB":
                img = img.convert("RGB")
            printable_area = hdc.GetDeviceCaps(win32con.HORZRES), hdc.GetDeviceCaps(win32con.VERTRES)
            img_width, img_height = img.size

            # Calcular escala para mantener el aspecto
            scale = min(printable_area[0] / img_width, printable_area[1] / img_height)
            new_width = int(img_width * scale)
            new_height = int(img_height * scale)
            img = img.resize((new_width, new_height), Image.LANCZOS)

            # Centrar la imagen
            x = (printable_area[0] - new_width) // 2
            y = (printable_area[1] - new_height) // 2

            dib = ImageWin.Dib(img)
            for _ in range(copies):
                hdc.StartDoc(image_path)
                hdc.StartPage()
                dib.draw(hdc.GetHandleOutput(), (x, y, x + new_width, y + new_height))
                hdc.EndPage()
                hdc.EndDoc()
            hdc.DeleteDC()
        finally:
            win32print.ClosePrinter(hprinter)

    def print_pdf_as_image(self, printer_name: str, pdf_path: str, copies: int = 1) -> Dict[str, Any]:
        """Convierte un PDF a imagen y lo imprime en la impresora de etiquetas."""
        try:
            if not os.path.exists(pdf_path):
                print(f"Archivo no encontrado: {pdf_path}")
                return {
                    'success': False,
                    'error': f'Archivo no encontrado: {pdf_path}',
                    'timestamp': datetime.now().isoformat()
                }
            # Ruta absoluta de poppler
            poppler_path = r"C:\ImpresionHttp\poppler\Library\bin"
            if not os.path.exists(poppler_path):
                poppler_path = r"C:\ImpresionHttp\poppler\bin"
            print(f"Usando poppler_path: {poppler_path}")
            print(f"PDF a convertir: {pdf_path}")
            print(f"Existe PDF: {os.path.exists(pdf_path)}")
            pages = convert_from_path(pdf_path, dpi=203, poppler_path=poppler_path)
            for i in range(copies):
                for page in pages:
                    img = page.convert('RGB')
                    with tempfile.NamedTemporaryFile(suffix='.bmp', delete=False) as temp_img:
                        img.save(temp_img.name, 'BMP')
                        temp_file = temp_img.name
                    self.print_image_direct(printer_name, temp_file, 1)
                    os.unlink(temp_file)
            return {
                'success': True,
                'message': f'PDF convertido e impreso como imagen en {printer_name}',
                'file_path': pdf_path,
                'copies': copies,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error imprimiendo PDF como imagen {pdf_path} en {printer_name}: {e}")
            print(f"Error imprimiendo PDF como imagen {pdf_path} en {printer_name}: {e}")
            return {
                'success': False,
                'error': str(e),
                'printer': printer_name,
                'file_path': pdf_path,
                'timestamp': datetime.now().isoformat()
            }

    def print_image(self, printer_name: str, image_path: str, copies: int = 1) -> Dict[str, Any]:
        """Imprime una imagen en la impresora de etiquetas."""
        try:
            if not os.path.exists(image_path):
                return {
                    'success': False,
                    'error': f'Archivo no encontrado: {image_path}',
                    'timestamp': datetime.now().isoformat()
                }
            self.print_image_direct(printer_name, image_path, copies)
            return {
                'success': True,
                'message': f'Imagen impresa en {printer_name}',
                'file_path': image_path,
                'copies': copies,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error imprimiendo imagen {image_path} en {printer_name}: {e}")
            return {
                'success': False,
                'error': str(e),
                'printer': printer_name,
                'file_path': image_path,
                'timestamp': datetime.now().isoformat()
            } 

    def get_available_printers(self):
        printers = []
        for printer in win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL):
            printers.append({'name': printer[2]})
        return printers 