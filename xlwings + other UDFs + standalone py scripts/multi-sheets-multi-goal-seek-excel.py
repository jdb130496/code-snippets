import xlwings as xw

# === CONFIG ===
FILE_PATH = r"D:\DGB Personal Data\personal\DGB investments New.xlsm"
SHEET_NAME = "Shares"

# (Set Cell, Target Value Cell, By Changing Cell)
# NOTE: Excel file must be OPEN before running this script
GOAL_SEEK_MAP = [
    ("Shares", "U174", "S174", "U170"),
    ("Shares", "U181", "S181", "U176"),
    ("Shares", "U186", "S186", "U183"),
    ("Shares", "U194", "S194", "U188"),
    ("Shares", "U201", "S201", "U196"),
    ("Shares", "U206", "S206", "U203"),
    ("Shares", "U211", "S211", "U208"),
    ("Shares", "U217", "S217", "U213"),
    ("Shares", "U222", "S222", "U219"),
    ("Shares", "U227", "S227", "U224"),
    ("Shares", "U233", "S233", "U229"),
    ("Shares", "U238", "S238", "U235"),
    ("Juhi_Mutual_Funds", "R44", "P44", "P2"),
    ("Dhawal_Mutual_Funds", "R70", "Q70", "P1"),
    ("Bina_Mutual_Funds", "T123", "R123", "S1"),
    ("Shares", "Q44", "S28", "S42"),
    ("Shares", "Q141", "L141", "Q91"),
    ("Shares", "R141", "R142", "Q90"),

]

def run_goal_seek():
    wb = xw.Book(FILE_PATH)
    # Validate all sheet names upfront
    actual_sheets = [s.name for s in wb.sheets]
    map_sheets = set(sheet_name for sheet_name, *_ in GOAL_SEEK_MAP)
    invalid = map_sheets - set(actual_sheets)
    if invalid:
        print(f"ERROR: These sheet names don't exist in the workbook: {invalid}")
        print(f"Available sheets: {actual_sheets}")
        return  # stop before doing anything
    for sheet_name, set_cell, target_cell, change_cell in GOAL_SEEK_MAP:  # unpack 4 values now
        ws = wb.sheets[sheet_name]                                          # get sheet per row
        wb.app.calculate()
        target_value = ws.range(target_cell).value
        print(f"[{sheet_name}] Goal Seek: {set_cell} → {target_value} by changing {change_cell}")
        ws.range(set_cell).api.GoalSeek(
            Goal=target_value,
            ChangingCell=ws.range(change_cell).api
        )
        wb.app.calculate()
        result = ws.range(set_cell).value
        print(f"  Result: {set_cell} = {result} (target was {target_value})")

    wb.save()
    print("Done!")
if __name__ == "__main__":
    run_goal_seek()
