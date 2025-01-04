import binascii

# Open the text file containing the hex string and read its contents
with open('D:\dgbdata\hex_block.txt', 'r') as f:
    hex_string = f.read().strip()

# Convert the hex string to binary data
binary_data = binascii.unhexlify(hex_string)

# Write the binary data to a new file
with open(r'd:\dgbdata\binarydump.bin', 'wb') as f:
    f.write(binary_data)

