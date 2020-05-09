from dash import Dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Output, Input
import pandas as pd
import mpld3
import matplotlib
from numpy.random import rand

# TODO add a proper charts and graphs

def process_data():
    # TODO this will load all the data and do the maths

    data = {'row_1': [3, 2, 1, 0], 'row_2': ['a', 'b', 'c', 'd']}

    df = pd.DataFrame.from_dict(data, orient='index')

    html = df.to_html()
    print(html)
    # read_data_in
    return html


