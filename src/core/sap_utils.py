import time
import logging

logger = logging.getLogger("SAP_Automation")

def _iter_children(component):
    """Safe iterator over SAP component children."""
    try:
        count = component.Children.Count
    except Exception:
        return
    for i in range(count):
        try:
            yield component.Children(i)
        except Exception:
            continue

def find_control_recursive(root, predicate):
    """
    Finds the first control matching the predicate.
    """
    try:
        if predicate(root):
            return root
    except Exception:
        pass

    for child in _iter_children(root):
        found = find_control_recursive(child, predicate)
        if found is not None:
            return found
    return None

def find_alv_shell(root):
    """
    Finds the ALV GuiShell.
    """
    def is_alv(node):
        t = getattr(node, "Type", "")
        return t == "GuiShell" and (hasattr(node, "GetCellValue") or hasattr(node, "SelectedRows"))
    
    return find_control_recursive(root, is_alv)

def handle_security_popup(session, max_attempts=6):
    """
    Handles the SAP security popup by clicking 'Allow'.
    """
    labels_ok = ("permetre", "permitir", "allow")
    
    for attempt in range(max_attempts):
        for idx in (1, 2):
            try:
                wnd = session.findById(f"wnd[{idx}]")
                if wnd.Type != "GuiModalWindow":
                    continue
                
                for child in _iter_children(wnd):
                    if child.Type != "GuiButton":
                        continue
                    
                    text = (getattr(child, "Text", "") or "").strip().lower()
                    tooltip = (getattr(child, "Tooltip", "") or "").strip().lower()
                    
                    if any(lbl in text for lbl in labels_ok) or any(lbl in tooltip for lbl in labels_ok):
                        child.press()
                        logger.info("Security popup handled (Allow pressed).")
                        return
            except Exception:
                continue
        time.sleep(0.5)

def close_excel_workbook(full_path):
    """
    Closes the specific Excel workbook if open.
    """
    try:
        import win32com.client
        excel = win32com.client.GetActiveObject("Excel.Application")
    except Exception:
        logger.debug("Excel not running or pywin32 issue.")
        return

    try:
        full_path_norm = full_path.lower().replace("/", "\\")
        target_wb = None
        for wb in excel.Workbooks:
            try:
                if wb.FullName.lower().replace("/", "\\") == full_path_norm:
                    target_wb = wb
                    break
            except Exception:
                continue
        
        if target_wb:
            only_this = excel.Workbooks.Count == 1
            target_wb.Close(SaveChanges=0)
            logger.info(f"Closed Excel workbook: {full_path}")
            
            if only_this:
                excel.Quit()
                logger.info("Closed Excel application (was the last workbook).")
        else:
            logger.debug(f"Workbook not found in Excel: {full_path}")

    except Exception as e:
        logger.warning(f"Error closing Excel: {e}")
