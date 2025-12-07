import undetected_chromedriver as uc

print("Starting...")

chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

options = uc.ChromeOptions()
options.binary_location = chrome_path

# Add flags required for Chrome 143 on Windows 11
options.add_argument("--remote-allow-origins=*")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--disable-software-rasterizer")
options.add_argument("--disable-features=RendererCodeIntegrity")
options.add_argument("--disable-blink-features=AutomationControlled")

driver = uc.Chrome(options=options, version_main=143, use_subprocess=True)

driver.get("https://google.com")
print("Browser opened!")
input("Press Enter to exit...")
driver.quit()


