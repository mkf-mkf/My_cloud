import requests
import os
import re
import datetime as dt


def saver(login, password, start_date, end_date=None):
    '''
    login: str
    password: str
    start_date, end_date = datetime.datetime

    return: list

    скачивает файл за каждый день, возвращает список с именами файлов
    '''
    if end_date is None:
        end_date = start_date

    downloaded_folder = r'E:\Trading_diary\Detailed'
    filename_pattern = re.compile(r'filename="([.\w-]+)')

    s = requests.session()
    login_data = {'user' : login, 'password' : password}
    resp = s.post('https://globaltrading.propreports.com/login.php', login_data)
    
    list_of_files = []

    while start_date <= end_date:
        date = start_date.strftime('%Y-%m-%d')
        get_detailed_data = {'startDate' : date, 'endDate' : date,
                           'reportType' : 'detailed', 'export' : 1}
    
        #export_excel = 'https://globaltrading.propreports.com/report.php?startDate=2018-08-09&endDate=2018-08-09&groupId=-4&accountId=250&reportType=detailed&mode=1&baseCurrency=USD&export=1'

        r = s.post('https://globaltrading.propreports.com/report.php', get_detailed_data) # 
        #r = s.get(export_excel)
    
        try:
            
            filename = re.search(filename_pattern, r.headers['Content-Disposition'])[1]

            with open(os.path.join(downloaded_folder, filename), 'wb') as f:  
                f.write(r.content)

            list_of_files.append(filename)
    
        except KeyError:
            pass
        
        start_date += dt.timedelta(days=1)

    r = s.get('https://globaltrading.propreports.com/logout.php')

    return list_of_files