import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sap_common import connect_to_session, find_alv_shell


def main():
    session = connect_to_session()
    root = session.findById("wnd[0]")
    alv = find_alv_shell(root)

    if alv:
        print("ALV encontrado:")
        print("Type:", alv.Type)
        print("Id:", alv.Id)
        print("Name:", alv.Name)
    else:
        print("NO se encontró ALV en esta pantalla.")


if __name__ == "__main__":
    main()
