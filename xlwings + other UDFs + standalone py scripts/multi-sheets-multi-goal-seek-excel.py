import xlwings as xw

# === CONFIG ===
FILE_PATH = r"D:\DGB Personal Data\personal\DGB investments New.xlsm"
SHEET_NAME = "Shares"

# (Set Cell, Target Value Cell, By Changing Cell)
# NOTE: Excel file must be OPEN before running this script
GOAL_SEEK_MAP = [
    ("Shares", "U178", "S178", "U174"),
    ("Shares", "U185", "S185", "U180"),
    ("Shares", "U190", "S190", "U187"),
    ("Shares", "U199", "S199", "U192"),
    ("Shares", "U204", "S204", "U201"),
    ("Shares", "U211", "S211", "U206"),
    ("Shares", "U216", "S216", "U213"),
    ("Shares", "U221", "S221", "U218"),
    ("Shares", "U227", "S227", "U223"),
    ("Shares", "U232", "S232", "U229"),
    ("Shares", "U237", "S237", "U234"),
    ("Shares", "U243", "S243", "U239"),
    ("Shares", "U248", "S248", "U245"),
    ("Juhi_Mutual_Funds", "R44", "P44", "P2"),
    ("Dhawal_Mutual_Funds", "R70", "Q70", "P1"),
    ("Bina_Mutual_Funds", "T123", "R123", "S1"),
    ("Shares", "Q44", "S28", "S42"),
    ("Shares", "Q145", "L145", "Q93"),
    ("Shares", "R145", "R146", "Q92"),

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
