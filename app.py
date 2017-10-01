from flask import Flask, render_template, request
from bokeh.plotting import figure
from bokeh.embed import components
import simplejson as json
import pandas as pd
import numpy as np
import requests

app = Flask(__name__)
QUANDL_URL = 'https://www.quandl.com/api/v3/datatables/WIKI/PRICES.json'
QUANDL_KEY = open('API.txt').read()
INDEX_TITLE = 'Stock Ticker Demo'
COLOR = {'adj_close': 'darkblue',
         'adj_open': 'darkgreen',
         'close': 'lightblue',
         'open': 'lightgreen'}
DESC = {'adj_close': 'Adj. Closing Price',
        'adj_open': 'Adj. Opening Price',
        'close': 'Closing Price',
        'open': 'Opening Price'}
TOOLS = 'pan, wheel_zoom, box_zoom, reset, save'

def request_info(ticker, query, hist):
    today = str(np.datetime64('today', 'D'))
    start = str(np.datetime64('today', 'D') - np.timedelta64(hist, 'D'))

    keys = {'ticker': ticker,
            'date.gte': start,
            'date.lt': today,
            'qopts.columns': ','.join(query),
            'api_key': 'BcQQP1z-ERr55WK5ZDxG'}

    r = requests.get(QUANDL_URL, params=keys)
    j = json.loads(r.text)
    cols = [d['name'] for d in j['datatable']['columns']]
    df = pd.DataFrame(j['datatable']['data'], columns=cols).set_index('date')

    if len(df) == 0:
        return None, None

    p = figure(tools=TOOLS, title='{} - Last {} Days'.format(ticker, hist),
               x_axis_label='Date', x_axis_type='datetime', responsive=True)

    for col in df.columns:
        p.line(pd.to_datetime(df.index), df[col], legend=DESC[col],
               line_color=COLOR[col], line_width=1)

    p.legend.location = 'bottom_right'

    page_title = '{} Quotes - Last {} Days'.format(ticker, hist)
    return p, page_title


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():
    if request.method != 'POST':
        return render_template('index.html', title=INDEX_TITLE)

    errors = []
    notices = []
    ticker = request.form.get('ticker')
    hist = request.form.get('hist')
    query = request.form.getlist('features')

    # Error Checking
    if ticker == '':
        errors.append('No company specified.')
    if not hist.isdigit():
        errors.append('Invalid history length.')
    if not query:
        errors.append('You must check at least one value.')
    if errors:
        return render_template('index.html', title=INDEX_TITLE,
                               errors=errors)

    query.append('date')
    hist = int(hist)
    if hist > 180:
        notices.append('Note: Only displaying last 180 days.')
        hist = 180

    plot, page_title = request_info(ticker, query, hist)

    if plot is None:
        errors.append('No data exists for this company and date range.')
        return render_template('index.html', title=INDEX_TITLE,
                               errors=errors)

    script, div = components(plot)
    return render_template('index.html', title=page_title,
                           script=script, div=div, notices=notices)

if __name__ == '__main__':
    app.run(port=33507)
