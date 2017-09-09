from flask import Flask, render_template, request, redirect
from bokeh.plotting import figure, output_notebook, show
from bokeh.embed import components
import simplejson as json
import pandas as pd
import numpy as np
import requests

app = Flask(__name__)
app.vars = {}
INDEX_TITLE = 'Stock Ticker Demo'
COLORS = {'adj_close': 'darkblue',
          'adj_open': 'darkgreen',
          'close': 'lightblue',
          'open': 'lightgreen'}
TOOLS = 'pan, wheel_zoom, box_zoom, reset, save'

def request_info(ticker, query, hist):
    hist = min(hist, 120)
    query.append('date')
    
    today = str(np.datetime64('today', 'D'))
    start = str(np.datetime64('today', 'D') - np.timedelta64(hist, 'D'))
    
    keys = {'ticker': ticker, 'date.gte': start, 'date.lt': today,
            'qopts.columns': ','.join(query), 'api_key': 'BcQQP1z-ERr55WK5ZDxG'}

    r = requests.get('https://www.quandl.com/api/v3/datatables/WIKI/PRICES.json', params=keys)
    
    j = json.loads(r.text)
    cols = [d['name'] for d in j['datatable']['columns']]
    df = pd.DataFrame(j['datatable']['data'], columns=cols).set_index('date')
    
    if len(df) == 0:
        return None, None
    
    p = figure(tools=TOOLS, title='{} - Last {} Days'.format(ticker, hist),
           x_axis_label='Date', x_axis_type='datetime')
    for col in df.columns:
        p.line(pd.to_datetime(df.index), df[col], legend=col.title(), line_width=2, line_color=COLORS[col])

    title = '{} Quotes - Last {} Days'.format(ticker, hist)
    return p, title


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        errors = []
        app.vars['ticker'] = request.form.get('ticker')
        app.vars['hist'] = request.form.get('hist')
        app.vars['features'] = request.form.getlist('features')
        
        if len(app.vars['features']) == 0:
            errors.append('You must check at least one value.')
        if app.vars['ticker'] == '':
            errors.append('No company specified.')
        if not app.vars['hist'].isdigit():
            errors.append('Invalid history length.')
        if len(errors) > 0:
            return render_template('index.html', title=index_title, errors=errors)
        
        plot, title = request_info(app.vars['ticker'], app.vars['features'], int(app.vars['hist']))
        if plot is None:
            errors.append('No data exists for this company and date range.')
            return render_template('index.html', title=INDEX_TITLE, errors=errors)
        
        script, div = components(plot)
        return render_template('index.html', title=title, script=script, div=div)
    else:
        return render_template('index.html', title=INDEX_TITLE)

if __name__ == '__main__':
    app.run(port=33507)
