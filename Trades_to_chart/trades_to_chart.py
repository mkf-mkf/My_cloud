
# coding: utf-8

# Trades
# + Адрес хранилища данных: points
# Получение данных
# Адрес хранилища данных: данные
# + download data
# + read file
# Получение словаря датафремов трейдов
# + Данные: словарь датафреймов
# + method(type): type
# Преобразования к таймфрему оси чарта
# + Датафрейм: Агрегированный датафрейм по таймфрему
# + Агрегация экзекьюшинов с разницей времени < 5s
# + Агрегация по таймфреймам
# Рисование экзекьюшина на чарте
# + Dataframe: chart
# + plotly
# главная программа
# "Перенесение трейдов на график"
# главная программа(передаем источник трейдов, источник таблиц для графиков, дата=последний рабочий день):
#     обработка трейдов(источник трейдов, дата):
#     датафрейм графика = обработка источника таблиц графика(источник таблиц графиков, дата=последний рабочий день)
#     датафрейм трейдов = обработка источника хранилища (источник трейдов)
#     рисуем график стака с точками входа(датафрейм графика, датафрейм трейдов)
# Рисование чарта
# Рисование трейдов
# Candlestick
# Хранилище данных: chart object
# подготовка данных для графика
# + адрес хранилища данных: строка
# Получение данных
# + адресс файла (строка): содержимое файла
# + чтение данных
# Подготовка датафрейма
# Объект данных: строка
# + csv to Dataframe
# + Convert Data
# + Prepare columns
# Выбор времени
# Датафрейм : рабочий датафрейм
# + обрезаем датафрейм до нужных данных
# Получение таймфрейма
# + Dataframe : Dataframe
# + трансформация датафрейма
#    в нужный таймфрейм
# Plotting
# + Dataframe: Plott
# ploly candlestick
# Чарт
#

# деф главная программа(передаем источник трейдов, источник таблиц для графиков, дата=последний рабочий день):
#     обработка трейдов(источник трейдов, дата):
#     датафрейм графика = обработка источника таблиц графика(источник таблиц графиков, дата=последний рабочий день)
#     датафрейм трейдов = обработка источника хранилища (источник трейдов)
#     рисуем график стака с точками входа(датафрейм графика, датафрейм трейдов)

# In[1]:


import pandas as pd
import re
import plotly
import plotly.plotly as py
import plotly.graph_objs as go
import datetime as dt
import win32com.client
import time
from xlrd.compdoc import CompDocError

#plotly.tools.set_credentials_file(username='mkf', api_key='crwJntc1jJsAdaHKiDPL')


# In[2]:


from plotly.offline import download_plotlyjs, init_notebook_mode, plot, iplot
from plotly import tools
init_notebook_mode(connected=True)


# In[3]:


def fix_excel(trades_file):
    """Открывает и закрывает эксель файл при помощи VBA"""
    import win32com.client

    xl=win32com.client.Dispatch("Excel.Application")
    xl.Application.DisplayAlerts = False # disables Excel pop up message (for saving the file)
    wb = xl.Workbooks.Open(Filename=trades_file)
    wb.SaveAs(trades_file)
    wb.Close(True)
    xl.Application.DisplayAlerts = True

# In[279]:


def open_excel(path):
    """Открытие и чтение файла, в том числе, если он неправильно составлен"""
    try:
        open_file = pd.read_excel(path, encoding='utf-16', header=None)
    except CompDocError:
        fix_excel(path)
        open_file = pd.read_excel(path, encoding='utf-16', header=None)
    return open_file


# In[280]:


def normalise_formats(storage_of_executions):
    """Создание датафрейма Детейлс файла с нужными форматами и колонками"""
    important_columns = ['Order Id', 'Time', 'B/S', 'Qty', 'Price', 'Gross', 'Net', 'Route']
    copy_storage_of_executions = storage_of_executions.copy()
    for date, tickers in storage_of_executions.items():
        for ticker, executions in tickers.items():
            new_df = executions[important_columns]
            new_df.rename(columns={'B/S':'B_S', 'Order Id': 'Order_Id'}, inplace=True)
            new_df.insert(0, 'Date_Time', pd.to_datetime((date + ' ' + new_df['Time']), dayfirst=False))
            new_df.insert(1, 'Ticker', ticker)
            new_df['BP_Used'] = new_df['Price'] * new_df['Qty']
            new_df['Qty'] = new_df.apply(lambda x: x['Qty'] if new_df['B_S'][x.name] in ['B', 'C'] else -x['Qty'], axis=1)
            #new_df.insert(6, 'Pos_Size', new_df['Qty'].cumsum())
            new_df.reset_index(inplace=True)
            copy_storage_of_executions[date][ticker] = group_by_order_final(new_df)
    return copy_storage_of_executions


# In[281]:


def group_by_order(executions):
    """Стандартная группирока при помощи groupby"""
    round_sum = lambda x: round(sum(x), 2)
    int_sum = lambda x: int(sum(x))
    executions_by_order = executions.groupby('Order_Id').agg(({'index': 'first', 'Ticker' : 'first','Time' : 'first',
                                                               'Date_Time' : 'first', 'B_S' : 'first', 'Qty' : sum,
                                                               'Gross' : round_sum, 'Net' : round_sum, 'Route' : 'first',
                                                               'BP_Used': 'sum'}))

    executions_by_order['Price'] = abs(round(executions_by_order['BP_Used'] / executions_by_order['Qty'], 3))
    return executions_by_order


# In[7]:


def group_by_order_final(execution):
    ''' нужен для того, чтоб ордера работали в порядке исполнения, а не только по номеру'''
    new_group_by_orger = group_by_order(pd.DataFrame(columns=execution.columns))
    one_group = pd.DataFrame(columns=execution.columns)
    for i in range(len(execution)):
        if one_group.empty:
            one_group = one_group.append(execution.iloc[i, :])

        else:
            if execution.iloc[i]['Order_Id'] == one_group.iloc[-1]['Order_Id']:
                one_group = one_group.append(execution.iloc[i])

            else:
                new_group_by_orger = new_group_by_orger.append(group_by_order(one_group))
                #one_group = pd.DataFrame(columns=execution.columns)
                one_group = pd.DataFrame([execution.iloc[i]])


    new_group_by_orger = new_group_by_orger.append(group_by_order(one_group))
    new_group_by_orger.insert(6, 'Pos_Size', new_group_by_orger['Qty'].cumsum().apply(int))
    return new_group_by_orger



# In[294]:


def preprocessing_trades(storage_of_executions):
    """парсинг Детейлд файла и вывод его в формат {дата : {тикер : датафррейм_екзекюшина}}"""
    file_parsing = {}
    excel_df = storage_of_executions
    reindex = {a : b for a, b in zip(range(22), excel_df.iloc[2, :])} # вторая строка, 22 колонки в файле эксель
    excel_df = excel_df.rename(columns=reindex)

    date_re = re.compile(r'\d{1,2}/\d{1,2}/\d{4}')
    options_re = re.compile(r'^\+([\w/]+)\s{1,2}-\s.*')
    ticker_re = re.compile(r'^([\w/]+)\s{1,2}-\s.*')
    time_re = re.compile(r'\d\d:\d\d:\d\d')

    options = False
    for i in range(len(excel_df)):
        if pd.notna(excel_df.iloc[i][0]):
            if options == False:
                if re.match(date_re, excel_df.iloc[i][0]): #дата
                    date = excel_df.iloc[i][0]
                    file_parsing[date] = {}
                    continue

                elif re.match(options_re, excel_df.iloc[i][0]): #опционы
                    options = True
                    continue

                elif re.match(ticker_re, excel_df.iloc[i][0]): # если тикер
                    ticker = re.match(ticker_re, excel_df.iloc[i][0])[1]
                    file_parsing[date][ticker] = pd.DataFrame()
                    continue

                elif excel_df.iloc[i][0] == 'Time':

                    file_parsing[date][ticker].reindex(columns=excel_df.iloc[i])
                    columns = excel_df.iloc[i]
                    continue

                elif re.match(time_re, excel_df.iloc[i][0]): #Время
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


# In[283]:


def create_chart_df(chart_file):
    """Работа с есигнал чартом, нормализация форматов, создание нужных колонок"""
    chart_df = pd.read_csv(chart_file, sep=';', decimal=',', header=0)
    chart_df[['Open', 'High', 'Low', 'Close', 'PC', 'Vol']] = chart_df[['Open', 'High', 'Low', 'Close', 'PC', 'Vol']].apply(lambda x:  round(x, 2))
    if 'Time' in chart_df:
        chart_df.insert(0, 'Date_Time', pd.to_datetime((chart_df['Date'] + ' ' + chart_df['Time']), dayfirst=True))
    else:
        chart_df.insert(0, 'Date_Time', pd.to_datetime((chart_df['Date']), dayfirst=True))
    return chart_df


# In[284]:


def resampler(df, timeframe='5T'):
    """создание пятиминутного датафрейма"""
    return df.resample(timeframe).apply({'Open': 'first', 'High' : 'max', 'Low':'min', 'Close':'last'})


# In[255]:


def gap(needed_chart):
    open_candle = needed_chart.loc[needed_chart.Date_Time.apply(lambda x: x.time()) == dt.time(9, 30)]
    string = ''
    gap_ser = round((open_candle.Open - open_candle.PC) / open_candle.PC * 100, 1)
    for i in gap_ser:
        string += str(i)
    return string


# In[310]:


def chart_with_needed_dates(chart_df, date_of_trade):
    return chart_df[(chart_df.Date_Time.apply(lambda x: x.date()) >= date_of_trade.date()) &
      (chart_df.Date_Time.apply(lambda x: x.date()) < date_of_trade.date().replace(day=date_of_trade.day+1))]


# In[318]:


def make_main_chart(needed_chart, daily_df, drawing_trades, spy_needed_chart, spy_daily):

    buy_executions = drawing_trades.loc[drawing_trades['B_S'].isin(['B', 'C'])]
    sell_executions = drawing_trades.loc[drawing_trades['B_S'].isin(['S', 'T'])]

    decreasing = {"fillcolor": "rgb(227, 14, 0)",
                  "line": {
                      "color": "rgb(8, 7, 7)",
                      "width": 1}}

    increasing = {"fillcolor": "rgb(68, 171, 42)",
                  "line": {
                      "color": "rgb(5, 10, 8)",
                      "width": 1}}

    chart_1m = go.Candlestick(x=needed_chart.Date_Time,
                           open=needed_chart.Open,
                           high=needed_chart.High,
                           low=needed_chart.Low,
                           close=needed_chart.Close,
                           name=f"{buy_executions.Ticker[0]}_1m",
                           decreasing = decreasing,
                           increasing = increasing,
                           hoverinfo="x+y")

    chart_resampled_to5m = resampler(needed_chart.set_index('Date_Time'))

    chart_5m = go.Candlestick(x=chart_resampled_to5m.index,
                           open=chart_resampled_to5m.Open,
                           high=chart_resampled_to5m.High,
                           low=chart_resampled_to5m.Low,
                           close=chart_resampled_to5m.Close,
                           name=f"{buy_executions.Ticker[0]}_5m",
                           decreasing=decreasing,
                           increasing=increasing,
                           hoverinfo="x+y", visible="legendonly", yaxis='y')

    daily_chart = go.Candlestick(x=daily_df.Date_Time,
                                 open=daily_df.Open,
                                 high=daily_df.High,
                                 low=daily_df.Low,
                                 close=daily_df.Close,
                                 name=f"{buy_executions.Ticker[0]}_daily",
                                 yaxis='y4')

    spy_daily_chart = go.Candlestick(x=spy_daily.Date_Time,
                                 open=spy_daily.Open,
                                 high=spy_daily.High,
                                 low=spy_daily.Low,
                                 close=spy_daily.Close,
                                 name=f"{buy_executions.Ticker[0]}_daily",
                                 yaxis='y3',
                                 xaxis='x1')

    spy_chart_candlestick = go.Candlestick(x=spy_needed_chart.Date_Time,
                           open=spy_needed_chart.Open,
                           high=spy_needed_chart.High,
                           low=spy_needed_chart.Low,
                           close=spy_needed_chart.Close,
                          name='SPY',
                          decreasing = {"fillcolor": "rgb(227, 14, 0)",
                                        "line": {
                                          "color": "rgb(8, 7, 7)",
                                          "width": 1}},
                          increasing = {"fillcolor": "rgb(68, 171, 42)",
                                        "line": {
                                          "color": "rgb(5, 10, 8)",
                                          "width": 1}},
                          hoverinfo="x+y", xaxis='x', yaxis='y3')


    text_lambda = lambda x: [f'{i.B_S}: {int(i.Qty)}, Pos_Size: {i.Pos_Size}' for i in x.itertuples()]

    buy_trace = go.Scatter(x=buy_executions.Date_Time, y=buy_executions.Price, mode='markers', name='Buy',
                           marker = {"color": "rgb(103, 228, 97)",
                                     "line": {"width": 1},
                                     "size": 8},
                           text=text_lambda(buy_executions),
                           hoverinfo="y+text")

    sell_trace = go.Scatter(x=sell_executions.Date_Time, y=sell_executions.Price, mode='markers', name='Sell',
                            marker={
                                   "color": "rgb(235, 180, 12)",
                                   "line": {"width": 1},
                                   "size": 8},
                            yaxis= "y",
                            text=text_lambda(sell_executions),
                            hoverinfo="y+text")

    PH = go.Scatter(x=needed_chart.Date_Time, y=needed_chart.PH, name='PH',
                    line={"color": "rgb(0, 147, 0)", "dash": "dot", "shape": "linear", "width": 2},
                    hoverinfo='none')

    PL = go.Scatter(x=needed_chart.Date_Time, y=needed_chart.PL, name='PL',
                    line={"color": "rgb(189, 103, 117)", "dash": "dot"},
                    yaxis= "y", hoverinfo='none')

    PC = go.Scatter(x=needed_chart.Date_Time, y=needed_chart.PC, name='PC',
                    line={"color": "rgb(120, 75, 140)", "dash": "dash"},
                    yaxis="y", hoverinfo='none')

    Vol = dict(x=needed_chart.Date_Time, y=needed_chart.Vol, type='bar', yaxis='y2',
               marker= {"color": "rgb(119, 123, 227)"}, name='Vol')

    daily_Vol = dict(x=daily_df.Date_Time, y=daily_df.Vol, type='bar', yaxis='y2', xaxis='x1',
               marker= {"color": "rgb(119, 123, 227)"}, name='daily_Vol')

    #open_time_marker = needed_chart.loc[needed_chart.Date_Time.apply(
    #    lambda x: x.time()) == dt.time(9, 30), "Date_Time"]

    set_of_dates = set(needed_chart.Date_Time.apply(lambda x: x.date()))

    open_time_marker = [dt.datetime(i.year, i.month, i.day, 9, 30) for i in set_of_dates]

    #close_time_marker = needed_chart.loc[needed_chart.Date_Time.apply(
    #    lambda x: x.time()) == dt.time(16, 0), "Date_Time"]

    close_time_marker = [dt.datetime(i.year, i.month, i.day, 16, 0) for i in set_of_dates]

    y_coordinates_open_close_lines = [min(needed_chart.Low.min(), needed_chart.PL.min()),
                                      max(needed_chart.High.max(), needed_chart.PH.max())]

    open_time_line = go.Line(x=[open_time_marker, open_time_marker],
                                y=y_coordinates_open_close_lines, xaxis="x", yaxis='y')

    data = [chart_1m, buy_trace, sell_trace, PH, PL, PC, Vol, spy_chart_candlestick, chart_5m,
            daily_chart, spy_daily_chart, daily_Vol]

    layout = {
      'title': f'{gap(needed_chart)}%   {needed_chart.Date_Time.iloc[0].strftime("%Y-%m-%d")}\
      {drawing_trades.Ticker[0]}\
   Gross: {drawing_trades.Gross.sum()}   Vol: {int(drawing_trades.Qty.apply(abs).sum())}   \
   Net: {round(drawing_trades.Net.sum())}',
      "autosize": True,
      "height" : 1300,
      "bargap": 0.54,
      "xaxis": {
        "anchor": "y2",
        "autorange": True,
        "domain": [0, 65],
        "range": ["2018-08-06 05:17:30", "2018-08-06 19:47:30"],
        "rangeslider": {
          "autorange": True,
            "visible": False,
          #"range": ["2018-08-06 06:00:00", "2018-08-06 16:20:00"],
          #"range": ["2018-08-06 05:17:30", "2018-08-06 19:47:30"],
          #"yaxis2": {"rangemode": "match"}
        },
        "type": "date"
      },
        "xaxis1":{
            "anchor": "y",
            "autorange": True,
            "domain": [0.66, 1],
            #"range": ["2018-08-06 05:17:30", "2018-08-06 19:47:30"],
            "rangeslider": {
                "visible" : False,
                "autorange": True,
              #"range": ["2018-08-06 05:17:30", "2018-08-06 19:47:30"],
        }
      },

      "yaxis": {
        "anchor": "free",
        "autorange": True,
        "domain": [0.42, 0.82],
        #"overlaying": False,
        "position": 0,
        "range": [18.02, 23.62],
        "type": "linear"
      },
      "yaxis2": {
        "anchor": "x",
        "autorange": True,
        "domain": [0.35, 0.42],
        "range": [0, 254736.842105],
        "type": "linear"
      },
        "yaxis3": {
        "anchor": "x",
        "autorange": True,
        "domain": [0.82, 1],
        #"range": [0, 254736.842105],
        "type": "linear"
      },
        "yaxis4": {
        "anchor": "free",
        "autorange": True,
        "domain": [0.06, 0.35],
        #"overlaying": False,
        "position": 0,
        #"range": [18.02, 23.62],
        "type": "linear",
            "layer": "below traces",
            "side": "right"
       },

        "yaxis5": {
            "anchor": "free",
            "autorange": True,
            "domain": [0.00, 0.06],
            # "overlaying": False,
            "position": 0,
            # "range": [18.02, 23.62],
            "type": "linear",
            "layer": "below traces",
            "side": "right"
        },
         'shapes': [*[
        {
            'type': 'line',
            # x-reference is assigned to the x-values
            'xref': 'x',
            # y-reference is assigned to the plot paper [0,1]
            #'yref': 'paper',
            'x0': open_time_marker[i],
            'y0': y_coordinates_open_close_lines[0],
            'x1': open_time_marker[i],
            'y1': y_coordinates_open_close_lines[1],
            #'fillcolor': '#d3d3d3',
            'opacity': 0.2,
            'line': {
                'width' : 1,
                'dash' : 'dot'
            }
        } for i in range(len(open_time_marker))
       ],
        *[{
            'type': 'line',
            # x-reference is assigned to the x-values
            'xref': 'x',
            # y-reference is assigned to the plot paper [0,1]
            #'yref': 'paper',
            'x0': close_time_marker[i],
            'y0': y_coordinates_open_close_lines[0],
            'x1': close_time_marker[i],
            'y1': y_coordinates_open_close_lines[1],
            #'fillcolor': '#d3d3d3',
            'opacity': 0.2,
            'line': {
                'width' : 1,
                'dash' : 'dot'
            }
        } for i in range(len(open_time_marker))
        ]
                   ]
    }
    filename = r'E:\Trading_diary\Drawn_charts' + f'\{buy_executions.Date_Time.iloc[0].strftime("%Y-%m-%d")}_{buy_executions.Ticker[0]}.html'
    plot(dict(data=data, layout=layout), auto_open=False, filename=filename)
    return filename


if __name__ == '__main__':
    # In[295]:


    trades_file = r'C:/Users/User/Downloads/07060212-2018-08-06-to-2018-08-09-detailed.xls'
    chart_file = r'C:\Users\User\Documents\ARLO_06.08.18.csv'
    spy_file = r'C:\Users\User\Documents\SPY_example.csv'

    #trades_file = r'C:\Users\Kir\Documents\07060212-2018-08-06-to-2018-08-09-detailed.xlsx'
    #chart_file = r'C:\Users\User\Documents\Old_comp\Chart 2016-07-16-09-54.csv'


    # In[296]:


    date = '8/6/2018'
    ticker = 'ARLO'

    #trades_file = r'C:/Users/User/Downloads/07060212-2018-08-06-to-2018-08-09-detailed.xls'
    #chart_file = r'C:\Users\User\Documents\Old_comp\Chart 2016-07-16-09-54.csv'

    opened_file = open_excel(trades_file)
    date_tickers_exec = preprocessing_trades(opened_file)

    # In[297]:


    drawing_trades = date_tickers_exec[date][ticker]


    # In[298]:


    chart_df = create_chart_df(chart_file)


    # In[299]:


    spy_chart = create_chart_df(r"C:\Users\User\Documents\SPY_example_1m.csv")


    # In[300]:


    date_of_trade = drawing_trades.Date_Time[0]
    needed_chart = chart_df[(chart_df.Date_Time.apply(lambda x: x.date()) >= date_of_trade.date()) &
          (chart_df.Date_Time.apply(lambda x: x.date()) < date_of_trade.date().replace(day=date_of_trade.day+1))]


    # In[301]:


    spy_needed_chart = spy_chart[(spy_chart.Date_Time.apply(lambda x: x.date()) >= date_of_trade.date()) &
          (spy_chart.Date_Time.apply(lambda x: x.date()) < date_of_trade.date().replace(day=date_of_trade.day+1))]


    # In[302]:


    make_main_chart(needed_chart, drawing_trades, spy_needed_chart)


# In[ ]:


def candle_time(series, timeframe):
    #print(series, type(series))
    minute = series.minute - series.minute % timeframe
    return dt.datetime(series.year, series.month, series.day, series.hour, minute)

    #for i in len(dataframe):
    #    dataframe.iloc[i, 3]
    #dataframe.insert(0, 'Candle_Time', )


