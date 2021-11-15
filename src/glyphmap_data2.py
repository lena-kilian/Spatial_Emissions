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
from datetime import datetime
import geopandas as gpd
import pickle


wd = r'/Users/lenakilian/Documents/Ausbildung/UoLeeds/PhD/Analysis/'
years = list(range(2007, 2018, 2))
geog = 'MSOA'

lookup = pd.read_csv(wd + 'data/raw/Geography/Conversion_Lookups/UK_full_lookup_2001_to_2011.csv')\
    [['MSOA11CD', 'MSOA01CD', 'RGN11NM']].drop_duplicates()


london_grid = gpd.read_file(wd + 'data/processed/GWR_data/london_grid_intersection_fixed.shp')\
    .merge(lookup.loc[lookup['RGN11NM'] == 'London'][['MSOA11CD', 'MSOA01CD']].drop_duplicates(), on='MSOA01CD')
msoa_area = london_grid.dissolve(by='MSOA11CD')[['geometry']]
msoa_area['area_msoa11cd'] = msoa_area.geometry.area
london_grid = london_grid.set_index('MSOA11CD').join(msoa_area[['area_msoa11cd']], how='left')
london_grid['area_split'] = london_grid.geometry.area

# id_shp = london_grid.dissolve(by='id') 
# id_shp = id_shp.join(id_shp.bounds)
# id_shp['area_grid'] = id_shp.geometry.area
# id_shp['width'] = id_shp['maxx'] - id_shp['minx']
# id_shp['height'] = id_shp['maxy'] - id_shp['miny']
# id_shp.to_file(wd + 'data/processed/GWR_data/london_grid.shp')
id_shp = gpd.read_file(wd + 'data/processed/GWR_data/london_grid.shp')

emissions = {}
for year in years:
    year_difference = years[1] - years[0]
    year_str = str(year) + '-' + str(year + year_difference - 1)
    emissions[year] = pd.read_csv(wd + 'data/processed/GHG_Estimates/' + geog + '_' + year_str + '.csv', index_col=0)

new_cat = {}
cat_dict = pd.read_excel(wd + '/data/processed/LCFS/Meta/lcfs_desc_anne&john.xlsx')
cats = cat_dict[['category']].drop_duplicates()['category']
cat_dict['ccp_code'] = [x.split(' ')[0] for x in cat_dict['ccp']]
cat_dict = dict(zip(cat_dict['ccp_code'], cat_dict['category_5']))
for year in years:
    new_cat[year] = emissions[year].rename(columns=cat_dict).sum(axis=1, level=0)
    if year in years and year < 2014:
        new_cat[year] = lookup[['MSOA11CD', 'MSOA01CD', 'RGN11NM']].drop_duplicates().set_index('MSOA01CD').join(new_cat[year]).set_index('MSOA11CD')
    else:
        new_cat[year] = lookup[['MSOA11CD', 'RGN11NM']].drop_duplicates().set_index('MSOA11CD').join(new_cat[year])
    new_cat[year] = new_cat[year].loc[new_cat[year]['RGN11NM'] == 'London']
    

# add to grid by weighted area    
idx = ['Private transport: other', 'Private transport: Petrol, diesel, motoring oils', 'Rail, bus transport', 'Air transport', 'Private transport: Rental, taxi', 'Water transport']

new_cat_shp = {}    
for year in years:
    print('\n', new_cat[year][['population']].sum())
    new_cat_shp[year] = london_grid.join(new_cat[year]).drop('geometry', axis=1).fillna(0)
    new_cat_shp[year][idx] = new_cat_shp[year][idx].apply(lambda x: x * new_cat_shp[year]['population'])
    
    new_cat_shp[year]['area_fraction'] = new_cat_shp[year]['area_split'] / new_cat_shp[year]['area_msoa11cd']
    new_cat_shp[year][idx + ['population']] = new_cat_shp[year][idx + ['population']].apply(lambda x: x * new_cat_shp[year]['area_fraction'])
    
    new_cat_shp[year] = new_cat_shp[year].groupby('id').sum()
    print(new_cat_shp[year][['population']].sum(skipna=True))
    new_cat_shp[year][idx] = new_cat_shp[year][idx].apply(lambda x: x / new_cat_shp[year]['population'])
    
    new_cat_shp[year] = id_shp[['geometry']].join(new_cat_shp[year][idx + ['population']])
    
    
for item in idx:
    new_cat_shp[year].plot(column=item); plt.title(item); plt.show()
"""   
all_data = id_shp.join(new_cat_shp[year].drop(['geometry', 'population'], axis=1).stack().reset_index(level=1).drop(0, axis=1))\
    .set_index('level_1', append=True)
for year in years:
    temp = new_cat_shp[year].drop(['geometry', 'population', 'new_area'], axis=1).stack().reset_index().set_index(['id', 'level_1'])
    temp.columns = ['y' + str(year)]
    all_data = all_data.join(temp)
"""

all_data = pd.DataFrame()
for year in years:
    temp = id_shp.join(new_cat_shp[year][idx + ['population']])
    temp['year'] = year
    all_data = all_data.append(temp)
all_data.drop(['area', 'new_area'], axis=1).to_file(wd + 'data/processed/GWR_data/london_grid_w_data.shp')

