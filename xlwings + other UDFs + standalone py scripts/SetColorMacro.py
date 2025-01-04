import xlwings as xw

def apply_colors(input_range, row_offset, col_offset):
    wb = xw.Book.caller()
    sheet = wb.sheets.active

    for cell in sheet.range(input_range):
        hex_value = cell.value
        if isinstance(hex_value, str) and len(hex_value) == 7 and hex_value.startswith('#'):
            try:
                # Convert the hex color code to RGB values
                rgb_value = int(hex_value[1:], 16)
                r = (rgb_value >> 16) & 255
                g = (rgb_value >> 8) & 255
                b = rgb_value & 255

                # Apply color with the offset defined by user
                cell.offset(row_offset, col_offset).color = (r, g, b)
            except ValueError:
                # Reset color for invalid hex codes
                cell.offset(row_offset, col_offset).color = None
        else:
            # Reset color for non-string values
            cell.offset(row_offset, col_offset).color = None

