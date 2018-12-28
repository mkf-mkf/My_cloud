import pandas as pd
import datetime as dt
import re
import trades_to_chart as tdc
import os

def preprocessing_bests(storage_of_executions):
    """парсинг Детейлд файла и вывод его в формат {дата : {тикер : датафррейм_екзекюшина}}"""
    file_parsing = {}
    excel_df = storage_of_executions
    reindex = {a: b for a, b in zip(range(22), excel_df.iloc[2, :])}  # вторая строка, 22 колонки в файле эксель
    excel_df = excel_df.rename(columns=reindex)

    date_re = re.compile(r'\d{1,2}/\d{1,2}/\d{4}')
    options_re = re.compile(r'^\+([\w/]+)\s{1,2}-\s.*')
    ticker_re = re.compile(r'^([\w/]+)\s{1,2}-\s.*')
    time_re = re.compile(r'\d\d:\d\d:\d\d')

    options = False
    for i in range(len(excel_df)):
        if pd.notna(excel_df.iloc[i][0]):
            if options == False:
                if re.match(date_re, excel_df.iloc[i][0]):  # дата
                    date = excel_df.iloc[i][0]
                    file_parsing[date] = {}
                    continue

                elif re.match(options_re, excel_df.iloc[i][0]):  # опционы
                    options = True
                    continue

                elif re.match(ticker_re, excel_df.iloc[i][0]):  # если тикер
                    ticker = re.match(ticker_re, excel_df.iloc[i][0])[1]
                    file_parsing[date][ticker] = pd.DataFrame()
                    continue

                elif excel_df.iloc[i][0] == 'Time':

                    file_parsing[date][ticker].reindex(columns=excel_df.iloc[i])
                    columns = excel_df.iloc[i]
                    continue

                elif re.match(time_re, excel_df.iloc[i][0]):  # Время
                    file_parsing[date][ticker] = file_parsing[date][ticker].append(excel_df.iloc[i, :])

            else:
                if re.match(date_re, excel_df.iloc[i][0]):
                    options = False
                    date = excel_df.iloc[i][0]
                    file_parsing[date] = {}

                elif re.match(ticker_re, excel_df.iloc[i][0]):
                    options = False
                    ticker = re.match(ticker_re, excel_df.iloc[i][0])[1]
                    file_parsing[date][ticker] = pd.DataFrame()

    date_ticker_exec = normalise_formats(file_parsing)
    return date_ticker_exec