import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sap_common import connect_to_session, run_transaction, press_button

def main():
    session = connect_to_session()

    # 1) Abrir transacción
    run_transaction(session, "/nZTSD_FACTURACION")

    # 2) Filtro: número de factura
    session.findById("wnd[0]/usr/txtS_NUM_F-LOW").Text = "2025102419"
    session.findById("wnd[0]/usr/txtS_NUM_F-HIGH").Text = ""

    # 3) Ejecutar (F8)
    press_button(session, "wnd[0]/tbar[1]/btn[8]")

if __name__ == "__main__":
    main()
