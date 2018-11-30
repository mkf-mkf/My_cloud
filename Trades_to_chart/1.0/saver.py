from pandas import read_csv
from selenium import webdriver
import time
import datetime as dt


def saver(start_date, end_date=None):
    if end_date is None:
        end_date = start_date
    propreports_date_format = '%Y-%m-%d'
    login = "07060212"
    password = "parolo12"
    download_path = r'E:\Trading_diary\Detailed'

    chromeOptions = webdriver.ChromeOptions()
    prefs = {"download.default_directory" : download_path}
    chromeOptions.add_experimental_option("prefs",prefs)
    #chromedriver = "path/to/chromedriver.exe"
    driver = webdriver.Chrome(chrome_options=chromeOptions)
    

    driver = webdriver.Chrome()
    driver.set_window_size(1600, 900)

    start_date = dt.datetime.strftime(start_date, propreports_date_format)
    end_date = dt.datetime.strftime(end_date, propreports_date_format)
    driver.get(
        f'https://globaltrading.propreports.com/report.php?reportType=detailed&range=custom&startDate={start_date}&endDate={end_date}')

    driver.find_element_by_name('user').send_keys(login)
    driver.find_element_by_name('password').send_keys(password)
    driver.find_element_by_class_name('autoWidth').click()
    time.sleep(5)

    try:
        driver.find_element_by_link_text('Export to Excel').click()
        time.sleep(10)
    except Exception:
        pass

    driver.get('https://globaltrading.propreports.com/logout.php')

    driver.quit()

if __name__ == '__main__':
    saver()


"""
setting Chrome preferences w/ Selenium Webdriver in Python

The following worked for me:

chromeOptions = webdriver.ChromeOptions()
prefs = {"download.default_directory" : "/some/path"}
chromeOptions.add_experimental_option("prefs",prefs)
chromedriver = "path/to/chromedriver.exe"
driver = webdriver.Chrome(executable_path=chromedriver, chrome_options=chromeOptions)
"""
