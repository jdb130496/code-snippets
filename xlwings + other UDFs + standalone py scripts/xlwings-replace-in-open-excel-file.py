import xlwings as xw
import re

FILE_PATH = r"D:\DGB Personal Data\personal\DGB investments New.xlsm"
SHEET_NAME = "Bina_Mutual_Funds"

REPLACEMENTS = {
    "HDFC Large and Mid Cap Fund"       : "HDFC Large & Mid Cap Fund",
    "HDFC ELSS Tax Saver"               : "HDFC ELSS - Tax Saver Fund",
    "HDFC Hybrid Debt Fund"             : "HDFC Conservative Hybrid Fund",
    "HDFC Hybrid Equity Fund"           : "HDFC Aggressive Hybrid Fund",
    "HDFC Credit Risk Debt Fund"        : "HDFC Credit Risk Fund",
    "HDFC Dynamic Debt Fund"            : "HDFC Dynamic Term Fund",
    "HDFC Floating Rate Debt Fund"      : "HDFC Floating Interest Rates Fund",
    "HDFC Income Fund"                  : "HDFC Medium to Long Term Fund",
    "HDFC Long Duration Debt Fund"      : "HDFC Long Term Fund",
    "HDFC Low Duration Fund"            : "HDFC Ultra Short to Short Term Fund",
    "HDFC Medium Term Debt Fund"        : "HDFC Medium Term Fund",
    "HDFC Multi-Asset Allocation Fund"  : "HDFC Multi Asset Allocation Fund",
    "HDFC Short Term  Debt Fund"        : "HDFC Short Term Fund",
    "HDFC Retirement Savings Fund"      : "HDFC Retirement Fund",
}

def run_replace():
    wb = xw.Book(FILE_PATH)
    ws = wb.sheets[SHEET_NAME]

    last_row = ws.used_range.last_cell.row
    rng = ws.range(f"A1:A{last_row}")

    # ✅ Read entire column in ONE call
    values = rng.value

    replaced_count = 0
    new_values = []

    for i, val in enumerate(values):
        if val is None:
            new_values.append(None)
            continue

        cell_val = str(val).strip()
        new_val = cell_val  # default — no change

        # normalise multiple spaces to single for comparison
        normalised_cell = re.sub(r' +', ' ', cell_val)

        for old_name, new_name in REPLACEMENTS.items():
            normalised_old = re.sub(r' +', ' ', old_name)

            if normalised_old in normalised_cell:
                # try exact replace first
                new_val = cell_val.replace(old_name, new_name)
                # if exact didn't work (space mismatch), use normalised
                if new_val == cell_val:
                    new_val = normalised_cell.replace(normalised_old, new_name)
                print(f"  ✅ Row {i+1}: '{cell_val}' → '{new_val}'")
                replaced_count += 1
                break  # one match per cell is enough

        new_values.append(new_val)

    # ✅ Write entire column back in ONE call
    rng.value = [[v] for v in new_values]

    print(f"\nDone! {replaced_count} replacements made.")

if __name__ == "__main__":
    run_replace()
