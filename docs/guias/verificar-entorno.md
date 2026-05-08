# Guía de verificación de configuración SAP Automation

Esta guía resume las verificaciones realizadas para confirmar que el sistema de automatización SAP está correctamente configurado en Windows con Python, SAP GUI y SAP GUI Scripting.

## 1. Verificar estructura de configuración

Desde la raíz del proyecto:

```powershell
dir config
```

Debe existir al menos:

```text
config/settings.yaml
config/secrets.yaml
```

---

## 2. Validar `settings.yaml`

Ejecutar:

```powershell
python -c "import yaml; print(yaml.safe_load(open('config/settings.yaml', encoding='utf-8')))"
```

Resultado esperado:

- El archivo se lee sin errores.
- Se muestran las secciones principales, por ejemplo:

```yaml
sap:
  connection_mode: credentials
  connection_string: SAP IDI ECO FIN
  transaction_code: /nZTSD_FACTURACION
```

Nota crítica: si la guía menciona parámetros como `login_wait` o `export_wait`, pero el archivo real contiene otros como `long_wait` o `max_retries`, no es necesariamente un error. Lo importante es que esos nombres coincidan con lo que espera el código.

---

## 3. Validar `secrets.yaml` sin mostrar la contraseña

Ejecutar:

```powershell
python -c "import yaml; d=yaml.safe_load(open('config/secrets.yaml', encoding='utf-8')); d['sap_credentials']['password']='***'; print(d)"
```

Resultado esperado:

```text
{'sap_credentials': {'username': '...', 'password': '***', 'client': '300', 'system_id': '...', 'language': 'CA'}}
```

Esto confirma que el archivo existe, es YAML válido y tiene la estructura esperada.

---

## 4. Confirmar que `secrets.yaml` está excluido de Git

Ejecutar:

```powershell
git check-ignore -v config/secrets.yaml
```

Resultado esperado:

- Debe mostrar la regla de `.gitignore` que excluye `config/secrets.yaml`.

Si no devuelve nada, el archivo podría estar en riesgo de ser versionado.

---

## 5. Verificar el gestor de credenciales

Ejecutar:

```powershell
python -m src.utils.credential_manager get
```

Resultado esperado:

- Debe mostrar las credenciales cargadas.
- La contraseña debe aparecer oculta o enmascarada.

---

## 6. Verificar que el paquete `src` se puede importar

Ejecutar:

```powershell
python -c "import src; print('src importado correctamente')"
```

Resultado esperado:

```text
src importado correctamente
```

---

## 7. Identificar la ruta real de `SAPConnection`

Si una guía indica una ruta que falla, por ejemplo:

```python
from src.sap.connection import SAPConnection
```

y aparece un error como:

```text
ModuleNotFoundError: No module named 'src.sap'
```

buscar la ubicación real con:

```powershell
Get-ChildItem -Recurse src -Filter *.py | Select-String -Pattern "class SAP|SAPConnection|connect|connection"
```

En este proyecto, la ruta correcta es:

```python
from src.core.sap_connection import SAPConnection
```

---

## 8. Verificar importación de `SAPConnection`

Ejecutar:

```powershell
python -c "from src.core.sap_connection import SAPConnection; print('SAPConnection importado correctamente')"
```

Resultado esperado:

```text
SAPConnection importado correctamente
```

---

## 9. Verificar disponibilidad de `win32com`

Ejecutar:

```powershell
python -c "import win32com.client; print('win32com disponible')"
```

Resultado esperado:

```text
win32com disponible
```

Si falla, probablemente falta instalar `pywin32`:

```powershell
pip install pywin32
```

---

## 10. Probar conexión SAP con credenciales

Ejecutar:

```powershell
python -c "import yaml; from src.core.sap_connection import SAPConnection; cfg=yaml.safe_load(open('config/settings.yaml', encoding='utf-8')); sec=yaml.safe_load(open('config/secrets.yaml', encoding='utf-8')); sap=cfg['sap']; creds=sec['sap_credentials']; conn=SAPConnection(connection_mode=sap['connection_mode'], connection_string=sap['connection_string'], credentials=creds); session=conn.connect(); print('Conectado a SAP:', session.Info.SystemName, session.Info.Client)"
```

Resultado esperado:

```text
Conectado a SAP: ... 300
```

Importante: si se agrega `conn.disconnect()` al final, la sesión se cerrará inmediatamente después de abrirse. Eso es normal.

---

## 11. Desactivar notificaciones de SAP GUI Scripting

Durante la primera prueba pueden aparecer avisos como:

```text
Un script intenta acceder a SAP GUI
```

o:

```text
Un script intenta abrir una conexión
```

Para desactivarlos:

1. Abrir **SAP Logon**.
2. Hacer clic en el icono de la esquina superior izquierda de la ventana.
3. Entrar en:

```text
Opciones
```

4. En el panel izquierdo, abrir:

```text
Accessibilitat i scripting
```

5. Entrar en:

```text
Suport scripting
```

6. Dejar marcada esta opción:

```text
Activar suport scripting
```

7. Desmarcar estas dos opciones:

```text
Notificar si un script es vincula a un SAP GUI
Notificar quan un script obri una connexió
```

8. Pulsar:

```text
D’acord
```

Resultado esperado:

- SAP GUI Scripting sigue activo.
- Python puede conectarse a SAP.
- Ya no aparecen alertas que bloqueen la automatización.

---

## 12. Probar conexión después de desactivar notificaciones

Repetir:

```powershell
python -c "import yaml; from src.core.sap_connection import SAPConnection; cfg=yaml.safe_load(open('config/settings.yaml', encoding='utf-8')); sec=yaml.safe_load(open('config/secrets.yaml', encoding='utf-8')); sap=cfg['sap']; creds=sec['sap_credentials']; conn=SAPConnection(connection_mode=sap['connection_mode'], connection_string=sap['connection_string'], credentials=creds); session=conn.connect(); print('Conectado a SAP:', session.Info.SystemName, session.Info.Client)"
```

Resultado esperado:

- SAP abre sesión automáticamente.
- No aparecen avisos de scripting.
- La sesión queda abierta.

---

## 13. Verificar transacción configurada

Ejecutar:

```powershell
python -c "import yaml; cfg=yaml.safe_load(open('config/settings.yaml', encoding='utf-8')); print(cfg['sap'].get('transaction_code'))"
```

Resultado esperado:

```text
/nZTSD_FACTURACION
```

---

## 14. Probar apertura de la transacción desde Python

Con SAP ya abierto, ejecutar:

```powershell
python -c "import win32com.client; SapGuiAuto=win32com.client.GetObject('SAPGUI'); app=SapGuiAuto.GetScriptingEngine; conn=app.Children(0); session=conn.Children(0); session.StartTransaction('ZTSD_FACTURACION'); print('Transacción abierta:', session.Info.Transaction)"
```

Resultado esperado:

```text
Transacción abierta: ZTSD_FACTURACION
```

---

## Diagnóstico final esperado

Si todas las pruebas anteriores funcionan, la configuración mínima está validada:

```text
settings.yaml válido
secrets.yaml válido
secrets.yaml excluido de Git
credential_manager funcional
src importable
SAPConnection importable desde src.core.sap_connection
win32com disponible
SAP GUI Scripting activo
notificaciones de scripting desactivadas
login automático por credentials funcional
sesión SAP accesible desde Python
transacción configurada abre correctamente
```

Con esto, el entorno queda preparado para ejecutar scripts de automatización SAP sin intervención manual inicial.
