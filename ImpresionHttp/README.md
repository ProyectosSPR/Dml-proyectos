# Sistema de Impresión HTTP - Instalación y Cloudflare Tunnel

## 1. Instalación de ImpresionHttp

**IMPORTANTE:**
- Instala el sistema SIEMPRE en la ruta `C:\ImpresionHttp`.
- No cambies la ruta de instalación, ya que el sistema y Poppler están configurados para funcionar solo ahí.

### Pasos:
1. Ejecuta el instalador `ImpresionHttp-Setup.exe`.
2. Cuando te pregunte la carpeta de instalación, asegúrate de que sea:
   ```
   C:\ImpresionHttp
   ```
3. Finaliza la instalación.

**No necesitas instalar Python ni ninguna dependencia adicional.**

---

## 2. Instalación de Cloudflared (Cloudflare Tunnel)

1. Descarga el instalador de Cloudflared para Windows desde:
   [https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.msi])

2. Ejecuta el instalador y sigue los pasos para instalar.

3. Abre **Command Prompt (CMD) como Administrador**:
   - Pulsa `Win + S`, escribe `cmd`, haz clic derecho y selecciona **"Ejecutar como administrador"**.

4. Ejecuta el siguiente comando (reemplaza el token por el tuyo):
   ```sh
   cloudflared.exe service install eyJhIjoiMzRhZDRkMjRlYjIyMDVjMGEyZWNhMjcwOTZlYzliY2UiLCJ0IjoiY2I0NzFiMTMtMTk2YS00M2E3LTkxOTEtNGJhMGMzODg5MmRjIiwicyI6IllUQXpaamMyTlRZdFptUmxOQzAwT1dRNUxUa3laVEl0TnpWaVpEaGxPVGd4TmpVMCJ9
   ```

---

## 3. Notas importantes

- **No necesitas instalar Python**: El sistema ya incluye todo lo necesario.
- **No cambies la carpeta de instalación**: Debe ser `C:\ImpresionHttp` para que funcione correctamente.
- **No es necesario modificar el PATH**: El sistema ya está configurado para encontrar Poppler y sus dependencias.
- **Cloudflared** solo requiere instalarse y ejecutar el comando de tu túnel.

---

## 4. Desinstalación

- Para desinstalar ImpresionHttp, usa "Agregar o quitar programas" en Windows.
- Para desinstalar Cloudflared, ve a "Agregar o quitar programas" y busca "Cloudflared".

---

## 5. Soporte

Si tienes problemas, asegúrate de:
- Haber instalado todo en `C:\ImpresionHttp`.
- Haber ejecutado el comando de Cloudflared como administrador.
- Que tu impresora esté correctamente instalada en Windows.

Si el problema persiste, contacta al soporte técnico con una captura de pantalla del error. 


Se debe de configurar la resolucion a 401 x 201 mm