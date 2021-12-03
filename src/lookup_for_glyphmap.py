#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr  1 12:08:02 2021

@author: lenakilian
"""


import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import copy as cp
from datetime import datetime
import geopandas as gpd
import mapclassify
import random
import math

data_directory = "/Users/lenakilian/Documents/Ausbildung/UoLeeds/PhD/Analysis"

wd = r'/Users/lenakilian/Documents/Ausbildung/UoLeeds/PhD/Analysis/'
years = list(range(2007, 2018, 2))
geog = 'MSOA'

dict_cat = 'day_17'

lookup = pd.read_csv(wd + 'data/raw/Geography/Conversion_Lookups/UK_full_lookup_2001_to_2011.csv')\
    [['MSOA11CD', 'MSOA01CD', 'RGN11NM']].drop_duplicates()

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
        new_cat[year] = new_cat[year].join(lookup.set_index('MSOA01CD')).set_index('MSOA11CD')
    else:
        new_cat[year] = new_cat[year].join(lookup.set_index('MSOA11CD'))
    #new_cat[year] = new_cat[year].mean(axis=0, level=0)

data = {}
for year in years:
    data[year] = new_cat[year].loc[(new_cat[year]['RGN11NM'] != 'Scotland') & 
                                   (new_cat[year]['RGN11NM'] != 'Northern Ireland') & 
                                   (new_cat[year]['RGN11NM'] != 'Wales')] 

# load geog data to match with ghg (msoa level)
msoa_2011 = gpd.read_file(eval("r'" + data_directory + "/data/raw/Geography/Shapefiles/UK/msoa_2011_uk_all.shp'")).set_index('MSOA11CD')[['geometry']]
lookup = pd.read_csv(eval("r'" + data_directory + "/data/raw/Geography/Conversion_Lookups/UK_full_lookup_2001_to_2011.csv'"))
msoa_2011 = msoa_2011.join(lookup[['MSOA01CD', 'MSOA11CD', 'RGN11NM']].drop_duplicates().set_index('MSOA11CD')).reset_index().to_crs(epsg=3035)
uaa_lookup = pd.read_csv(eval("r'" + data_directory + "/data/raw/Geography/Conversion_Lookups/Output_Area_to_County_and_Unitary_Authority_(December_2019)_Lookup_in_England.csv'"))
uaa_lookup = uaa_lookup.merge(lookup[['OA11CD', 'MSOA11CD']], on='OA11CD', how='left')[['MSOA11CD', 'CTYUA19NM']].drop_duplicates()


# create lookup from grid data to LADs and UAAs
# load grid data
areas = gpd.read_file(eval("r'" + data_directory + "/data/processed/Geography/lad_grid.shp'"))[['area_nm']]
# load uaa and lad to msoa lookups
uaa_check = uaa_lookup[['CTYUA19NM']].drop_duplicates(); uaa_check['UAA_match'] = True
lad_check = lookup[['LAD17NM']].drop_duplicates(); lad_check['LAD_match'] = True

# clean strings and merge
uaa_check['UAA_nm'] = uaa_check['CTYUA19NM'].str.lower().str.replace(',', '').str.replace('city of', '').str.replace(' ', '')
areas['UAA_nm'] = areas['area_nm'].str.lower().str.replace(',', '').str.replace('city of', '').str.replace(' ', '')
lad_check['LAD_nm'] = lad_check['LAD17NM'].str.lower().str.replace(',', '').str.replace('city of', '').str.replace(' ', '')
areas['LAD_nm'] = areas['area_nm'].str.lower().str.replace(',', '').str.replace('city of', '').str.replace(' ', '')

areas = areas.merge(uaa_check, on='UAA_nm', how='left').merge(lad_check, on='LAD_nm', how='left')
# create lookup from msoa to grid
areas_lad = areas.loc[areas['LAD_match'] == True]
areas_uaa = areas.loc[(areas['UAA_match'] == True) & (areas['LAD_match'] != True)]

areas_lad = lookup[['MSOA11CD', 'LAD17NM']].drop_duplicates().merge(areas_lad[['area_nm', 'LAD17NM']], on='LAD17NM')
areas_uaa = uaa_lookup.merge(areas_uaa[['area_nm', 'CTYUA19NM']], on='CTYUA19NM')

grid_lookup = areas_lad[['MSOA11CD', 'area_nm']].append(areas_uaa[['MSOA11CD', 'area_nm']])

# combine years of ghg into one df
all_data = pd.DataFrame(columns= data[2007].columns.to_list() + ['year'])
for year in range(2007, 2018):
    temp = cp.copy(data[year])
    temp['year'] = year
    all_data = all_data.append(temp)
# match ghg to area data
all_data = all_data.join(grid_lookup.set_index('MSOA11CD'))





# aggregate from MSOA to area
to_agg = all_data.loc[:,'1.1.1.1':'12.5.3.5'].columns.tolist() + ['Income anonymised', 'total_ghg']
all_data[to_agg] = all_data[to_agg].apply(lambda x: x*all_data['population'])
all_data = all_data.groupby(['RGN11NM', 'area_nm', 'year']).sum()
all_data[to_agg] = all_data[to_agg].apply(lambda x: x/all_data['population'])

# add mean across years
mean = all_data[['total_ghg', 'population']]
mean['ghg_mean'] = mean['total_ghg'] * mean['population']
mean = mean.sum(axis=0, level=1)
mean['ghg_mean'] = mean['ghg_mean'] / mean['population']
all_data = all_data.join(mean[['ghg_mean']])

# aggregate products (coicop 1)
all_data.columns = [x.split('.')[0] for x in all_data.loc[:,'1.1.1.1':'12.5.3.5'].columns] + all_data.loc[:,'population':].columns.tolist()
all_data = all_data.sum(axis=1, level=0)

# save as csv
all_data.to_csv(r'/Users/lenakilian/Desktop/30daymaps/glyphmap_data_england.csv')
