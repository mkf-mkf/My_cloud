import keyboard as kb
import time
import datetime as dt
# import pandas as pd
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


def download_chart_of_ticker(ticker, date, timeframe=1):
    now = dt.datetime.now()
    if not timeframe in ['d', 'D', 'w', 'W', 'q', 'Q', 'y', 'Y']:
        str_date = dt.datetime.strftime(date - dt.timedelta(days=1), "%d%m%Y")
        title_date = '2011-01-01'

    else:
        str_date = '01012011'
        title_date = f'{date:%Y-%m-%d}'

    ticker = ticker.upper()
    sleep(1)
    kb.send('alt+tab')
    sleep(1)

    kb.send('esc')

    # отправляем по символу тикер
    # for char in ticker:
    #    kb.send(char)

    kb.write(ticker)
    time.sleep(0.3)
    kb.send('enter')
    sleep(5)

    # выбираем таймфрейм и отправляем дату
    kb.send(f"esc, tab, comma, {timeframe}, enter, ctrl+shift+g")
    time.sleep(1.5)

    for i in str_date:
        kb.send(i)

    kb.send('enter')

    # переключаем на сам чарт
    if timeframe in ['d', 'D', 'w', 'W', 'q', 'Q', 'y', 'Y']:
        sleep(5)
    else:
        sleep(15)

    kb.send('esc, tab')

    kb.send('ctrl+alt+d')  # открываем окно "export to excel"

    time.sleep(0.4)
    kb.send('ctrl+a')

    path_dir = f'E:\\Trading_diary\\Esignal_charts\\{ticker}\\'

    if os.path.exists(path_dir) == False:
        os.makedirs(path_dir)

    if dt.datetime.now().time() > dt.time(16, 10):
        file_name = path_dir + f'{ticker}_{timeframe}_{title_date}_{now:%Y-%m-%d}.csv'

    else:
        file_name = path_dir + f'{ticker}_{timeframe}_{title_date}_{now - dt.timedelta(days=1):%Y-%m-%d}.csv'

    kb.write(file_name)

    kb.send('enter')


    sleep(12)
    kb.send('esc')
    time.sleep(0.1)
    kb.send('esc')
    time.sleep(0.1)

    if timeframe in ['d', 'D']:
        kb.send('ctrl+alt+d')  # открываем окно "export to excel"
        time.sleep(0.4)
        kb.send('ctrl+a')
        file_name = path_dir + f'{ticker}_latest_daily.csv'
        kb.write(file_name)
        time.sleep(0.3)
        kb.send('enter')
        sleep(5)
        kb.send('esc')
        time.sleep(0.1)
        kb.send('esc')
        time.sleep(0.1)


    kb.send('alt+tab')
    time.sleep(1)

    return file_name

