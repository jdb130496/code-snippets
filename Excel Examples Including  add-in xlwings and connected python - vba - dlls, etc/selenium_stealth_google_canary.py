from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium_stealth import stealth
from bs4 import BeautifulSoup
import time
from datetime import datetime as dt
import re
import xlwings as xw
import re  # Regular expression library
import pickle

@xw.func
def get_historical_data(script_name, end_date, start_date):
    end_date_timestamp = int(dt.strptime(end_date, "%d/%m/%Y").timestamp())
    start_date_timestamp = int(dt.strptime(start_date, "%d/%m/%Y").timestamp())
    options = webdriver.ChromeOptions()
#    options.add_argument("--remote-debugging-port=9292")
#    options.add_argument("user-data-dir=D:\\User Data")  # replace with the path to your User Data director
#    options.add_argument("profile-directory=Default")  # replace with your profile directory
    options.add_extension(r'D:\dev\AdBlock-—-best-ad-blocker.crx') 
    options.add_argument("start-maximized")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.binary_location = r"C:\Users\baksh\AppData\Local\Google\Chrome SxS\Application\chrome.exe"
    driver = webdriver.Chrome(service=Service(r"D:\chromedriver.exe"), options=options)
    url = f"https://in.investing.com/equities/{script_name}-historical-data?end_date={end_date_timestamp}&st_date={start_date_timestamp}"
    driver.get(url)
#    try:
#        cookies = pickle.load(open("cookies.pkl", "rb"))
#        for cookie in cookies:
#            driver.add_cookie(cookie)
#        driver.refresh()
#    except (FileNotFoundError, EOFError):
#        pass
    stealth(driver,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
        )
    time.sleep(2)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    div = soup.find('div', {'class': 'common-table-scroller js-table-scroller'})
    table = div.find('table', {'class': 'common-table medium js-table'})
    colgroup = table.find('colgroup')
    headers = [col.get('class')[0] for col in colgroup.find_all('col')]
    tbody = table.find('tbody')
    data = [
        [
            dt.strptime(" ".join([td.text.strip().rsplit(' ', 1)[0], re.sub(r'\D', '', td.text.strip().rsplit(' ', 1)[1])]), "%b %d, %Y") if i == 0 else float(td.text.replace(',', '')) if 1 <= i <= 4 else td.text.strip() 
            for i, td in enumerate(tr.find_all('td'))
        ]# .strftime("%d/%m/%Y") in dt.strptime(" ".join([td.text.strip().rsplit(' ', 1)[0], re.sub(r'\D', '', td.text.strip().rsplit(' ', 1)[1])]), "%b %d, %Y") at the end deleted to avoid date being converted to text.
        for tr in tbody.find_all('tr')
    ]
    result = [headers] + data
    driver.quit()
    return result

