import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sap_common import connect_to_session, find_control_recursive


def main():
    session = connect_to_session()
    root = session.findById("wnd[0]")

    # Buscamos el campo OKCODE (la barra donde se escribe /nVA01, etc.)
    def is_okcode(c):
        return getattr(c, "Type", "") == "GuiOkCodeField"

    ok = find_control_recursive(root, is_okcode)

    if ok:
        print("OKCODE encontrado:")
        print("Type:", ok.Type)
        print("Id:", ok.Id)
        print("Name:", ok.Name)
    else:
        print("NO se encontró el campo OKCODE.")

if __name__ == "__main__":
    main()
