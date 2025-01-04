fileName = 'ANU_3May2012_100MB'
outputFileName = 'ANU_3May2012_100MB.txt'
with open(fileName, mode='rb') as inputFile, open(outputFileName, mode='w') as outputFile:
    # read two bytes at a time
    while (bytes := inputFile.read(2)):
        # convert bytes to integer
        value = int.from_bytes(bytes, 'big')
        # extract sign bit (0 for negative, 1 for positive)
        sign = value >> 15
        # extract next 15 bits and convert to signed integer
        value = -(value & 0x7fff) if sign == 0 else value & 0x7fff
        # write value to output file
        outputFile.write(f'{value}\n')
