from selenium import webdriver
from selenium_stealth import stealth
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
import time
from datetime import datetime as dt
import re
import xlwings as xw
import re  # Regular expression library

@xw.func
def get_historical_data(script_name, end_date, start_date):
    end_date_timestamp = int(dt.strptime(end_date, "%d/%m/%Y").timestamp())
    start_date_timestamp = int(dt.strptime(start_date, "%d/%m/%Y").timestamp())
    options = webdriver.ChromeOptions()
    options.add_argument("start-minimized")
#    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537")
#    options.add_argument("--headless")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.binary_location = r"C:\Users\baksh\AppData\Local\Google\Chrome SxS\Application\chrome.exe"
    service = Service(r"D:\chromedriver.exe")  # replace with the path to your ChromeDriver
    options.add_extension(r'D:\AdBlock-—-best-ad-blocker.crx')
    driver = webdriver.Chrome(service=service, options=options)
    url = f"https://in.investing.com/equities/{script_name}-historical-data?end_date={end_date_timestamp}&st_date={start_date_timestamp}"
    stealth(driver,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
        )
    driver.get(url)
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

import pandas as pd
import xlwings as xw
import yfinance as yf
import datetime

@xw.func
def get_stock_data_yf(symbol, start_date, end_date):
    # Convert the date format from "dd/mm/yyyy" to "yyyy-mm-dd"
    start_date = datetime.datetime.strptime(start_date, "%d/%m/%Y").strftime("%Y-%m-%d")
    end_date = datetime.datetime.strptime(end_date, "%d/%m/%Y").strftime("%Y-%m-%d")

    # Download historical market data
    hist = yf.Ticker(symbol).history(start=start_date, end=end_date)

    # Fill missing values with a default value (like 'N/A' or 0)
    hist.fillna('N/A', inplace=True)

    # Reset the index to include it in the output
    hist.reset_index(inplace=True)

    # Convert the DataFrame to a list of lists
    data = hist.values.tolist()

    # Add the column names as the first list in the output
    data.insert(0, hist.columns.tolist())

    return data

@xw.func
def get_historical_data_gold(script_name, end_date, start_date):
    end_date_timestamp = int(dt.strptime(end_date, "%d/%m/%Y").timestamp())
    start_date_timestamp = int(dt.strptime(start_date, "%d/%m/%Y").timestamp())
    options = webdriver.ChromeOptions()
    options.add_argument("start-minimized")
#    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537")
#    options.add_argument("--headless")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.binary_location = r"C:\Users\baksh\AppData\Local\Google\Chrome SxS\Application\chrome.exe"
    service = Service(r"D:\chromedriver.exe")  # replace with the path to your ChromeDriver
    options.add_extension(r'D:\AdBlock-—-best-ad-blocker.crx')
    driver = webdriver.Chrome(service=service, options=options)
    options.add_extension(r'D:\AdBlock-—-best-ad-blocker.crx')
    url = f"https://in.investing.com/commodities/{script_name}-historical-data?cid=49776&end_date={end_date_timestamp}&st_date={start_date_timestamp}&interval_sec=daily"
    stealth(driver,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
        )
    driver.get(url)
    time.sleep(12)
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

@xw.func
def get_historical_data_other(script_name, end_date, start_date):
    end_date_timestamp = int(dt.strptime(end_date, "%d/%m/%Y").timestamp())
    start_date_timestamp = int(dt.strptime(start_date, "%d/%m/%Y").timestamp())
    options = webdriver.ChromeOptions()
    options.add_argument("start-minimized")
#    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537")
#    options.add_argument("--headless")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.binary_location = r"C:\Users\baksh\AppData\Local\Google\Chrome SxS\Application\chrome.exe"
    service = Service(r"D:\chromedriver.exe")  # replace with the path to your ChromeDriver
    options.add_extension(r'D:\AdBlock-—-best-ad-blocker.crx')
    driver = webdriver.Chrome(service=service, options=options)
    options.add_extension(r'D:\AdBlock-—-best-ad-blocker.crx')
    url = f"https://in.investing.com/commodities/{script_name}-historical-data?end_date={end_date_timestamp}&st_date={start_date_timestamp}&interval_sec=daily"
    stealth(driver,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
        )
    driver.get(url)
    time.sleep(12)
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

