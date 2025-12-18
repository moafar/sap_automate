import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sap_common import connect_to_session, run_transaction


def main():
    session = connect_to_session()
    # Cambia 'SE16N' por cualquier transacción que tengas permitida
    run_transaction(session, "/nZTSD_FACTURACION")

if __name__ == "__main__":
    main()
