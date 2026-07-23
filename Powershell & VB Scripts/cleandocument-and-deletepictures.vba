Sub DeleteAllPictures()
    Dim oShape As Shape
    Dim oInline As InlineShape
    
    ' Delete floating shapes (images, drawings)
    Do While ActiveDocument.Shapes.Count > 0
        ActiveDocument.Shapes(1).Delete
    Loop
    
    ' Delete inline images
    Do While ActiveDocument.InlineShapes.Count > 0
        ActiveDocument.InlineShapes(1).Delete
    Loop
    
    MsgBox "Done! Deleted all pictures.", vbInformation
End Sub
Sub CleanDocument()
    ' Delete floating shapes
    Do While ActiveDocument.Shapes.Count > 0
        ActiveDocument.Shapes(1).Delete
    Loop
    
    ' Delete inline images
    Do While ActiveDocument.InlineShapes.Count > 0
        ActiveDocument.InlineShapes(1).Delete
    Loop
    
    ' Use Find/Replace to collapse multiple blank lines into one
    Dim oFind As Find
    Dim lBefore As Long
    Dim lAfter As Long
    
    Set oFind = ActiveDocument.Content.Find
    oFind.ClearFormatting
    oFind.Replacement.ClearFormatting
    oFind.Forward = True
    oFind.Wrap = wdFindContinue
    oFind.Format = False
    oFind.MatchWildcards = False
    oFind.Text = "^13^13"
    oFind.Replacement.Text = "^13"
    
    ' Loop but stop when paragraph count stops changing
    Do
        lBefore = ActiveDocument.Paragraphs.Count
        oFind.Execute Replace:=wdReplaceAll
        lAfter = ActiveDocument.Paragraphs.Count
    Loop While lAfter < lBefore
    
    MsgBox "Done! Pictures removed and blank lines cleaned.", vbInformation
End Sub

