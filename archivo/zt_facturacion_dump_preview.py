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

    # 5) Intentar leer tamaños
    try:
        rows = alv.RowCount
        cols = alv.ColumnCount
        print(f"ALV: {rows} filas, {cols} columnas")
    except Exception as e:
        print("Error leyendo RowCount/ColumnCount:", repr(e))
        return

    # 6) Intentar mostrar las primeras 3 filas y 5 columnas
    max_rows = min(rows, 3)
    max_cols = min(cols, 5)

    print("Preview de datos (máx 3x5):")
    for r in range(max_rows):
        values = []
        for c in range(max_cols):
            try:
                val = alv.GetCellValue(r, c)
            except Exception as e:
                val = f"<err:{e}>"
            values.append(str(val))
        print(f"Fila {r}: " + " | ".join(values))


if __name__ == "__main__":
    main()
