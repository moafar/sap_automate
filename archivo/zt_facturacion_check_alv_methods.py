import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sap_common import (
    connect_to_session,
    run_transaction,
    press_button,
    find_alv_shell,
)


def main():
    session = connect_to_session()

    # 1) Ir a la transacción
    run_transaction(session, "/nZTSD_FACTURACION")

    # 2) Filtro por número de factura
    session.findById("wnd[0]/usr/txtS_NUM_F-LOW").Text = "2025102419"
    session.findById("wnd[0]/usr/txtS_NUM_F-HIGH").Text = ""

    # 3) Ejecutar
    press_button(session, "wnd[0]/tbar[1]/btn[8]")

    # 4) Encontrar ALV
    root = session.findById("wnd[0]")
    alv = find_alv_shell(root)

    if not alv:
        print("NO se encontró ALV.")
        return

    print("ALV encontrado:", alv.Id)
    print("Type:", alv.Type)
    print("has RowCount   :", hasattr(alv, "RowCount"))
    print("has ColumnCount:", hasattr(alv, "ColumnCount"))
    print("has GetCellValue:", hasattr(alv, "GetCellValue"))

    # Intentar leer RowCount si existe
    try:
        rc = alv.RowCount
        print("RowCount OK   :", rc)
    except Exception as e:
        print("RowCount ERROR:", repr(e))

    # Intentar leer una celda (0,0) si es posible
    try:
        value_00 = alv.GetCellValue(0, 0)
        print("GetCellValue(0,0):", value_00)
    except Exception as e:
        print("GetCellValue ERROR:", repr(e))


if __name__ == "__main__":
    main()
