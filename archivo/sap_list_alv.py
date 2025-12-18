import win32com.client


def get_session(connection_index: int = 0, session_index: int = 0):
    sap_gui_auto = win32com.client.GetObject("SAPGUI")
    app = sap_gui_auto.GetScriptingEngine
    return app.Children(connection_index).Children(session_index)


def is_alv(component) -> bool:
    t = getattr(component, "Type", "")
    cid = getattr(component, "Id", "")
    name = getattr(component, "Name", "")
    text = f"{t} {cid} {name}".upper()
    if "ALV" in text:
        return True
    if t in ("GuiALVGrid", "GuiALVTree"):
        return True
    return False


def iter_children(component):
    try:
        count = component.Children.Count
    except Exception:
        return
    for i in range(count):
        try:
            yield component.Children(i)
        except Exception:
            continue


def collect_alvs(component, found=None):
    if found is None:
        found = []
    if is_alv(component):
        found.append(
            {
                "type": getattr(component, "Type", ""),
                "name": getattr(component, "Name", ""),
                "id": getattr(component, "Id", ""),
            }
        )
    for child in iter_children(component):
        collect_alvs(child, found)
    return found


def main():
    session = get_session()
    root = session.findById("wnd[0]")
    alvs = collect_alvs(root)

    if not alvs:
        print("No se encontraron ALVs en la sesión actual.")
        return

    print("ALVs detectados:")
    for i, a in enumerate(alvs, 1):
        print(f"{i}. {a['type']} | {a['name']} | {a['id']}")


if __name__ == "__main__":
    main()
