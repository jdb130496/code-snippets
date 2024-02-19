#Hex blocks obtained from site: https://qrng.anu.edu.au/random-block-hex/
with open('D:\dgbdata\hex_block.txt', 'r') as f:
    hex_data = f.read().strip()

result = []
for i in range(0, len(hex_data), 4):
    hex_block = hex_data[i:i+4]
    binary_block = bin(int(hex_block, 16))[2:].zfill(16)
    sign = -1 if binary_block[0] == '0' else 1
    value = sign * int(binary_block[1:], 2)
    result.append(value)

with open('D:\dgbdata\integers.txt', 'w') as f:
    for value in result:
        f.write(str(value) + '\n')

