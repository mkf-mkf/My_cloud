import requests
import os
import re

def saver(login, passwod, start_date, end_date=None):
    if end_date is None:
        end_date = start_date
    s = requests.session()
    downloaded_folder = r'E:\Trading_diary\Detailed'
    login_data = {'user' : login, 'password' : password}
    resp = s.post('https://globaltrading.propreports.com/login.php', login_data)
    get_detailed_data = {'startDate' : start_date, 'endDate' : end_date,
                       'reportType' : 'detailed', 'export' : 1}
    export_excel = 'https://globaltrading.propreports.com/report.php?startDate=2018-08-09&endDate=2018-08-09&groupId=-4&accountId=250&reportType=detailed&mode=1&baseCurrency=USD&export=1'

    #r.post('https://globaltrading.propreports.com/report.php, get_detailed_data) # должно работать, и этот вариант лучше, но не провер€л
    r = s.get(export_excel)
    try:
        filename_pattern = re.compile(r'filename="([.\w-]+)')
        filename = re.search(filename_pattern, r.headers['Content-Disposition'])[1]

        with open(os.path.join(downloaded_folder, filename), 'wb') as f:  
            f.write(r.content)
    except KeyError:
        pass
