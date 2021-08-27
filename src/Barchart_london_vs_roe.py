#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar  5 10:15:25 2021

@author: lenakilian
"""

import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import copy as cp
from matplotlib import cm
from matplotlib.lines import Line2D
from matplotlib import rc



wd = r'/Users/lenakilian/Documents/Ausbildung/UoLeeds/PhD/Analysis/'
years = list(range(2007, 2018, 2))
geog = 'MSOA'

dict_cat = 'category_6'

# set font globally
plt.rcParams.update({'font.family':'Times New Roman'})

# load region and 2001 to 2011 lookup
lookup = pd.read_csv(wd + 'data/raw/Geography/Conversion_Lookups/UK_full_lookup_2001_to_2011.csv')\
    [['MSOA11CD', 'MSOA01CD', 'RGN11NM']].drop_duplicates()

emissions = {}
for year in years:
    year_difference = years[1] - years[0]
    year_str = str(year) + '-' + str(year + year_difference - 1)
    emissions[year] = pd.read_csv(wd + 'data/processed/GHG_Estimates/' + geog + '_' + year_str + '.csv', index_col=0)

new_cat = {}
cat_dict = pd.read_excel(wd + '/data/processed/LCFS/Meta/lcfs_desc_anne&john.xlsx')
cats = cat_dict[['category']].drop_duplicates()['category']
cat_dict['ccp_code'] = [x.split(' ')[0] for x in cat_dict['ccp']]
cat_dict = dict(zip(cat_dict['ccp_code'], cat_dict[dict_cat]))
for year in years:
    new_cat[year] = emissions[year].rename(columns=cat_dict).sum(axis=1, level=0)

idx = new_cat[2017].columns.tolist(); idx.remove('other'); idx.remove('population')
#idx = ['Private transport: Petrol, diesel, motoring oils', 'Private transport: other', 
#       'Rail, bus transport', 'Air transport', 'Private transport: Rental, taxi', 'Water transport']

all_data = pd.DataFrame()
for year in years:
    if year < 2014:
        temp = cp.copy(new_cat[year]).join(lookup.set_index('MSOA01CD'))
    else:
        temp = cp.copy(new_cat[year]).join(lookup.set_index('MSOA11CD')[['RGN11NM']])
    temp['year'] = year
    temp = temp.loc[(temp['RGN11NM'] != 'Wales') & (temp['RGN11NM'] != 'Northern Ireland') & (temp['RGN11NM'] != 'Scotland')]
    temp['RGN'] = 'London'
    temp.loc[temp['RGN11NM'] != 'London', 'RGN'] = 'Rest of England'
    all_data = all_data.append(temp)


england_avg = cp.copy(all_data)
england_avg[idx] = england_avg[idx].apply(lambda x: x*england_avg['population'])
england_avg = england_avg.groupby(['year']).sum()
england_avg[idx] = england_avg[idx].apply(lambda x: x/england_avg['population'])


summary = cp.copy(all_data)
summary[idx] = summary[idx].apply(lambda x: x*summary['population'])
summary = summary.groupby(['year', 'RGN']).sum()
summary = summary[idx].apply(lambda x: x/summary['population'])

# make colourbar
#max_col = 200
#cmap = cm.get_cmap('RdBu')
#gap = int(max_col / (len(idx) - 1))
#my_cols =  [cmap(x) for x in list(range(0, max_col+1, gap))]
my_cols = ['#6D0021', '#C54A43', '#F1B593', '#CAE0EF', '#65A5D0', '#12366E'][:len(idx)]
# make barcharts
fig, axs = plt.subplots(nrows=1, ncols=2, sharey=True, figsize=(8,3))

# set font
#tnrfont = {'fontname':'Times New Roman'}

order = summary.T.sort_values((2017, 'Rest of England'), ascending=False).index.tolist()
order.remove('Other transport'); order.append('Other transport')
for i in range(2):
    area = ['London', 'Rest of England'][i]
    data = summary[order].T.swaplevel(axis=1)[[area]]
    start = [0 for x in years]
    for j in range(len(data.index.tolist())):
        item = data.index.tolist()[j]
        values = data.loc[item, :]
        axs[i].barh(width=values, y=[str(y) for y in years], left=start, color=my_cols[j])
        start += values
        if i == 0:
            print(item)
    axs[i].set_title(area)
    axs[i].set_xlim(0, 3.6)
    axs[i].set_xlabel('tCO$_{2}$e per capita')
    for j in range(3):
        axs[i].axvline(x=j+1, c='k', linestyle=':',  linewidth=0.75)
axs[0].invert_xaxis()
axs[0].yaxis.tick_right()
# make custom legend
legend_elements1 = []; legend_elements2 = []
for k in range(int(len(my_cols)/2)):
    legend_elements1.append(Line2D([k], [k], marker='o', color='w', label=data.index[k], markerfacecolor=my_cols[k], markersize=12))
    n = int(len(my_cols)/2) + k
    legend_elements2.append(Line2D([n], [n], marker='o', color='w', label=data.index[n], markerfacecolor=my_cols[n], markersize=12))    
axs[0].legend(handles=legend_elements1, loc='upper center', bbox_to_anchor=(0.6, -0.2), frameon=False)
axs[1].legend(handles=legend_elements2, loc='upper center', bbox_to_anchor=(0.5, -0.2), frameon=False)
plt.gca().invert_yaxis()
plt.savefig(wd + 'Spatial_Emissions/outputs/Graphs/Bar_Transport_London_vs_RoE_values.png', bbox_inches='tight', dpi=200)


# go by percentage
percent = summary.T.apply(lambda x: x/x.sum() * 100)
my_cols = ['#6D0021', '#C54A43', '#F1B593', '#CAE0EF', '#65A5D0', '#12366E'][:len(idx)]
# make barcharts
fig, axs = plt.subplots(nrows=1, ncols=2, sharey=True, figsize=(8,3))
for i in range(2):
    area = ['London', 'Rest of England'][i]
    data = percent.T[order].T.swaplevel(axis=1)[[area]]
    start = [0 for x in years]
    for j in range(len(data.index.tolist())):
        item = data.index.tolist()[j]
        values = data.loc[item, :]
        axs[i].barh(width=values, y=[str(y) for y in years], left=start, color=my_cols[j])
        start += values
        if i == 0:
            print(item)
    axs[i].set_title(area)
    axs[i].set_xlabel('% of tCO$_{2}$e per capita')
    #for j in [25, 50, 75]:
    #    axs[i].axvline(x=j, c='k', linestyle=':',  linewidth=0.75)
axs[0].invert_xaxis()
axs[0].yaxis.tick_right()
# make custom legend
legend_elements1 = []; legend_elements2 = []
for k in range(int(len(my_cols)/2)):
    legend_elements1.append(Line2D([k], [k], marker='o', color='w', label=data.index[k], markerfacecolor=my_cols[k], markersize=12))
    n = int(len(my_cols)/2) + k
    legend_elements2.append(Line2D([n], [n], marker='o', color='w', label=data.index[n], markerfacecolor=my_cols[n], markersize=12))    
axs[0].legend(handles=legend_elements1, loc='upper center', bbox_to_anchor=(0.6, -0.2), frameon=False)
axs[1].legend(handles=legend_elements2, loc='upper center', bbox_to_anchor=(0.5, -0.2), frameon=False)
plt.gca().invert_yaxis()
plt.savefig(wd + 'Spatial_Emissions/outputs/Graphs/Bar_Transport_London_vs_RoE_percent.png', bbox_inches='tight', dpi=200)



