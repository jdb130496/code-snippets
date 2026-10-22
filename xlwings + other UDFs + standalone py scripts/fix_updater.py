with open(r'D:\dev\update_gecko_driver_and_firefox_nightly_06102026.py', encoding='utf-8') as f:
    content = f.read()

old = '        print("\\n--- Backup: Scripts ---")\n        result = subprocess.run(["python", r"D:\\dev\\backup_firefox.py", "--scripts-only"])'
new = '        backup_ts = time.strftime("%Y%m%d_%H%M%S")\n\n        print("\\n--- Backup: Scripts ---")\n        result = subprocess.run(["python", r"D:\\dev\\backup_firefox.py", "--scripts-only", backup_ts])'

assert old in content, "OLD string not found"
content = content.replace(old, new, 1)

old2 = '        result = subprocess.run(["python", r"D:\\dev\\backup_firefox.py", "--userdata-only"])'
new2 = '        result = subprocess.run(["python", r"D:\\dev\\backup_firefox.py", "--userdata-only", backup_ts])'

assert old2 in content, "OLD2 string not found"
content = content.replace(old2, new2, 1)

with open(r'D:\dev\update_gecko_driver_and_firefox_nightly_06102026.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Done')
