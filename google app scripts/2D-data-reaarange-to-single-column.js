function stackData() {
  var sheet = SpreadsheetApp.getActiveSheet();
  var data = sheet.getRange("A1:AD625").getValues();
  var stackedData = [];
  for (var i = 0; i < data.length; i++) {
    for (var j = 0; j < data[i].length; j++) {
      if (data[i][j] !== "") {
        stackedData.push([data[i][j]]);
      }
    }
  }
  sheet.getRange(1, 32, stackedData.length, 1).setValues(stackedData);
}

