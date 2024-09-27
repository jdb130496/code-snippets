#Converting the random numbers into one byte integers
#Binary file downloaded from https://cloudstor.aarnet.edu.au/plus/s/9Ik6roa7ACFyWL4 Referred by https://qrng.anu.edu.au/contact/faq/#downloads
fileName = 'ANU_3May2012_100MB'
outputFileName = 'ANU_3May2012_100MB.txt'
with open(fileName, mode='rb') as inputFile, open(outputFileName, mode='w') as outputFile:
    # read one byte, convert to integer 0--255
    while (byte := inputFile.read(1)):
        value = int.from_bytes(byte, 'big')
        outputFile.write(f'{value}\n')
