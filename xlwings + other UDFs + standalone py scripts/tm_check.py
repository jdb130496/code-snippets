import os

files_dir = r'D:\Programs\firefox-userdata\storage\default\moz-extension+++3b9f6911-8ac6-4f0f-90c3-a2b1e7a663d6^userContextId=4294967295\idb\3647222921wleabcEoxlt-eengsairo.files'

out_dir = r'D:\dev\recovered_scripts'
os.makedirs(out_dir, exist_ok=True)

for fname in sorted(os.listdir(files_dir)):
    if not fname.isdigit():
        continue  # skip journals and other system files
    fpath = os.path.join(files_dir, fname)
    print(f'\n=== FILE: {fname} ===')
    with open(fpath, 'rb') as f:
        raw = f.read()
    try:
        text = raw.decode('utf-8')
    except:
        text = raw.decode('utf-16-le')
    
    # Extract script name for filename
    for line in text.splitlines():
        if '@name' in line:
            name = line.split('@name')[-1].strip().replace(' ', '_')
            break
    else:
        name = f'script_{fname}'
    
    out_path = os.path.join(out_dir, f'{fname}_{name}.user.js')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(text)
    print(text[:200])
    print(f'  -> Saved to {out_path}')

print('\nAll scripts saved to D:\\dev\\recovered_scripts\\')
