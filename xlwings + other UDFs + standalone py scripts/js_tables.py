import pandas as pd
import requests
from io import StringIO
from selenium import webdriver # import selenium
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

url = "https://insidepublicaccounting.com/top-firms/ipa-500/"
driver = webdriver.Chrome() # create a webdriver instance for Chrome
driver.get(url) # open the url in Chrome

tabs = driver.find_elements(By.CSS_SELECTOR, "ul.et_pb_tabs_controls li") # find the elements that represent the tabs
dfs = [] # create an empty list to store the dataframes

for tab in tabs: # loop through the tabs
    tab.click() # click on the tab
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "tbody"))) # wait until the table body is loaded
    html = driver.page_source # get the html source of the page
    tables = pd.read_html(StringIO(html)) # read the tables from the html
    df = tables[0] # select the first dataframe in the list
    dfs.append(df) # append the dataframe to the list

driver.quit() # close the browser
final_df = pd.concat(dfs, ignore_index=True)
final_df.to_csv("final_df.csv", sep="\t")
#for df in dfs: # loop through the dataframes
#    print(df) # print each dataframe

