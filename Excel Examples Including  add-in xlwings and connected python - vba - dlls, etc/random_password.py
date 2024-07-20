import pandas as pd
# Read the text file into a 2-dimensional list
with open('ascii.txt', 'r') as f:
    lines = f.readlines()
    data = [line.strip().split('\t') for line in lines]

# Create a dictionary to map hex characters to their corresponding text
char_dict = dict(data)

# Define the hex string
hex_string = '6d950d6ef347e164d640a6bd1a66184ba8de1150d993e0fc70189e9104f99f93fabd487e59fd89ca056556121e65730a7f02b750688093786332b6857b610731e1fd91aeb645438e95203c50113a2fafdd36bc691505bc31dfca49dfd3d5f8ec87e121b53d58ed682198b2e07748e243ea70568b9b824f167db26427a9f8485c81f75816bac0679c565d4210c24f0b6915a4f5218906049fed84d0feb91c60be8b164c14a9899e34c9ae5ab7959d117b30f90012a4c61fe7de2da43b7af73ab053bde08158db0a93e8100806b16eb4cb7402802db2ebaa72ac6ba178f3618e1fe61716c767d5c2e911aff95a06acf3042a6f32c302b5ef3562d0755ec31f79e0df71972b78086dd33a4f8c0ca6b0b9587df1ff24de521987a242dcc810eb2f7ae15bac2539ba551dcc0335ce450ce1770472712a647f30510610206e9ebbb8adc1c04fab8cfd495279d664527c0a6a5f293bb05cb68a1f913809561ef9c83441324d9715ca2186bc33cf9b4b7f000bc4b397b1462a02ae7fe0211a2bebf03f1cdce428ddedd4b3d696a9eaefed680567490f2524240f9c49d0d1ed800aede8291bdc78895b4ea33fda5a19a4d6b63193cc2b731258e3532310f7e5052a282efc25527522f7e0d920edf5a6ad82a3b00c27357a78c718c0143fd4b01459ccd76c638b3982c2b3d081a258bf2e18210a6fd5b1e11d753a923b95e8a6798beec7d94037358d351499d5cb2c9c0a073510eccc6e06b42980e6d49a3f9fd1b083031f3bf49237eca47da046c8002b375950f1941cf04ba4bca068767eb5fddfec45c19adb2a1bd829da8e8bc6462a67663f4ac638df123f5efc7cf6d336e2af38159649a10c0612050d19038051fe50d23a9dafedb72bc88224c5eea522c8598f861574e3447c6561354d0d799b1554d35254c64e63cedcee86319d4256db550156656bc76b0eeb6151702e410d3a7408217d6a95c935916dfb09c2713edec4f155db81084060f8987a84440e0aeb78de213aea3f1082280fdb8e514404147f296b98ee3d2b047813987b89cb11aa480d562cbe2c2582ff9603435002890d867dbfd41a54c1df63a564b09207df7ae57a84aa61f2bc1142beb3358897d098c57eb2cd3e7bd532190cf9d67ebc9c101876324df4764472bde9b8b041398cef01bf9bad7df2bee7cf763e569fc07efb8ad2decf826116bf1f917e20852a91db80e96ece177d6a4735e59807cc1763d712d199c6917598b564a04be015049407980e6e09de5cec976934de5a869b0eceeb7f5fc00d184fdc2e2f12f7cf475295664134b1327b1672922f95edf53b2dde39343dfd623e46613a94266bf7c6f193417a9a6f1fcab3cf2dc6b9c5f54103dcb1a6f929b94812e120bfe8e3236f4691bcdf8ef5ab06fabd0e7c45cbe29952ac626c249d7b1ab605cb1925ddf6967e45ea9d9cf5b18175f208cdebb21c618aa5afe9c65a182cb98833859132228951727df12a2c81a4f6d1f4bf07601d8807b9aec930e12cd244beab0730f1fc7d9fa8'

# Group the hex string into pairs of two characters
hex_pairs = [hex_string[i:i+2] for i in range(0, len(hex_string), 2)]

# Convert the hex pairs to their corresponding text characters
text_chars = [char_dict.get(pair.upper(), '') for pair in hex_pairs]

# Remove any null characters from the list of text characters
text_chars = [char for char in text_chars if char]

passwords = []
i = 0
spechar="!@#$%^&*()"
digits="0123456789"
while i < len(text_chars):
    password = ''
    j = 0
    while j < 12:
        if i >= len(text_chars):
            break
        else:
            char = text_chars[i]
        if j == 0 and char in "!@#$%^&*()":
            i += 1
            continue
        if j <= 11 and char.isdigit() and sum([1 for c in digits if c in password]) == 3:
            i += 1
            continue
        if j <= 11 and char in "!@#$%^&*()" and sum([1 for c in spechar if c in password]) == 2:
            i += 1
            continue
        if not char.isalnum() and char not in "!@#$%^&*()":
            i += 1
            continue
        password += char
#        print(f"i={i}, j={j}")
        i += 1
        j += 1
#    print(password)
    if any(char.isupper() for char in password) and any(char.islower() for char in password) and any(char in "!@#$%^&*()" for char in password):
        passwords.append(password)
#print(passwords)

#for group in [passwords[i:i+10] for i in range(0, len(passwords), 10)]:
#    print('\n'.join(group))
#for password in passwords:
#    if len(password) >= 12:
#        print(password)


# Create a list of passwords that are at least 12 characters long
passwords_long = [password for password in passwords if len(password) >= 12]

# Create a pandas DataFrame with the passwords
#df = pd.DataFrame({'Passwords': passwords_long})
df = pd.DataFrame(passwords_long,columns=['Passwords_List'])

# Print the DataFrame
print(df)

