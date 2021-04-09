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

data_directory = "/Users/lenakilian/Documents/Ausbildung/UoLeeds/PhD/Analysis/Spatial_Emissions"

# import mean income data to adjust incomes for inflation (using 2019 for adjustment)
income_equivalised = pd.read_excel(eval("r'" + data_directory + "/data/raw/Mean_Income_Equivalised.xls'"), header=6).dropna(how='any')
income_equivalised.loc[income_equivalised['year'].str.contains('/'), 'year'] = income_equivalised['year'].str.split('/').str[0]
income_equivalised = income_equivalised.astype(int).set_index('year')

# import ghg data & adjust income for inflation
ghg = {}; income = {}; data = {}
for year in range(2007, 2018):
    # import ghg and income
    ghg[year] = pd.read_csv(eval("r'" + data_directory + "/data/processed/GHG_Estimates/MSOA_" + str(year) + ".csv'"))
    income[year] = pd.read_csv(eval("r'" + data_directory + "/data/processed/Income/UK_Income_MSOA_" + str(year) + ".csv'"))
    # adjust for equivalised incomes (account for inflation)
    income[year]['Income anonymised'] = income[year]['Income anonymised'] * income[year]['population']
    total_income = income_equivalised.loc[year, 'Mean equivalised disposable income'] * income[year]['population'].sum()
    income[year]['Income anonymised'] = ((income[year]['Income anonymised'] / income[year]['Income anonymised'].sum()) * total_income) / income[year]['population']
    # add income and ghg to one dataset
    data[year] = ghg[year].join(income[year][['Income anonymised']])
    data[year]['total_ghg'] = data[year].loc[:,'1.1.1.1':'12.5.3.5'].sum(1)

# load geog data to match with ghg (msoa level)
msoa_2011 = gpd.read_file(eval("r'" + data_directory + "/data/raw/Geography/Shapefiles/UK/msoa_2011_uk_all.shp'")).set_index('MSOA11CD')[['geometry']]
lookup = pd.read_csv(eval("r'" + data_directory + "/data/raw/Geography/Conversion_Lookups/UK_full_lookup_2001_to_2011.csv'"))
msoa_2011 = msoa_2011.join(lookup[['MSOA01CD', 'MSOA11CD', 'RGN11NM']].drop_duplicates().set_index('MSOA11CD')).reset_index().to_crs(epsg=3035)
uaa_lookup = pd.read_csv(eval("r'" + data_directory + "/data/raw/Geography/Conversion_Lookups/Output_Area_to_County_and_Unitary_Authority_(December_2019)_Lookup_in_England.csv'"))
uaa_lookup = uaa_lookup.merge(lookup[['OA11CD', 'MSOA11CD']], on='OA11CD', how='left')[['MSOA11CD', 'CTYUA19NM']].drop_duplicates()


for year in range(2007, 2018):
    if year < 2014:
        data[year] = msoa_2011.set_index('MSOA01CD')[['geometry', 'RGN11NM']].join(data[year].set_index('MSOA01CD'), how='right')
    else:
        data[year] = msoa_2011.set_index('MSOA11CD')[['geometry', 'RGN11NM']].join(data[year].set_index('MSOA11CD'), how='left')
    data[year] = data[year].loc[(data[year]['RGN11NM'] != 'Scotland') & (data[year]['RGN11NM'] != 'Northern Ireland') & (data[year]['RGN11NM'] != 'Wales')] 

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
all_data.to_csv(eval("r'" + data_directory + "/data/processed/ghg_income_uaa_lad_grid.csv'"))
