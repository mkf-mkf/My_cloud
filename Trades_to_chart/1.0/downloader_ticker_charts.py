import keyboard as kb
import time
import datetime as dt
#import pandas as pd
import os

def pause(seconds):
    k = 0
    while kb.is_pressed('esc') == False and k <= seconds:
        time.sleep(0.01)
        k += 0.01
    if kb.is_pressed('esc') == True:
        return True

def sleep(sec):
    for i in range(sec):
        time.sleep(1)


def download_chart_of_ticker(ticker, date):
    
    now = dt.datetime.now()
    str_date = dt.datetime.strftime(date - dt.timedelta(days=1), "%d%m%Y")
    #str_date_dots = dt.datetime.strftime(date, "%d.%m.%Y")
    sleep(2)
    kb.send('alt+tab')
    sleep(1)

    ticker = ticker.upper()
    kb.send('esc')
    
    # отправляем по символу тикер
    #for char in ticker:
    #    kb.send(char)
        
    
    kb.write(ticker)
    time.sleep(0.3)
    kb.send('enter')
    sleep(5)
    
    # выбираем дейли и отправляем дату
    kb.send("esc, tab, comma, 1, enter, ctrl+shift+g")
    time.sleep(0.2)
    
    for i in str_date:
        kb.send(i)

    kb.send('enter')
    
    # переключаем на сам чарт
    sleep(12)
    kb.send('esc, tab')
    
    kb.send('ctrl+alt+d') # открываем окно "export to excel"
        
    time.sleep(0.1)
    kb.send('ctrl+a')
    
    path_dir = f'E:\\Trading_diary\\Esignal_charts\\{ticker}\\'
    
    if os.path.exists(path_dir) == False:
        os.makedirs(path_dir)

    if dt.datetime.now().time() > dt.time(16, 0):
        file_name = path_dir + f'{ticker}_{date:%Y-%m-%d}_{now:%Y-%m-%d}.csv'

    else:
        file_name = path_dir + f'{ticker}_{date:%Y-%m-%d}_{now - dt.timedelta(days=1):%Y-%m-%d}.csv'

    kb.write(file_name)
    
    
    kb.send('enter')
    
    sleep(15)
    kb.send('esc')
    time.sleep(0.1)
    kb.send('esc')
    time.sleep(0.1)
    kb.send('alt+tab')

    return file_name

