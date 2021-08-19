#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar  5 10:15:25 2021

@author: lenakilian
"""

import pandas as pd
import copy as cp
import geopandas as gpd


wd = r'/Users/lenakilian/Documents/Ausbildung/UoLeeds/PhD/Analysis/'
years = list(range(2007, 2018, 2))
geog = 'MSOA'

dict_cat = 'category_6'

lookup = pd.read_csv(wd + 'data/raw/Geography/Conversion_Lookups/UK_full_lookup_2001_to_2011.csv')\
    [['MSOA11CD', 'MSOA01CD', 'RGN11NM']].drop_duplicates()

# add extra variabled to grid
splits = gpd.read_file(wd + 'data/processed/GWR_data/london_grid_intersection_fixed.shp')
splits['area_split'] = splits['geometry'].area
temp = splits.dissolve('MSOA01CD')
temp['area_msoa1'] = temp['geometry'].area
splits = splits.set_index('MSOA01CD').join(temp[['area_msoa1']]).reset_index()

grid = splits.dissolve('id')
grid['miny'] = grid.bounds.miny
grid['maxy'] = grid.bounds.maxy
grid['minx'] = grid.bounds.minx
grid['maxx'] = grid.bounds.maxx
grid['height'] = grid['maxx'] - grid['minx']
grid['width'] = grid['maxy'] - grid['miny']


# import emissions
emissions = {}
for year in years:
    year_difference = years[1] - years[0]
    year_str = str(year) + '-' + str(year + year_difference - 1)
    emissions[year] = pd.read_csv(wd + 'data/processed/GHG_Estimates/' + geog + '_' + year_str + '.csv', index_col=0)

new_cat = {}
cat_dict = pd.read_excel(wd + '/data/processed/LCFS/Meta/lcfs_desc_anne&john.xlsx')
cats = cat_dict[['category']].drop_duplicates()['category']
cat_dict['ccp_code'] = [x.split(' ')[0] for x in cat_dict['ccp']]

idx = cat_dict[[dict_cat]].drop_duplicates()[dict_cat].tolist(); idx.remove('other')

cat_dict = dict(zip(cat_dict['ccp_code'], cat_dict[dict_cat]))
for year in years:
    new_cat[year] = emissions[year].rename(columns=cat_dict).sum(axis=1, level=0)
    if year < 2014:
        new_cat[year] = new_cat[year].join(lookup.set_index('MSOA01CD'))
    else:
        new_cat[year] = new_cat[year].join(lookup.set_index('MSOA11CD')).set_index('MSOA01CD')
    new_cat[year] = new_cat[year].mean(axis=0, level=0)
    new_cat[year] = splits.set_index('MSOA01CD').join(new_cat[year], how='left')

# calculate emissions for grid
#idx = ['Private transport: Petrol, diesel, motoring oils', 'Private transport: other', 
#       'Rail, bus transport', 'Air transport', 'Private transport: Rental, taxi', 'Water transport']

grid_emissions = pd.DataFrame()
for year in years:
    temp = cp.copy(new_cat[year])
    temp[idx] = temp[idx].apply(lambda x: x*temp['population'])
    temp['area_prop'] = temp['area_split'] / temp['area_msoa1']
    temp[idx + ['population']] = temp[idx + ['population']].apply(lambda x: x*temp['area_prop'])
    temp = temp.fillna(0).groupby('id').sum()
    temp[idx] = temp[idx].apply(lambda x: x/temp['population'])
    temp['year'] = year
    temp = grid[['geometry', 'area', 'new_area', 'area_split', 'miny', 'maxy', 'minx', 'maxx', 'height', 'width']]\
        .join(temp[idx + ['population', 'year']])
    grid_emissions = grid_emissions.append(temp)

#new_idx = ['Priv_petrol', 'Priv_other', 'Rail_bus', 'Air', 'Priv_Rental', 'Water']
#grid_emissions = grid_emissions.rename(columns=dict(zip(idx, new_idx)))

grid_emissions.to_file(wd + 'data/processed/GWR_data/london_grid_w_data_newcats.shp')