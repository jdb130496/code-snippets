function readDataFromRange() {
    var startCol = 4;
    var startRow = 20;
    var endCol = 8;
    var endRow = 22;
    
    // Get the cell range
    var range = SpreadsheetApp.getActiveSheet().getRange(startRow + 1, startCol + 1, endRow - startRow + 1, endCol - startCol + 1);
    
    // Get the data from the cell range
    var data = range.getValues();
    
    // Flatten the data into a single column array
    var result = [];
    for (var i = 0; i < data.length; i++) {
        for (var j = 0; j < data[i].length; j++) {
            result.push(data[i][j]);
        }
    }
    
    // Output the result in column A, starting 2 rows below the selected range
    var outputRange = SpreadsheetApp.getActiveSheet().getRange(endRow + 3, startCol+1, result.length, 1);
    outputRange.setValues(result.map(function(x) { return [x]; }));
}


