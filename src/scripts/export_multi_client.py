"""
Multi-Client Invoice Exporter
==============================
Script para exportar facturas de múltiples clientes con filtros fijos.

Aplica los siguientes filtros por cada cliente:
- Mes inicial: configurable (ej: 1)
- Mes final: configurable (ej: 10)
- Año: configurable (ej: 2025)
- Status: configurable (ej: F)

Genera un archivo Excel por cada cliente.

La lista de clientes se lee desde un archivo de texto con el formato:
- Un código de cliente por línea
- Líneas que empiezan con # son comentarios (ignoradas)
- Líneas vacías son ignoradas
"""

import os
import time
import logging
from datetime import datetime
from src.core.sap_utils import find_alv_shell, handle_security_popup, close_excel_workbook

logger = logging.getLogger("SAP_Automation")


def read_client_list(file_path):
    """
    Lee la lista de clientes desde un archivo de texto.
    
    Args:
        file_path: Ruta al archivo con la lista de clientes
        
    Returns:
        list: Lista de códigos de clientes
        
    Raises:
        FileNotFoundError: Si el archivo no existe
        ValueError: Si el archivo está vacío o no tiene clientes válidos
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Client list file not found: {file_path}")
    
    clients = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            # Quitar espacios en blanco
            line = line.strip()
            
            # Ignorar líneas vacías y comentarios
            if not line or line.startswith('#'):
                continue
            
            # Validar que no contenga espacios (código de cliente debe ser continuo)
            if ' ' in line:
                logger.warning(f"Line {line_num}: Ignoring line with spaces: '{line}'")
                continue
            
            clients.append(line)
    
    if not clients:
        raise ValueError(f"No valid client codes found in file: {file_path}")
    
    logger.info(f"Loaded {len(clients)} clients from {file_path}")
    return clients


class MultiClientExporter:
    """Exportador de facturas para múltiples clientes."""
    
    def __init__(self, session, config):
        """
        Inicializa el exportador.
        
        Args:
            session: Sesión SAP GUI activa
            config: Configuración del proyecto
        """
        self.session = session
        self.config = config
        
    def run(self, client_list, month_from, month_to, year, status):
        """
        Ejecuta la exportación para múltiples clientes.
        
        Args:
            client_list: Lista de códigos de clientes (ej: ["CLI001", "CLI002"])
            month_from: Mes inicial de facturación (ej: 1)
            month_to: Mes final de facturación (ej: 10)
            year: Año de facturación (ej: 2025)
            status: Status de facturación (ej: "F")
            
        Returns:
            dict: Resultados de la exportación por cliente
        """
        logger.info(f"Starting multi-client export for {len(client_list)} clients")
        logger.info(f"Filters: Month={month_from}-{month_to}, Year={year}, Status={status}")
        
        results = {}
        
        for idx, client_code in enumerate(client_list, 1):
            logger.info(f"[{idx}/{len(client_list)}] Processing client: {client_code}")
            
            try:
                success = self._export_single_client(
                    client_code=client_code,
                    month_from=month_from,
                    month_to=month_to,
                    year=year,
                    status=status
                )
                
                results[client_code] = {
                    "success": success,
                    "timestamp": datetime.now().isoformat()
                }
                
                if success:
                    logger.info(f"✓ Client {client_code} exported successfully")
                else:
                    logger.warning(f"✗ Client {client_code} export failed")
                    
            except Exception as e:
                logger.error(f"✗ Error exporting client {client_code}: {e}")
                results[client_code] = {
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
        
        # Resumen final
        successful = sum(1 for r in results.values() if r["success"])
        failed = len(results) - successful
        
        logger.info("="*60)
        logger.info(f"EXPORT SUMMARY: Success={successful}, Failed={failed}, Total={len(results)}")
        logger.info("="*60)
        
        return results
    
    def _export_single_client(self, client_code, month_from, month_to, year, status):
        """
        Exporta facturas para un solo cliente.
        
        Args:
            client_code: Código del cliente
            month_from: Mes inicial
            month_to: Mes final
            year: Año
            status: Status
            
        Returns:
            bool: True si la exportación fue exitosa
        """
        try:
            # 1. Navegar a la transacción
            tcode = self.config['sap']['transaction_code']
            self.session.findById("wnd[0]/tbar[0]/okcd").Text = tcode
            self.session.findById("wnd[0]").sendVKey(0)
            time.sleep(self.config['timeouts']['long_wait'])  # Need more time for transaction to load
            
            # 2. Aplicar filtros
            self._apply_filters(client_code, month_from, month_to, year, status)
            
            # 3. Ejecutar búsqueda
            self.session.findById("wnd[0]/tbar[1]/btn[8]").press()
            time.sleep(self.config['timeouts']['long_wait'])
            
            # 4. Verificar si hay resultados
            wnd0 = self.session.findById("wnd[0]")
            alv = find_alv_shell(wnd0)
            
            if not alv:
                logger.warning(f"No ALV found for client {client_code} - possibly no data")
                return False
            
            # 5. Exportar a Excel
            alv.ContextMenu()
            alv.SelectContextMenuItem("&XXL")
            time.sleep(self.config['timeouts']['default_wait'])
            
            # 6. Configurar formato de exportación
            self._handle_export_dialog()
            
            # 7. Guardar archivo
            extension = self.config['export'].get('extension', 'csv')
            filename = f"EXPORT_CLIENT_{client_code}_{year}M{month_from:02d}-{month_to:02d}_{datetime.now():%Y%m%d_%H%M%S}.{extension}"
            export_dir = self.config['export']['default_directory']
            full_path = os.path.join(export_dir, filename)
            
            self._handle_save_dialog(export_dir, filename)
            
            # 8. Manejar popup de seguridad
            handle_security_popup(self.session)
            
            # 9. Cerrar Excel
            time.sleep(self.config['timeouts']['long_wait'])
            close_excel_workbook(full_path)
            
            logger.info(f"Export saved: {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Error during export for client {client_code}: {e}")
            return False
    
    def _apply_filters(self, client_code, month_from, month_to, year, status):
        """
        Aplica los filtros en el formulario.
        
        Args:
            client_code: Código del cliente
            month_from: Mes inicial
            month_to: Mes final
            year: Año
            status: Status
        """
        # Cliente
        self.session.findById("wnd[0]/usr/ctxtS_KUNNR-LOW").Text = str(client_code)
        self.session.findById("wnd[0]/usr/ctxtS_KUNNR-HIGH").Text = ""
        
        # Mes inicial
        self.session.findById("wnd[0]/usr/ctxtS_MES-LOW").Text = str(month_from)
        
        # Mes final
        self.session.findById("wnd[0]/usr/ctxtS_MES-HIGH").Text = str(month_to)
        
        # Año
        self.session.findById("wnd[0]/usr/txtS_GJAHR-LOW").Text = str(year)
        self.session.findById("wnd[0]/usr/txtS_GJAHR-HIGH").Text = ""
        
        # Status
        self.session.findById("wnd[0]/usr/ctxtS_STATUS-LOW").Text = str(status)
        self.session.findById("wnd[0]/usr/ctxtS_STATUS-HIGH").Text = ""
        
        logger.debug(f"Filters applied: Client={client_code}, Month={month_from}-{month_to}, Year={year}, Status={status}")
    
    def _handle_export_dialog(self):
        """Maneja el diálogo de exportación."""
        try:
            wnd1 = self.session.findById("wnd[1]")
            
            # Intentar seleccionar formato
            try:
                cmb_format = wnd1.findById("usr/ssubSUB_CONFIGURATION:SAPLSALV_GUI_CUL_EXPORT_AS:0512/cmbGS_EXPORT-FORMAT")
                
                # Intentar establecer el formato configurado
                export_format = self.config['export'].get('format', 'csv-LEAN-STANDARD')
                
                # Si el formato es numérico, intentar convertirlo
                try:
                    cmb_format.Key = export_format
                    logger.debug(f"Export format set to: {export_format}")
                except Exception as format_error:
                    # Si falla, intentar con el formato por texto
                    logger.warning(f"Could not set format '{export_format}': {format_error}")
                    logger.info("Continuing with default export format")
                    
            except Exception as combo_error:
                logger.warning(f"Could not find format combo box: {combo_error}")
                logger.info("Continuing with default export format")
            
            # Presionar botón de exportación
            try:
                wnd1.findById("tbar[0]/btn[20]").press()
            except:
                wnd1.findById("tbar[0]/btn[0]").press()
            
            logger.debug("Export dialog handled")
            
        except Exception as e:
            logger.error(f"Error in export dialog: {e}")
            raise
    
    def _handle_save_dialog(self, directory, filename):
        """
        Maneja el diálogo de guardado.
        
        Args:
            directory: Directorio de destino
            filename: Nombre del archivo
        """
        time.sleep(self.config['timeouts']['default_wait'])
        
        try:
            wnd1 = self.session.findById("wnd[1]")
            wnd1.findById("usr/ctxtDY_PATH").Text = directory
            wnd1.findById("usr/ctxtDY_FILENAME").Text = filename
            wnd1.findById("tbar[0]/btn[0]").press()
            
            logger.debug("Save dialog handled")
            
        except Exception as e:
            logger.error(f"Error in save dialog: {e}")
            raise
