#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun  28

@author: lenakilian
"""

import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import geopandas as gpd
from statsmodels.stats.weightstats import DescrStatsW
from sklearn.preprocessing import MinMaxScaler
import matplotlib.patches as mpatches

wd = r'/Users/lenakilian/Documents/Ausbildung/UoLeeds/PhD/Analysis/'

data = gpd.read_file(wd + 'data/processed/GWR_data/gwr_data_london_2015.shp')

data['total_income'] = data['income'] * data['population'] / 1000
data['total_work'] = data['total_work'] * 10
data['lim_pc'] = 100 - data['not_lim_pc']

# build the scaler model
scaler = MinMaxScaler(); scaler.fit(data[['AI2015_ln']])
# fit using the train set
data[['AI2015_ln_sc']] = scaler.transform(data[['AI2015_ln']]) * 100


var_list = ['total_income', 'total_work']
msoa_vars = ['AI2015_ln_sc', 'AI2015_ln', 'pop_65+_pc', 'pop_14-_pc', 'bame_pct', 'lim_pc']
transport = ['Car/van pu', 'Flights', 'Rail', 'Bus', 'Combined f', 'Other tran',]

var_dict = ['Car/van\npurchases and\nmotoring oils', 'Flights', 'Rail', 'Bus', 'Combined\nfares', 'Other\ntransport',
            
            'Weekly Income\n(1,000 GBP)', 'Distance to\nworkplace\n(100 km)',
            
            'Public Trans-\nport Density (scaled)', 'Public Trans-\nport Density', 
            'Pop. aged\n≥65 (%)', 'Pop. aged\n≤14 (%)', 
            'Pop. identifying\nas BAME (%)', 'Pop. limited\nin day-to-day\nactivities (%)']
new_dict = [x.replace('\n', ' ') for x in var_dict]
var_dict = dict(zip(transport + var_list + msoa_vars, var_dict))


means = pd.DataFrame(data[transport + var_list].sum() / data['population'].sum())
means.columns = ['mean']
means['std'] = np.nan

for item in var_list + transport:
    data['temp'] = data[item] / data['population']
    means.loc[item, 'std'] = DescrStatsW(data['temp'], weights=data['population'], ddof=1).std
    
temp = data[msoa_vars + ['population']].describe().loc[['mean', 'std']].T
means = means.append(temp)

temp = data[transport + var_list + msoa_vars + ['population']]
temp[transport + var_list] = temp[transport + var_list].apply(lambda x:x/temp['population'])

temp = temp.describe().loc[['min', 'max']].T

means = means.join(temp)

# barchart with weighted means and SDs

my_cols = ['#C54A43', '#C54A43', '#F1B593']
fig, axs = plt.subplots(nrows=1, ncols=3, figsize=(11,2.5), 
                        gridspec_kw={'width_ratios': [len(transport), len(var_list), len(msoa_vars)]})
for i in range(3):
    item = [transport, var_list, msoa_vars][i]
    temp = means.loc[item].reset_index()
    temp['index'] = temp['index'].map(var_dict)
    sns.barplot(ax=axs[i], data=temp, x='index', y='mean', ci='std', color=my_cols[i], edgecolor='k')
    axs[i].errorbar(x=temp['index'], y=temp['mean'], yerr=temp['std'], fmt='none', c='black', capsize = 2)
    axs[i].set_xticklabels(axs[i].xaxis.get_majorticklabels(), rotation=90)
    axs[i].set_xlabel('')
axs[0].set_ylabel('tCO$_{2}$e / capita')
axs[1].set_ylabel('Value / capita')
axs[2].set_ylabel('Value (scaled 0-100)')

legend_elements1 = mpatches.Patch(color='#C54A43', label='Mean Weighted by population')
legend_elements2 = mpatches.Patch(color='#F1B593', label='MSOA Mean')
axs[0].legend(handles=[legend_elements1], bbox_to_anchor=(1.4, -0.5), frameon=False)
axs[1].legend(handles=[legend_elements2], bbox_to_anchor=(1.8, -0.5), frameon=False)

plt.savefig(wd + 'Spatial_Emissions/outputs/Graphs/Bar_London_descriptives.png', bbox_inches='tight', dpi=200)

# only emissions
fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(8, 4))
temp = means.loc[transport].reset_index()
temp['index'] = temp['index'].map(var_dict)
sns.barplot(ax=ax, data=temp, y='index', x='mean', color='#C54A43', edgecolor='k')
ax.errorbar(y=temp['index'], x=temp['mean'], xerr=temp['std'], fmt='none', c='black', capsize = 2)
#ax.set_xticklabels(axs[i].xaxis.get_majorticklabels(), rotation=90)
ax.set_ylabel('')
ax.set_xlabel('tCO$_{2}$e / capita')
plt.savefig(wd + 'Spatial_Emissions/outputs/Graphs/Bar_London_descriptives_emissions.png', bbox_inches='tight', dpi=200)


means_summary = means.rename(index=dict(zip(transport + var_list + msoa_vars, new_dict))).T


# get ptal summary
ptal = data[['AI2015', 'PTAL2015', 'AI2015_ln']].groupby('PTAL2015').describe()\
    .swaplevel(axis=1)[['min', 'max']]
