On Error Resume Next

Set SapGuiAuto = GetObject("SAPGUI")
If Err.Number <> 0 Then
    MsgBox "ERROR: SAPGUI no responde al objeto COM." & vbCrLf & _
           "Scripting está DESHABILITADO en el servidor o no tienes permisos.", vbCritical
    WScript.Quit
End If

Set app = SapGuiAuto.GetScriptingEngine
If Err.Number <> 0 Then
    MsgBox "ERROR: No se pudo obtener ScriptingEngine." & vbCrLf & _
           "Scripting está BLOQUEADO en el servidor.", vbCritical
    WScript.Quit
End If

MsgBox "EXITO: ScriptingEngine está disponible y funcionando.", vbInformation
