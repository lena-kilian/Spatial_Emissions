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
import geopandas as gpd



wd = r'/Users/lenakilian/Documents/Ausbildung/UoLeeds/PhD/Analysis/'
years = list(range(2007, 2018, 2))
geog = 'MSOA'

dict_cat = 'category_6'

# set font globally
plt.rcParams.update({'font.family':'Times New Roman'})

# load region and 2001 to 2011 lookup
lookup = pd.read_csv(wd + 'data/raw/Geography/Conversion_Lookups/UK_full_lookup_2001_to_2011.csv')\
    [['MSOA11CD', 'MSOA01CD', 'RGN11NM']].drop_duplicates()
ew_shp = gpd.read_file(wd + 'data/raw/Geography/Shapefiles/EnglandWales/msoa_2011_ew.shp')\
    .set_index('msoa11cd').join(lookup.set_index('MSOA11CD'), how='left')
lon_shp = ew_shp.loc[ew_shp['RGN11NM'] == 'London']

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

london_data = all_data.loc[all_data['RGN11NM'] == 'London']
london_data['year_str'] = ['Y' + str(x) for x in london_data['year']]

g = sns.FacetGrid(london_data, col='year_str')
g.map(sns.scatterplot, 'Car/van purchases and motoring oils', 'Rail and bus')

# check for clusters of high and low
new_data = pd.DataFrame()
for year in years:
    temp = london_data.loc[london_data['year'] == year]
    
    temp['Car_median'] = 'below 25th percentile car emissions'
    temp.loc[temp['Car/van purchases and motoring oils'] > temp['Car/van purchases and motoring oils'].quantile(0.33), 'Car_median'] = 'above 25th percentile car emissions'

    temp['RB_median'] = 'Below 25th percentile rail and bus emissions'
    temp.loc[temp['Rail and bus'] > temp['Rail and bus'].quantile(0.33), 'RB_median'] = 'Above 25th percentile rail and bus emissions'
    
    new_data = new_data.append(temp)
    
summary = new_data.groupby(['year', 'Car_median', 'RB_median']).describe()[['Car/van purchases and motoring oils', 'Rail and bus']]

new_data['group'] = new_data['RB_median'] + ' & ' + new_data['Car_median']
my_cols = ['#12366E', '#65A5D0', '#CAE0EF', '#C54A43'] # '#6D0021', , '#F1B593'

from matplotlib.colors import LinearSegmentedColormap
my_cmap = LinearSegmentedColormap.from_list('name', my_cols)

new_data = lon_shp.join(new_data[['Car/van purchases and motoring oils', 'Rail and bus', 'group', 'year']])

for year in years:
    temp = new_data.loc[new_data['year'] == year]
    temp.plot(column='group', legend=True, cmap=my_cmap); plt.show() #color=temp['col']
    
new_data.loc[new_data['year'] == 2015].plot(column='group', legend=True, cmap=my_cmap); plt.show()

new_data['land transport'] = new_data['Car/van purchases and motoring oils'] + new_data['Rail and bus']
new_data.loc[new_data['year'] == 2015].plot(column='land transport', legend=True, cmap='RdBu'); plt.show() 








