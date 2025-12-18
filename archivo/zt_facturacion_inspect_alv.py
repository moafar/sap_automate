import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sap_common import connect_to_session, run_transaction, find_alv_shell


def main():
    session = connect_to_session()

    # 1) Ir a la transacción ZTSD_FACTURACION
    run_transaction(session, "/nZTSD_FACTURACION")

    # OJO: si la transacción tiene una pantalla inicial de selección
    # y solo aparece el ALV después de ejecutar, en esta primera versión
    # asume que ya estás en la pantalla del ALV.
    root = session.findById("wnd[0]")
    alv = find_alv_shell(root)

    if alv:
        print("ALV ZTSD_FACTURACION encontrado:")
        print("Type:", alv.Type)
        print("Id  :", alv.Id)
        print("Name:", alv.Name)
    else:
        print("NO se encontró ALV en la pantalla actual de ZTSD_FACTURACION.")


if __name__ == "__main__":
    main()
