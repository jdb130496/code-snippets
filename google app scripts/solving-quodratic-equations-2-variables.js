function solveEquations() {
  var sheet = SpreadsheetApp.getActiveSheet();
  var range = sheet.getRange("A1:C2");
  var values = range.getValues();
  
  var D = values[0][0] * values[1][1] - values[0][1] * values[1][0];
  var Dx = values[0][2] * values[1][1] - values[0][1] * values[1][2];
  var Dy = values[0][0] * values[1][2] - values[0][2] * values[1][0];
  
  var X = Dx / D;
  var Y = Dy / D;
  
  sheet.getRange("E1").setValue("X");
  sheet.getRange("F1").setValue("Y")
  sheet.getRange("E2").setValue(X);
  sheet.getRange("F2").setValue(Y);
}
