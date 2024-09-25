import pandas as pd
import numpy as np
from datetime import datetime
import xlsxwriter

"""
There is a lot of math going on in here that is more than likely wrong. Should fix it.
"""


pd.set_option('display.max_columns', 45)

# product_name = ['gas', 'ngl', 'other', 'oil']
# uploaded file
file = r'C:\Users\Admin\Downloads\MILL_2020-03-30_0d8b925d15.csv'
writer = pd.ExcelWriter('volumes_report_df.xlsx', engine='xlsxwriter', date_format='YYYY-MM')
sheet_name = 'sheet'

overall_df = pd.read_csv(file, parse_dates=['production_date', 'income_date']).sort_values(by='normalized_well').dropna(
    subset=['normalized_well'])
overall_df['filter_date'] = overall_df.production_date.dt.strftime('%Y')
# print(overall_df.columns.tolist())
income_year_list = overall_df['income_date'].drop_duplicates().values.tolist()
product_name = overall_df['simple_product_name'].drop_duplicates().values.tolist()
# pd.to_datetime(overall_df.productiondate)
print(product_name)
# income_year_list.sort(reverse=True)
# income_yr = income_year_list[:13]
# income_df = overall_df[overall_df['income_date'].isin(income_yr)]

pfc = overall_df.groupby(['normalized_well'])['production_date']
ifc = overall_df.groupby(['normalized_well'])['income_date']

overall_df['pmin'] = pfc.transform(min)
overall_df['imin'] = ifc.transform(min)

df = overall_df[overall_df['imin'] >= '2019-01-01']
income_df = overall_df[overall_df['imin'] >= '2019-01-01']

print(df['simple_product_name'].drop_duplicates().values.tolist())
print(income_df['simple_product_name'].drop_duplicates().values.tolist())
# print(df.sort_values(by='min'))
# col = df['normalized_well'].drop_duplicates().values.tolist()
# df = df[df['normalized_well'].isin(col)]

# for c in col:
#     raw_df = df[df['normalized_well'] == c]
#     # print(df.head())
# for p, c in zip(product_name, col):
#     # print(p)
#     # raws = raw_df.filter()
#     try:
#         raws = df[df.apply(lambda x: x.get('simple_product_name', default=0) == p or x['normalized_well'] == c, axis=1)]
#     except:
#         pass
# raws = overall_df[overall_df.apply(lambda x: x.normalized_well == c or x.simple_product_name == p, axis=1)]
# print(raws)
# print(df)

totals_rev_prod = df.groupby(['normalized_well', 'production_date'])[
    'owner_net_value'].sum().reset_index()  # correct
totals_rev_prod = totals_rev_prod.rename(columns={'owner_net_value': 'prod_month'}).fillna('-')

totals_rev_acct = income_df.groupby(['normalized_well', 'income_date'])[
    'owner_net_value'].sum().reset_index()  # correct
totals_rev_acct = totals_rev_acct.rename(
    columns={'income_date': 'income_date', 'owner_net_value': 'acct_month'}).round(0).fillna('-')
# print(totals_rev_acct.columns.tolist())
# print(totals_rev_prod.columns.tolist())


vols_table = pd.pivot_table(df, values='resolved_owner_volume', index=['normalized_well', 'production_date'],
                            columns='simple_product_name',
                            aggfunc=np.sum)
vols_table['gas_boe'] = vols_table.get('gas', default=0) / 6
vols_table['oil_boe'] = vols_table.get('gas_boe', default=0) + vols_table.get('oil', default=0)
vols_table['place_holder1'] = 62
vols_table['place_holder2'] = 3

# tbl = vols_table.columns.tolist()
# print(vols_table.columns.tolist())
# new = list(set(tbl) - set(product_name))

price_table = pd.pivot_table(df, values='resolved_price', index=['normalized_well', 'production_date'],
                             columns='simple_product_name',
                             aggfunc=np.mean).round(2).fillna('-')

# price_table['oil'] = 0
# print(price_table.columns.tolist())
df_piv = vols_table.merge(price_table, on=['normalized_well', 'production_date']).reset_index().merge(totals_rev_prod,
                                                                                                      on=[
                                                                                                          'normalized_well',
                                                                                                          'production_date']).fillna('-')

df_pivot = df_piv.merge(totals_rev_acct, left_on=['normalized_well', 'production_date'],
                        right_on=['normalized_well', 'income_date'], how= 'left')

print(df_piv)
df_pivot['prod_date'] = df_pivot['production_date'].dt.strftime('%Y-%m')
df_pivot.fillna('-', inplace=True)
# # tbl = []
# # tbl.append(product_name)
df_pivot = df_pivot[['normalized_well', 'prod_date', 'prod_month', 'acct_month', 'oil_boe', 'oil_x',
                     'gas_x', 'gas_boe', 'ngl_x', 'other_x',
                     'oil_y', 'gas_y', 'ngl_y', 'other_y']]
# print(df_pivot)
# # print(df_pivot.head())
#
df_pivot.to_excel(writer, index=False, header=False, startrow=3, startcol=1, sheet_name=sheet_name)

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
# oil_gasboe_chart.combine(wti_oil_price_chart)
# ws.insert_chart('B2', oil_gasboe_chart)
# oil_gasboe_chart.set_y2_axis

bold_format_cell = wb.add_format({'bold': True, 'border': True, 'valign': 'center'})
merge_cell_format = wb.add_format({'bold': True, 'border': True, 'valign': 'center'})
date_fromat = wb.add_format({'num_format': 'yyyy-mm', 'valign': 'center'})
currancy_format = wb.add_format({'num_format': '[$$-409]#,##0', 'valign': 'center'})
currancy_format_dec = wb.add_format({'num_format': '[$$-409]#,##0.00', 'valign': 'center'})
cell_format = wb.add_format({'num_format': '#,##0', 'valign': 'center'})

dflen = 4 + len(df_pivot)

# ws.conditional_format('K5:L{}'.format(dflen), {'type': 'cell',
#                                                 'criteria': '>',
#                                                 'value': 0,
#                                                 'format': wb.add_format({'left': 1, 'right': 1})})

# ws.conditional_format('B5:D{}'.format(dflen), {'type': 'no_blanks',
#                                                'format': wb.add_format({'left': 1, 'right': 1})})

ws.conditional_format('B4:O{}'.format(dflen), {'type': 'no_blanks',
                                              'format': wb.add_format({'border': 1})})

# ws.conditional_format('D4:D{}'.format(dflen), {'type': 'no_blanks',
#                                                'format': wb.add_format({'right': 1})})

# ws.conditional_format('O5:O{}'.format(dflen), {'type': 'no_blanks',
#                                                'format': wb.add_format({'right': 1})})

# ws.conditional_format('C{}:O{}'.format(dflen, dflen), {'type': 'blanks',
#                                                        'format': wb.add_format({'top': 1})})

# ws.write('B3', 'Well Name', bold_format_cell)
# ws.write('B3', 'Well Name', bold_format_cell)
ws.write('D3', 'Prod. Month', bold_format_cell)
ws.write('E3', 'Acct. Month', bold_format_cell)
ws.write('F3', 'Oil + Gas Boe', bold_format_cell)
ws.write('G3', 'Oil', bold_format_cell)
ws.write('H3', 'Gas', bold_format_cell)
ws.write('I3', 'Gas BOE', bold_format_cell)
ws.write('J3', 'NGL', bold_format_cell)
ws.write('K3', 'Other', bold_format_cell)
# ws.write('K3', 'WTI', bold_format_cell)
# ws.write('L3', 'Nymex', bold_format_cell)
ws.write('L3', 'Oil', bold_format_cell)
ws.write('M3', 'Gas', bold_format_cell)
ws.write('N3', 'NGL', bold_format_cell)
ws.write('O3', 'Other', bold_format_cell)
ws.merge_range('B2:B3', 'Well Name', merge_cell_format)
ws.merge_range('C2:C3', 'Month', merge_cell_format)
ws.merge_range('D2:E2', 'Revenue', merge_cell_format)
ws.merge_range('F2:J2', 'Volumes by Production Month', merge_cell_format)
# ws.merge_range('K2:L2', 'Market Pricing', merge_cell_format)
ws.merge_range('K2:O2', 'Actual Pricing by Production Month', merge_cell_format)

ws.set_column('A:A', 2)
ws.set_column('B:B', 40, date_fromat)
ws.set_column('C:C', 14, cell_format)
ws.set_column('D:E', 14, currancy_format)
ws.set_column('F:K', 14, cell_format)
ws.set_column('L:O', 14, currancy_format_dec)

writer.save()

# TODO Get the api key for the pricing from EIA.gov
# returned returned file
# print(df_pivot.head())
