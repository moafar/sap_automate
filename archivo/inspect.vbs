Set SapGuiAuto = GetObject("SAPGUI")
Set application = SapGuiAuto.GetScriptingEngine
Set connection = application.Children(0)
Set session = connection.Children(0)

Set root = session.findById("wnd[0]/usr")

For i = 0 To root.Children.Count - 1
    On Error Resume Next
    Set child = root.Children(i)
    MsgBox child.Id
Next
