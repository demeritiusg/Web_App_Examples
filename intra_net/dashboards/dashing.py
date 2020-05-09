from dash import Dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Output, Input
import pandas as pd
import mpld3
import matplotlib
import numpy as np

# TODO add a proper charts and graphs

def process_data():
    #this will load all the data and do the maths

    # TODO add html button
    df = pd.read_excel(r'C:\Users\Admin\PycharmProjects\untitled4\Copy of Funded Deals 2020.xlsx', index=False)

    df_pivot = pd.pivot_table(df, values=['Opportunity Name', 'Committed Amount'],  index=['Funded Month'], aggfunc={'Opportunity Name': len, 'Committed Amount': np.sum}, fill_value=0, margins=True)

    df_pivot2 = pd.pivot_table(df, values=['Opportunity Name', 'Committed Amount'],  index=['Opportunity Source'], aggfunc={'Opportunity Name': len, 'Committed Amount': np.sum}, fill_value=0, margins=True)

    df_pivot3 = pd.pivot_table(df, values=['Opportunity Name', 'Committed Amount'],  index=['State', 'Summary of Counties'], aggfunc={'Opportunity Name': len, 'Committed Amount': np.sum}, fill_value=0, margins=True)

    df_pivot = df_pivot[['Opportunity Name', 'Committed Amount']]

    df_pivot2 = df_pivot2[['Opportunity Name', 'Committed Amount']]

    df_pivot3 = df_pivot3[['Opportunity Name', 'Committed Amount']]

    html = df_pivot.to_html()
    print(html)
    # read_data_in
    return html


