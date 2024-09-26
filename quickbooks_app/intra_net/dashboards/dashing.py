#for deletion

from dash import Dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Output, Input
import pandas as pd
import mpld3
import matplotlib
import numpy as np

# TODO add map.py and image_parse.py to this file.

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

    # read_data_in
    return html


############################################################################################################################
# work from map.py
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap as Basemap
from matplotlib.colors import rgb2hex, Normalize
from matplotlib.patches import Polygon
from matplotlib.colorbar import ColorbarBase

import pandas as pd

fig, ax = plt.subplots()

# Lambert Conformal map of lower 48 states.
m = Basemap(llcrnrlon=-119, llcrnrlat=20, urcrnrlon=-64, urcrnrlat=49,
            projection='lcc', lat_1=33, lat_2=45, lon_0=-95)

# Mercator projection, for Alaska and Hawaii
m_ = Basemap(llcrnrlon=-190, llcrnrlat=20, urcrnrlon=-143, urcrnrlat=46,
             projection='merc', lat_ts=20)  # do not change these numbers

# %% ---------   draw state boundaries  ----------------------------------------
## data from U.S Census Bureau
## http://www.census.gov/geo/www/cob/st2000.html
shp_info = m.readshapefile('st99_d00', 'states', drawbounds=True,
                           linewidth=0.45, color='gray')
shp_info_ = m_.readshapefile('st99_d00', 'states', drawbounds=False)

new_order = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October',
             'November', 'December']

df = pd.read_excel(r'C:\Users\Admin\PycharmProjects\untitled2\Copy of Funded Deals 2020.xlsx')
df['Funded Month'] = pd.Categorical(df['Funded Month'], categories=new_order, ordered=True)
df_pivot = pd.pivot_table(df, values=['Committed Amount'], index=['Funded Month'],
                          aggfunc={'Committed Amount': np.sum}, fill_value=0)

cm_pivot = pd.pivot_table(df, values=['Committed Amount'], index=['State'],
                          aggfunc={'Committed Amount': np.sum}, fill_value=0)
cm_pivot.reset_index(inplace=True)

## population density by state from
## http://en.wikipedia.org/wiki/List_of_U.S._states_by_population_density
popdensity1 = dict(zip(cm_pivot['State'], cm_pivot['Committed Amount']))
popdensity2 = {
    'New Jersey': 0,
    'Rhode Island': 0,
    'Massachusetts': 0,
    'Connecticut': 0,
    'Maryland': 0,
    'New York': 0,
    'Delaware': 0,
    'Florida': 0,
    'Ohio': 0,
    'Pennsylvania': 0,
    'Illinois': 0,
    'California': 0,
    'Hawaii': 0,
    'Virginia': 0,
    'Michigan': 0,
    'Indiana': 0,
    'North Carolina': 0,
    'Georgia': 0,
    'Tennessee': 0,
    'New Hampshire': 0,
    'South Carolina': 0,
    'Louisiana': 0,
    'Kentucky': 0,
    'Wisconsin': 0,
    'Washington': 0,
    'Alabama': 0,
    'Missouri': 0,
    'Texas': 0,
    'West Virginia': 0,
    'Vermont': 0,
    'Minnesota': 0,
    'Mississippi': 0,
    'Iowa': 0,
    'Arkansas': 0,
    'Oklahoma': 0,
    'Arizona': 0,
    'Colorado': 0,
    'Maine': 0,
    'Oregon': 0,
    'Kansas': 0,
    'Utah': 0,
    'Nebraska': 0,
    'Nevada': 0,
    'Idaho': 0,
    'New Mexico': 0,
    'South Dakota': 0,
    'North Dakota': 0,
    'Montana': 0,
    'Wyoming': 0,
    'Alaska': 0}
popdensity = {**popdensity2, **popdensity1}
# %% -------- choose a color for each state based on population density. -------
colors = {}
statenames = []
cmap = plt.cm.Blues  # use 'reversed hot' colormap
vmin = 0;
vmax = 120000  # set range.
norm = Normalize(vmin=vmin, vmax=vmax)
for shapedict in m.states_info:
    statename = shapedict['NAME']
    # skip DC and Puerto Rico.
    if statename not in ['District of Columbia', 'Puerto Rico']:
        pop = popdensity[statename]
        # calling colormap with value between 0 and 1 returns
        # rgba value.  Invert color range (hot colors are high
        # population), take sqrt root to spread out colors more.
        colors[statename] = cmap(np.sqrt((pop - vmin) / (vmax - vmin)))[:3]
    statenames.append(statename)

# %% ---------  cycle through state names, color each one.  --------------------
for nshape, seg in enumerate(m.states):
    # skip DC and Puerto Rico.
    if statenames[nshape] not in ['Puerto Rico', 'District of Columbia']:
        color = rgb2hex(colors[statenames[nshape]])
        # label = (CS=statenames[nshape], fmt='%2.1f', colors='w', fontsize=14)
        poly = Polygon(seg, facecolor=color, edgecolor=color)
        ax.add_patch(poly)

AREA_1 = 0.005  # exclude small Hawaiian islands that are smaller than AREA_1
AREA_2 = AREA_1 * 30.0  # exclude Alaskan islands that are smaller than AREA_2
AK_SCALE = 0.19  # scale down Alaska to show as a map inset
HI_OFFSET_X = -1900000  # X coordinate offset amount to move Hawaii "beneath" Texas
HI_OFFSET_Y = 250000  # similar to above: Y offset for Hawaii
AK_OFFSET_X = -250000  # X offset for Alaska (These four values are obtained
AK_OFFSET_Y = -750000  # via manual trial and error, thus changing them is not recommended.)

for nshape, shapedict in enumerate(m_.states_info):  # plot Alaska and Hawaii as map insets
    if shapedict['NAME'] in ['Alaska', 'Hawaii']:
        seg = m_.states[int(shapedict['SHAPENUM'] - 1)]
        if shapedict['NAME'] == 'Hawaii' and float(shapedict['AREA']) > AREA_1:
            seg = [(x + HI_OFFSET_X, y + HI_OFFSET_Y) for x, y in seg]
            color = rgb2hex(colors[statenames[nshape]])
        elif shapedict['NAME'] == 'Alaska' and float(shapedict['AREA']) > AREA_2:
            seg = [(x * AK_SCALE + AK_OFFSET_X, y * AK_SCALE + AK_OFFSET_Y) \
                   for x, y in seg]
            color = rgb2hex(colors[statenames[nshape]])
        poly = Polygon(seg, facecolor=color, edgecolor='gray', linewidth=.45)
        ax.add_patch(poly)

# ax.set_title('United states population density by state')

# %% ---------  Plot bounding boxes for Alaska and Hawaii insets  --------------
# light_gray = [0.8] * 3  # define light gray color RGB
# x1, y1 = m_([-190, -183, -180, -180, -175, -171, -171], [29, 29, 26, 26, 26, 22, 20])
# x2, y2 = m_([-180, -180, -177], [26, 23, 20])  # these numbers are fine-tuned manually
# m_.plot(x1, y1, color=light_gray, linewidth=0.8)  # do not change them drastically
# m_.plot(x2, y2, color=light_gray, linewidth=0.8)

# %% ---------   Show color bar  ---------------------------------------
ax_c = fig.add_axes([0.9, 0.66, 0.01, 0.19])

cb = ColorbarBase(ax_c, cmap=cmap, norm=norm, orientation='vertical', ticks=[vmin, vmax])

plt.show()

#####################################################################################################################################
# work from image_parse
# from PIL import Image
# src_im = Image.open("C:/Users/Admin/Documents/My Tableau Repository/Shapes/Airplane/plane.png")
# im = src_im.convert('RGBA')
# for i in range(36):
#     rot = im.rotate(i*10)
#     rot.save('C:/Users/Admin/Documents/My Tableau Repository/Shapes/Airplane/'+str(i*10).zfill(3)+"plane.png")


import matplotlib.table as pyt
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

###########################################################################################################################################################
# Bar and Line chart

new_order = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']

df = pd.read_excel(r'C:\Users\Admin\PycharmProjects\untitled2\Copy of Funded Deals 2020.xlsx')
df['Funded Month'] = pd.Categorical(df['Funded Month'], categories=new_order, ordered=True)
df_pivot = pd.pivot_table(df, values=['Opportunity Name', 'Committed Amount'],  index=['Funded Month'], aggfunc={'Opportunity Name': len, 'Committed Amount': np.sum}, fill_value=0)

color1 = 'tab:grey'
color2 = 'tab:orange'
fig, bar = plt.subplots()

bar = df_pivot['Opportunity Name'].plot.bar(color=color1, figsize=(10, 6), ylim=(0, round((df_pivot['Opportunity Name'].values.max()+6), 0)))
bar_labels = bar.get_xticklabels()
plt.setp(bar_labels, rotation=0, horizontalalignment='center')

bar.tick_params(axis='y')
line = bar.twinx()

line = df_pivot['Committed Amount'].plot.line(color=color2, figsize=(10, 6), ylim=(0, round((df_pivot['Committed Amount'].values.max()+200000), 0)))
line.tick_params(axis='y')

# print(type(line))

fig.tight_layout()

for p in bar.patches:
    height = p.get_height()  # height of each bar in the chart
    bar.annotate('{}'.format(height), xy=(p.get_x()+p.get_width()/2, height), xytext=(0, 3), textcoords='offset points', ha='center', va='bottom')

df_pivot.reset_index(inplace=True)
c = 0
for y in df_pivot['Committed Amount']:
    label = '${:0,.0f}'.format(y)
    print(c, y)
    line.annotate(label, xy=(c, y), textcoords='offset points', xytext=(30, 4), ha='left', arrowprops=dict(facecolor='black', arrowstyle='->'))
    c += 1

plt.show()

###################################################################################################################################################################
# Country chart

from mpl_toolkits.basemap import Basemap as Basemap
from matplotlib.colors import rgb2hex
from matplotlib.patches import Polygon


m = Basemap(llcrnrlon=-119, llcrnrlat=22, urcrnrlon=-64, urcrnrlat=49,
            projection='lcc', lat_1=33, lat_2=45, lon_0=-95)
shp_info = m.readshapefile('st99_d00', 'states', drawbounds=True)

cm_pivot = pd.pivot_table(df, values=['Opportunity Name', 'Committed Amount'],  index=['State'], aggfunc={'Opportunity Name': len, 'Committed Amount': np.sum}, fill_value=0)
cm_pivot.reset_index(inplace=True)

colors = {}
statenames = []
cm = plt.cm.hot
vmin = 0
vmax = 450  # set range.
for shapedict in m.states_info:
    statename = shapedict['NAME']
    # skip DC and Puerto Rico.
    if statename not in ['District of Columbia', 'Puerto Rico']:
        pop = cm_pivot.state
        # calling colormap with value between 0 and 1 returns
        # rgba value.  Invert color range (hot colors are high
        # population), take sqrt root to spread out colors more.
        colors[statename] = cm(1.-np.sqrt((pop-vmin)/(vmax-vmin)))[:3]
    statenames.append(statename)
# cycle through state names, color each one.
ax = plt.gca()  # get current axes instance
for nshape, seg in enumerate(m.states):
    # skip DC and Puerto Rico.
    if statenames[nshape] not in ['District of Columbia', 'Puerto Rico']:
        color = rgb2hex(colors[statenames[nshape]])
        poly = Polygon(seg, facecolor=color, edgecolor=color)
        ax.add_patch(poly)
plt.show()


