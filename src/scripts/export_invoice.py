import os
import time
import logging
from datetime import datetime
from src.core.sap_utils import find_alv_shell, handle_security_popup, close_excel_workbook

logger = logging.getLogger("SAP_Automation")

class InvoiceExporter:
    def __init__(self, session, config):
        self.session = session
        self.config = config

    def run(self, invoice_number):
        logger.info(f"Starting export for invoice: {invoice_number}")
        
        try:
            # 1. Run Transaction
            tcode = self.config['sap']['transaction_code']
            self.session.findById("wnd[0]/tbar[0]/okcd").Text = tcode
            self.session.findById("wnd[0]").sendVKey(0)
            logger.info(f"Transaction {tcode} started.")

            # 2. Apply Filter
            self.session.findById("wnd[0]/usr/txtS_NUM_F-LOW").Text = invoice_number
            self.session.findById("wnd[0]/usr/txtS_NUM_F-HIGH").Text = ""
            self.session.findById("wnd[0]/tbar[1]/btn[8]").press()
            logger.info("Filter applied.")

            # 3. Find ALV
            wnd0 = self.session.findById("wnd[0]")
            alv = find_alv_shell(wnd0)
            if not alv:
                logger.error("ALV Grid not found.")
                return False
            
            # 4. Trigger Export
            alv.ContextMenu()
            alv.SelectContextMenuItem("&XXL")
            logger.info("Export menu triggered.")

            # 5. Handle Export Dialog
            self._handle_export_dialog()

            # 6. Handle Save Dialog
            extension = self.config['export'].get('extension', 'csv')
            filename = f"{self.config['export']['default_filename_prefix']}{datetime.now():%Y%m%d_%H%M%S}.{extension}"
            export_dir = self.config['export']['default_directory']
            full_path = os.path.join(export_dir, filename)
            
            self._handle_save_dialog(export_dir, filename)

            # 7. Handle Security Popup
            handle_security_popup(self.session)

            # 8. Close Excel
            time.sleep(self.config['timeouts']['long_wait'])
            close_excel_workbook(full_path)
            
            logger.info(f"Export completed successfully: {full_path}")
            return True

        except Exception as e:
            logger.error(f"Export failed: {e}")
            return False

    def _handle_export_dialog(self):
        try:
            wnd1 = self.session.findById("wnd[1]")
            # Set format
            cmb_format = wnd1.findById("usr/ssubSUB_CONFIGURATION:SAPLSALV_GUI_CUL_EXPORT_AS:0512/cmbGS_EXPORT-FORMAT")
            cmb_format.Key = self.config['export']['format']
            
            # Press Export
            try:
                wnd1.findById("tbar[0]/btn[20]").press() # Try one button
            except:
                wnd1.findById("tbar[0]/btn[0]").press() # Try another
            
            logger.info("Export dialog handled.")
        except Exception as e:
            logger.error(f"Error in export dialog: {e}")
            raise

    def _handle_save_dialog(self, directory, filename):
        time.sleep(self.config['timeouts']['default_wait'])
        try:
            wnd1 = self.session.findById("wnd[1]")
            wnd1.findById("usr/ctxtDY_PATH").Text = directory
            wnd1.findById("usr/ctxtDY_FILENAME").Text = filename
            wnd1.findById("tbar[0]/btn[0]").press()
            logger.info("Save dialog handled.")
        except Exception as e:
            logger.error(f"Error in save dialog: {e}")
            raise
