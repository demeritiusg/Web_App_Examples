import pandas as pd
import numpy as np
from datetime import datetime
import xlsxwriter

product_name = ['gas', 'ngl', 'other', 'oil']
# uploaded file
file = r'C:\Users\Admin\Downloads\MILL_2020-03-30_0d8b925d15.csv'
writer = pd.ExcelWriter('volumes_report_wellanm.xlsx', engine='xlsxwriter', date_format='YYYY-MM')
sheet_name = 'Chart'

overall_df = pd.read_csv(file, parse_dates=['production_date', 'income_date'])
year_list = overall_df['production_date'].drop_duplicates().values.tolist()
income_year_list = overall_df['income_date'].drop_duplicates().values.tolist()
# pd.to_datetime(overall_df.productiondate)

year_list.sort(reverse=True)
income_year_list.sort(reverse=True)
yr = year_list[:13]
income_yr = income_year_list[:13]

df = overall_df[overall_df['production_date'].isin(yr)]
income_df = overall_df[overall_df['income_date'].isin(income_yr)]

col = income_df['normalized_well'].drop_duplicates().values.tolist()
df = df[df['normalized_well'].isin(col)]


for p in product_name:
    raw_df = df[df['simple_product_name'] == p]

    totals_rev_prod = df.groupby(['normalized_well', 'production_date'])['owner_net_value'].sum().reset_index()  # correct
    totals_rev_prod = totals_rev_prod.rename(columns={'owner_net_value': 'prod_month'}).round(0)

    totals_rev_acct = income_df.groupby(['normalized_well', 'income_date'])['owner_net_value'].sum().reset_index()  # correct
    totals_rev_acct = totals_rev_acct.rename(
        columns={'income_date': 'production_date', 'owner_net_value': 'acct_month'}).round(0)

vols_table = pd.pivot_table(df, values='resolved_owner_volume', index=['normalized_well', 'production_date'], columns='simple_product_name',
                            aggfunc=np.sum)
vols_table['gas_boe'] = vols_table['gas'] / 6
vols_table['oil_boe'] = vols_table['gas_boe'] + vols_table['oil']
vols_table['place_holder1'] = 62
vols_table['place_holder2'] = 3

price_table = pd.pivot_table(df, values='resolved_price', index=['normalized_well', 'production_date'], columns='simple_product_name',
                             aggfunc=np.mean).round(2).fillna('-')

df_pivot = vols_table.merge(price_table, on=['normalized_well', 'production_date']).reset_index().merge(totals_rev_prod,
                                                                                   on=['normalized_well', 'production_date']).merge(
    totals_rev_acct, on=['normalized_well', 'production_date']).fillna('-')

df_pivot['prod_date'] = df_pivot['production_date'].dt.strftime('%Y-%m')

df_pivot = df_pivot[['normalized_well', 'prod_date', 'prod_month', 'acct_month', 'oil_boe', 'oil_x',
                     'gas_x', 'gas_boe', 'ngl_x', 'other_x', 'place_holder1', 'place_holder2',
                     'oil_y', 'gas_y', 'ngl_y', 'other_y']]

df_pivot.to_excel(writer, index=False, header=False, startrow=29, startcol=1, sheet_name=sheet_name)

wb = writer.book
ws = writer.sheets[sheet_name]
###############################################################################
oil_gasboe_chart = wb.add_chart({'type': 'column'})
oil_gasboe_chart.add_series({'name': 'Oil',
                             'categories': '{}!$B30:B42'.format(sheet_name),
                             'values': '={}!$F$30:$F$42'.format(sheet_name),
                             'fill': {'color': '#4f81bd'},
                             'border': {'none': True}})
oil_gasboe_chart.add_series({'name': 'Gas BOE',
                             'values': '={}!$H$30:$H$42'.format(sheet_name),
                             'fill': {'color': '#a6a6a6'},
                             'border': {'none': True}})

oil_gasboe_chart.set_title({'name': 'Volumes by Production Month'})
oil_gasboe_chart.set_style(11)
oil_gasboe_chart.set_size({'width': 1476, 'height': 480})
oil_gasboe_chart.set_legend({'position': 'bottom'})
oil_gasboe_chart.set_y_axis({'line': {'none': True}})

# oil_gasboe_chart.set_plotarea({'border': {'none': True}})

wti_oil_price_chart = wb.add_chart({'type': 'line'})
wti_oil_price_chart.add_series({'name': 'WTI',
                                'values': '={}!$K$30:$K$42'.format(sheet_name),
                                'y2_axis': 70,
                                'line': {
                                    'color': '#9bbb59',
                                    'width': 2.25
                                }})
wti_oil_price_chart.add_series({'name': 'Oil Price',
                                'values': '={}!$M$30:$M$42'.format(sheet_name),
                                'y2_axis': 70,
                                'line': {
                                    'color': '#008000',
                                    'width': 2.25
                                }})
wti_oil_price_chart.add_series({'name': 'Nymex',
                                'values': '={}!$L$30:$L$42'.format(sheet_name),
                                'y2_axis': 70,
                                'line': {
                                    'color': '#ff5050',
                                    'width': 2.25
                                }})
wti_oil_price_chart.add_series({'name': 'Gas Price',
                                'values': '={}!$N$30:$N$42'.format(sheet_name),
                                'y2_axis': 70,
                                'line': {
                                    'color': '#c00000',
                                    'width': 2.25
                                }})
wti_oil_price_chart.set_y2_axis({'max': 70, 'line': {'none': True}})
oil_gasboe_chart.combine(wti_oil_price_chart)
ws.insert_chart('B2', oil_gasboe_chart)
oil_gasboe_chart.set_y2_axis

bold_format_cell = wb.add_format({'bold': True, 'border': True, 'valign': 'center'})
merge_cell_format = wb.add_format({'bold': True, 'border': True, 'valign': 'center'})
date_fromat = wb.add_format({'num_format': 'yyyy-mm', 'valign': 'center'})
currancy_format = wb.add_format({'num_format': '[$$-409]#,##0', 'valign': 'center'})
currancy_format_dec = wb.add_format({'num_format': '[$$-409]#,##0.00', 'valign': 'center'})
cell_format = wb.add_format({'num_format': '#,##0', 'valign': 'center'})

dflen = 30 + len(df_pivot)

ws.conditional_format('K30:L{}'.format(dflen), {'type': 'cell',
                                                'criteria': '>',
                                                'value': 0,
                                                'format': wb.add_format({'left': 1, 'right': 1})})

ws.conditional_format('B30:B{}'.format(dflen), {'type': 'no_blanks',
                                                'format': wb.add_format({'left': 1, 'right': 1})})

ws.conditional_format('B29:P29'.format(dflen), {'type': 'no_blanks',
                                                'format': wb.add_format({'border': 1})})

ws.conditional_format('D30:D{}'.format(dflen), {'type': 'no_blanks',
                                                'format': wb.add_format({'right': 1})})

ws.conditional_format('P30:P{}'.format(dflen), {'type': 'no_blanks',
                                                'format': wb.add_format({'right': 1})})

ws.conditional_format('B{}:P{}'.format(dflen, dflen), {'type': 'blanks',
                                                       'format': wb.add_format({'top': 1})})

ws.write('B29', 'Date', bold_format_cell)
ws.write('C29', 'Prod. Month', bold_format_cell)
ws.write('D29', 'Acct. Month', bold_format_cell)
ws.write('E29', 'Oil + Gas Boe', bold_format_cell)
ws.write('F29', 'Oil', bold_format_cell)
ws.write('G29', 'Gas', bold_format_cell)
ws.write('H29', 'Gas BOE', bold_format_cell)
ws.write('I29', 'NGL', bold_format_cell)
ws.write('J29', 'Other', bold_format_cell)
ws.write('K29', 'WTI', bold_format_cell)
ws.write('L29', 'Nymex', bold_format_cell)
ws.write('M29', 'Oil', bold_format_cell)
ws.write('N29', 'Gas', bold_format_cell)
ws.write('O29', 'NGL', bold_format_cell)
ws.write('P29', 'Other', bold_format_cell)
ws.merge_range('C28:D28', 'Revenue', merge_cell_format)
ws.merge_range('E28:J28', 'Volumes by Production Month', merge_cell_format)
ws.merge_range('K28:L28', 'Market Pricing', merge_cell_format)
ws.merge_range('M28:P28', 'Actual Pricing by Production Month', merge_cell_format)

ws.set_column('A:A', 2)
ws.set_column('B:B', 12, date_fromat)
ws.set_column('C:D', 14, currancy_format)
ws.set_column('E:J', 14, cell_format)
ws.set_column('K:L', 10, cell_format)
ws.set_column('M:P', 14, currancy_format_dec)

writer.save()

# TODO Get the api key for the pricing from EIA.gov
# returned returned file
print(df_pivot.head())
