Sub ForceConvertTextToNumber()
    Dim cell As Range
    Dim rng As Range
    
    Set rng = Selection  ' Uses whatever range you've selected on the sheet
    
    Application.ScreenUpdating = False
    
    For Each cell In rng
        If cell.HasFormula = False And Len(cell.Value) > 0 Then
            cell.Value = cell.Value  ' Re-enters the value, same effect as F2+Enter
        End If
    Next cell
    
    Application.ScreenUpdating = True
    MsgBox "Done converting range."
End Sub
