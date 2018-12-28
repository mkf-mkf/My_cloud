
# coding: utf-8

# In[24]:

import os
import datetime as dt
import pandas as pd
import re
from xlrd.compdoc import CompDocError
import plotly.graph_objs as go
from plotly.offline import download_plotlyjs, init_notebook_mode, plot, iplot
init_notebook_mode(connected=True)

# In[31]:


#ticker = None
#trade_date = None

###############################################
class RecievedDataError(Exception):
    pass


def fix_excel(trades_file):
    """Открывает и закрывает эксель файл при помощи VBA"""
    import win32com.client

    xl = win32com.client.Dispatch("Excel.Application")
    xl.Application.DisplayAlerts = False  # disables Excel pop up message (for saving the file)
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
            new_df.rename(columns={'B/S': 'B_S', 'Order Id': 'Order_Id'}, inplace=True)
            new_df.insert(0, 'Date_Time', pd.to_datetime((date + ' ' + new_df['Time']), dayfirst=False))
            new_df.insert(1, 'Ticker', ticker)
            new_df['BP_Used'] = new_df['Price'] * new_df['Qty']
            new_df['Qty'] = new_df.apply(lambda x: x['Qty'] if new_df['B_S'][x.name] in ['B', 'C'] else -x['Qty'],
                                         axis=1)
            # new_df.insert(6, 'Pos_Size', new_df['Qty'].cumsum())
            new_df.reset_index(inplace=True)
            copy_storage_of_executions[date][ticker] = group_by_order_final(new_df)
    return copy_storage_of_executions


# In[281]:


def group_by_order(executions):
    """Стандартная группирока при помощи groupby"""
    round_sum = lambda x: round(sum(x), 2)
    int_sum = lambda x: int(sum(x))
    executions_by_order = executions.groupby('Order_Id').agg(({'index': 'first', 'Ticker': 'first', 'Time': 'first',
                                                               'Date_Time': 'first', 'B_S': 'first', 'Qty': sum,
                                                               'Gross': round_sum, 'Net': round_sum, 'Route': 'first',
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
                # one_group = pd.DataFrame(columns=execution.columns)
                one_group = pd.DataFrame([execution.iloc[i]])

    new_group_by_orger = new_group_by_orger.append(group_by_order(one_group))
    new_group_by_orger.insert(6, 'Pos_Size', new_group_by_orger['Qty'].cumsum().apply(int))
    return new_group_by_orger


def preprocessing_trades(storage_of_executions):
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


# In[283]:


def create_chart_df(chart_file):
    """Работа с есигнал чартом, нормализация форматов, создание нужных колонок"""
    chart_df = pd.read_csv(chart_file, sep=';', decimal=',', header=0)
    chart_df[['Open', 'High', 'Low', 'Close', 'PC', 'Vol']] = chart_df[
        ['Open', 'High', 'Low', 'Close', 'PC', 'Vol']].apply(lambda x: round(x, 2))
    if 'Time' in chart_df:
        chart_df.insert(0, 'Date_Time', pd.to_datetime((chart_df['Date'] + ' ' + chart_df['Time']), dayfirst=True))
    else:
        chart_df.insert(0, 'Date_Time', pd.to_datetime((chart_df['Date']), dayfirst=True))
    return chart_df


# In[284]:


def resampler(df, timeframe='5T'):
    """создание пятиминутного датафрейма"""
    return df.resample(timeframe).apply({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last'})


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
    needed_start_dt = (date_of_trade - dt.timedelta(1)).replace(hour=15, minute=30)
    needed_end_dt = date_of_trade + dt.timedelta(1)
    #return chart_df[(chart_df.Date_Time.apply(lambda x: x.date()) >= date_of_trade.date()) &
    #                (chart_df.Date_Time.apply(lambda x: x.date()) < date_of_trade.date().replace(
    #                    day=date_of_trade.day + 1))]
    return chart_df.loc[(chart_df.Date_Time >= needed_start_dt) &
                        (chart_df.Date_Time <= needed_end_dt)]

##################################################################


def buy_sell_executions(drawing_trades):
    buy_executions = drawing_trades.loc[drawing_trades['B_S'].isin(['B', 'C'])]
    sell_executions = drawing_trades.loc[drawing_trades['B_S'].isin(['S', 'T'])]
    return {'buy_executions' : buy_executions, 'sell_executions' : sell_executions}


# In[32]:


def preparation_chart_traces(needed_chart, daily_df, spy_needed_chart, spy_daily, ticker):
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
                              name=f"{ticker}_1m",
                              decreasing=decreasing,
                              increasing=increasing,
                              hoverinfo="x+y",
                              xaxis='x10',
                              yaxis='y10')

    chart_resampled_to5m = resampler(needed_chart.set_index('Date_Time'))

    chart_5m = go.Candlestick(x=chart_resampled_to5m.index,
                              open=chart_resampled_to5m.Open,
                              high=chart_resampled_to5m.High,
                              low=chart_resampled_to5m.Low,
                              close=chart_resampled_to5m.Close,
                              name=f"{ticker}_5m",
                              decreasing=decreasing,
                              increasing=increasing,
                              hoverinfo="x+y", visible="legendonly", yaxis='y10',
                              xaxis='x10')

    daily_chart = go.Candlestick(x=daily_df.Date_Time,
                                 open=daily_df.Open,
                                 high=daily_df.High,
                                 low=daily_df.Low,
                                 close=daily_df.Close,
                                 name=f"{ticker}_daily",
                                 decreasing=decreasing,
                                 increasing=increasing,
                                 yaxis='y6',
                                 xaxis='x1')

    spy_daily_chart = go.Candlestick(x=spy_daily.Date_Time,
                                     open=spy_daily.Open,
                                     high=spy_daily.High,
                                     low=spy_daily.Low,
                                     close=spy_daily.Close,
                                     name=f"SPY_daily",
                                     decreasing=decreasing,
                                     increasing=increasing,
                                     yaxis='y7',
                                     xaxis='x1')

    spy_chart_candlestick = go.Candlestick(x=spy_needed_chart.Date_Time,
                                           open=spy_needed_chart.Open,
                                           high=spy_needed_chart.High,
                                           low=spy_needed_chart.Low,
                                           close=spy_needed_chart.Close,
                                           name='SPY_intraday',
                                           decreasing=decreasing,
                                           increasing=increasing,
                                           hoverinfo="x+y", xaxis='x10', yaxis='y2')


    PH = go.Scatter(x=needed_chart.Date_Time, y=needed_chart.PH, name='PH',
                    line={"color": "rgb(0, 147, 0)", "dash": "dot", "shape": "linear", "width": 2},
                    hoverinfo='none', xaxis='x10', yaxis='y10')

    PL = go.Scatter(x=needed_chart.Date_Time, y=needed_chart.PL, name='PL',
                    line={"color": "rgb(189, 103, 117)", "dash": "dot"},
                    hoverinfo='none', xaxis='x10', yaxis='y10')

    PC = go.Scatter(x=needed_chart.Date_Time, y=needed_chart.PC, name='PC',
                    line={"color": "rgb(120, 75, 140)", "dash": "dash"},
                    hoverinfo='none', xaxis='x10', yaxis='y10')

    Vol = dict(x=needed_chart.Date_Time, y=needed_chart.Vol, type='bar',
               marker={"color": "rgb(119, 123, 227)"}, name='Vol', xaxis='x10', yaxis='y1')

    daily_Vol = dict(x=daily_df.Date_Time, y=daily_df.Vol, type='bar',
                     marker={"color": "rgb(119, 123, 227)"},
                     name='daily_Vol', xaxis='x1', yaxis='y5')

    return [chart_1m, PH, PL, PC, Vol, spy_chart_candlestick, 
            chart_5m, daily_chart, spy_daily_chart, daily_Vol]


# In[29]:


def open_close_coordinates(needed_chart):
    y_coordinates_open_close_lines = [min(needed_chart.Low.min(), needed_chart.PL.min()),
                                      max(needed_chart.High.max(), needed_chart.PH.max())]
    
    set_of_dates = set(needed_chart.Date_Time.apply(lambda x: x.date()))
    
    open_time_marker = [dt.datetime(i.year, i.month, i.day, 9, 30) for i in set_of_dates]
    close_time_marker = [dt.datetime(i.year, i.month, i.day, 16, 0) for i in set_of_dates]
    
    return {'open_time_marker' : open_time_marker, 'close_time_marker' : close_time_marker,
            'y_coordinates_open_close_lines' : y_coordinates_open_close_lines}


# In[33]:
symbols = ["circle-dot", "square-dot", "diamond-dot", "cross-dot",
           "x-dot", "star-dot", "hexagram-dot", "star-square-dot",
          "star-diamond-dot", "diamond-tall-dot", "hexagon-dot"]


def preparation_trades_traces(name, drawing_trades, symbol='circle-dot'):
    executions = buy_sell_executions(drawing_trades)

    text_lambda = lambda x: [f'{i.B_S}: {int(i.Qty)}, Pos_Size: {i.Pos_Size}' for i in x.itertuples()]

    buy_trace = go.Scatter(x=executions['buy_executions'].Date_Time, y=executions['buy_executions'].Price,
                           mode='markers', name=f'Buy {name}',
                           marker={"color": "rgb(103, 228, 97)",
                                   "line": {"width": 1},
                                   "size": 8,
                                   'symbol':symbol},
                           text=text_lambda(executions['buy_executions']),
                           hoverinfo="y+text", visible="legendonly",
                           xaxis='x10', yaxis='y10')

    sell_trace = go.Scatter(x=executions['sell_executions'].Date_Time, y=executions['sell_executions'].Price,
                            mode='markers', name=f'Sell {name}',
                            marker={
                                "color": "rgb(235, 180, 12)",
                                "line": {"width": 1},
                                "size": 8,
                                'symbol':symbol},
                            text=text_lambda(executions['sell_executions']),
                            hoverinfo="y+text", visible="legendonly",
                            xaxis='x10', yaxis='y10')

    return [buy_trace, sell_trace]


# In[30]:
def find_max_net_key(df_dict):
    max_key = None
    max_net = None
    for key in df_dict:
        if not max_key or max_net < df_dict[key].Net.sum():
            max_key = key
            max_net = df_dict[key].Net.sum()
    return max_key


def make_layout(date, needed_chart, drawing_trades=None, exec_dict=None):
    open_close_markers = open_close_coordinates(needed_chart)
    try:
        chart_info = f'{gap(needed_chart)}%   {needed_chart.Date_Time.iloc[0].strftime("%Y-%m-%d")}'
    except:
        print(needed_chart)
        raise Exception

    if not drawing_trades and not exec_dict:
        raise RecievedDataError('Не получено датафрейма или словаря экзекьюшинов')

    elif drawing_trades:
        ticker = drawing_trades.Ticker[0]
        gross = drawing_trades.Gross.sum()
        vol = int(drawing_trades.Qty.apply(abs).sum())
        net = round(drawing_trades.Net.sum())

    elif exec_dict:
        max_net_key = find_max_net_key(exec_dict)

        ticker = exec_dict[max_net_key].Ticker[0]
        gross = exec_dict[max_net_key].Gross.sum()
        vol = int(exec_dict[max_net_key].Qty.apply(abs).sum())
        net = round(exec_dict[max_net_key].Net.sum())

    title = chart_info + ' '*8 + ticker + ' '*8 + f'Gross: {gross}    Vol: {vol}      Net: {net}'

    layout = {
        'title': title,
        "autosize": True,
        # "height" : 1300,
        # "bargap": 0.54,
        "xaxis10": {
            "anchor": 'free',
            # "autorange": True,
            "range": [date.replace(hour=6, minute=30),
                      date.replace(hour=16, minute=15)],
            "domain": [0, 0.65],
            "rangeslider": {
                "autorange": True,
                "visible": False,
            },
            "type": "date"
        },
        "xaxis1": {
            "anchor": "free",
            # "autorange": True,
            "range": [date - dt.timedelta(days=365),
                      date],
            "domain": [0.65, 1],
            "rangeslider": {
                "visible": False}
        },
        "yaxis10": {
            "anchor": "x10",
            "autorange": True,
            "domain": [0.17, 0.7],
            # "overlaying": False,
            "position": 0,
            # "range": [18.02, 23.62],
            "type": "linear"
        },
        "yaxis1": {
            "anchor": "x10",
            "autorange": True,
            "domain": [0, 0.16],
            "type": "linear"
        },
        "yaxis2": {
            "anchor": "x10",
            "autorange": True,
            "domain": [0.71, 1],
            "type": "linear"
        },
        "yaxis6": {
            "anchor": "x1",
            "autorange": True,
            "domain": [0.17, 0.7],
            # "overlaying": False,
            "position": 0,
            # "range": [18.02, 23.62],
            "type": "linear"
        },
        "yaxis5": {
            "anchor": "x1",
            "autorange": True,
            "domain": [0, 0.16],
            "type": "linear"
        },
        "yaxis7": {
            "anchor": "x1",
            "autorange": True,
            "domain": [0.71, 1],
            "type": "linear"
        },

        'shapes': [*[
            {
                'type': 'line',
                # x-reference is assigned to the x-values
                'xref': 'x',
                # y-reference is assigned to the plot paper [0,1]
                # 'yref': 'paper',
                'x0': open_close_markers['open_time_marker'][i],
                'y0': open_close_markers['y_coordinates_open_close_lines'][0],
                'x1': open_close_markers['open_time_marker'][i],
                'y1': open_close_markers['y_coordinates_open_close_lines'][1],
                # 'fillcolor': '#d3d3d3',
                'opacity': 0.2,
                'line': {
                    'width': 1,
                    'dash': 'dot'
                }
            } for i in range(len(open_close_markers['open_time_marker']))
        ],
                   *[{
                       'type': 'line',
                       # x-reference is assigned to the x-values
                       'xref': 'x',
                       # y-reference is assigned to the plot paper [0,1]
                       # 'yref': 'paper',
                       'x0': open_close_markers['open_time_marker'][i],
                       'y0': open_close_markers['y_coordinates_open_close_lines'][0],
                       'x1': open_close_markers['open_time_marker'][i],
                       'y1': open_close_markers['y_coordinates_open_close_lines'][1],
                       # 'fillcolor': '#d3d3d3',
                       'opacity': 0.2,
                       'line': {
                           'width': 1,
                           'dash': 'dot'
                       }
                   } for i in range(len(open_close_markers['open_time_marker']))
                   ]
                   ]
    }

    return layout


# In[ ]:
"""

trades_traces = []
for file in files:
    trades_traces = [*trades_traces, *prepearing_trades_traces(file)]


# In[ ]:


data = [*preparation_trades_traces(drawing_trades), # *trades_traces,
        *preparation_chart_traces(needed_chart, daily_df, spy_needed_chart, spy_daily)]

filename = r'E:\Trading_diary\Drawn_charts' + /
f'\{login}_{trade_date.strftime("%Y-%m-%d")}_{ticker}_{drawing_trades.Gross.sum()}.html'
plot(dict(data=data, layout=make_layout(needed_chart, drawing_trades)), auto_open=False, filename=filename)
return filename


# In[53]:


try:
    plot([go.Scatter(x=[1], y=[5])], filename=r'E:\Trading_diary\Drawn_charts\{login}\')
except FileNotFoundError:
    os.makedirs(f'E:\Trading_diary\Drawn_charts\{login}')
    plot([go.Scatter(x=[1], y=[5])], filename=r'E:\Trading_diary\Drawn_charts\asdfasc\aafa\tmp')


# In[54]:





# In[55]:


login=5
os.makedirs(f'E:\Trading_diary\Drawn_charts\{login}')

"""