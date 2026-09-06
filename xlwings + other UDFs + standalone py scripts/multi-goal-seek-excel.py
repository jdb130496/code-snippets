import xlwings as xw

# === CONFIG ===
FILE_PATH = r"D:\DGB Personal Data\personal\DGB investments New.xlsm"
SHEET_NAME = "Shares"

# (Set Cell, Target Value Cell, By Changing Cell)
# NOTE: Excel file must be OPEN before running this script
GOAL_SEEK_MAP = [
    ("U174", "S174", "U170"),
    ("U181", "S181", "U176"),
    ("U186", "S186", "U183"),
    ("U194", "S194", "U188"),
    ("U201", "S201", "U196"),
    ("U206", "S206", "U203"),
    ("U211", "S211", "U208"),
    ("U217", "S217", "U213"),
    ("U222", "S222", "U219"),
    ("U227", "S227", "U224"),
    ("U233", "S233", "U229"),
    ("U238", "S238", "U235"),
]

def run_goal_seek():
    # Attaches to already-open Excel file (does NOT open new instance)
    wb = xw.Book(FILE_PATH)
    ws = wb.sheets[SHEET_NAME]

    for set_cell, target_cell, change_cell in GOAL_SEEK_MAP:
        wb.app.calculate()                          # force fresh recalc
        target_value = ws.range(target_cell).value  # read target from S column
        print(f"Goal Seek: {set_cell} → {target_value} by changing {change_cell}")
        ws.range(set_cell).api.GoalSeek(
            Goal=target_value,
            ChangingCell=ws.range(change_cell).api
        )
        wb.app.calculate()                          # settle after goal seek
        result = ws.range(set_cell).value
        print(f"  Result: {set_cell} = {result} (target was {target_value})")

    wb.save()
    print("Done!")

if __name__ == "__main__":
    run_goal_seek()
