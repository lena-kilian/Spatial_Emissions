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
ew_shp = gpd.read_file(wd + 'data/raw/Geography/Shapefiles/EnglandWales/msoa_2011_ew.shp')\
    .set_index('msoa11cd').join(lookup.set_index('MSOA11CD'), how='left')
ew_shp = ew_shp.loc[ew_shp['RGN11NM'] != 'Wales']

emissions = {}
for year in years:
    year_difference = years[1] - years[0]
    year_str = str(year) + '-' + str(year + year_difference - 1)
    emissions[year] = pd.read_csv(wd + 'data/processed/GHG_Estimates/' + geog + '_' + year_str + '.csv', index_col=0)


# income from LCFS
ptal_2015_tab = pd.read_csv(wd + 'data/raw/PTAL/2015_Grid/2015  PTALs Contours 280515.TAB')

ptal_2015_grid = pd.read_excel(wd + 'data/raw/PTAL/2015_Grid/2015_PTALs_Grid_Values_280515.xlsx')
msoa_2011 = gpd.read_file(wd + 'data/raw/Geography/Shapefiles/UK/msoa_2011_uk_all.shp').set_index('MSOA11CD')[['geometry']]
lookup = pd.read_csv(wd + 'data/raw/Geography/Conversion_Lookups/UK_full_lookup_2001_to_2011.csv')
msoa_2011 = msoa_2011.join(lookup[['MSOA01CD', 'MSOA11CD', 'RGN11NM']].drop_duplicates().set_index('MSOA11CD')).reset_index().to_crs(epsg=3035)

london_2011 = msoa_2011.loc[msoa_2011['RGN11NM'] == 'London']

ptal_2015_points = gpd.GeoDataFrame(ptal_2015_grid, geometry=gpd.points_from_xy(ptal_2015_grid['X'], ptal_2015_grid['Y']))
ptal_2015_points.loc[ptal_2015_points['AI2015'] > 0].plot(column='AI2015')

new_london = london_2011.to_crs(epsg=32610); new_london['geometry']

london_2011.to_file(wd + '/data/raw/PTAL/2015_Grid/London_MSOAs_2011.shp')

pointInPoly = gpd.sjoin(ptal_2015_points, london_2011.to_crs(epsg=27700), op='within') 

ptal_dict = {'0':[np.nan, 0], '1a':[0, 2.5], '1b':[2.5, 5.0], '2':[5, 10], '3':[10, 15], '4':[15, 20], 
             '5':[20, 25], '6a':[25, 40], '6b':[40, np.nan]}

ptal_2015_msoa = pointInPoly.groupby(['MSOA11CD']).median()
ptal_2015_msoa = london_2011.set_index('MSOA11CD').join(ptal_2015_msoa)
ptal_2015_msoa['PTAL2015'] = '0'

for item in ['1a', '1b', '2', '3', '4', '5', '6a', '6b']:
    ptal_2015_msoa.loc[ptal_2015_msoa['AI2015'] > ptal_dict[item][0], 'PTAL2015'] = item

ptal_2015_msoa['AI2015_ln'] = np.log(ptal_2015_msoa['AI2015'] + 1)
    
fig, axs = plt.subplots(ncols=1, nrows=3, figsize=(5, 15))
ptal_2015_msoa.plot(column='AI2015', legend=True, ax=axs[0], cmap='RdBu'); axs[0].set_title('AI 2015')
ptal_2015_msoa.plot(column='AI2015_ln', legend=True, ax=axs[1], cmap='RdBu'); axs[1].set_title('AI 2015 (log)')
ptal_2015_msoa.plot(column='PTAL2015', legend=True, ax=axs[2], cmap='RdBu'); axs[2].set_title('PTAL 2015')


# check if income estimates match
new_cat_shp = {}
cat_dict = pd.read_excel(wd + '/data/processed/LCFS/Meta/lcfs_desc_anne&john.xlsx')
cats = cat_dict[['category']].drop_duplicates()['category']
cat_dict['ccp_code'] = [x.split(' ')[0] for x in cat_dict['ccp']]
cat_dict = dict(zip(cat_dict['ccp_code'], cat_dict['category_5']))
for year in years:
    new_cat_shp[year] = emissions[year].rename(columns=cat_dict).sum(axis=1, level=0)
    new_cat_shp[year] = ptal_2015_msoa[['geometry', 'AI2015', 'AI2015_ln', 'PTAL2015']].join(new_cat_shp[year])

# scatterplots
idx = ['Private transport: Petrol, diesel, motoring oils', 'Private transport: other', 
       'Rail, bus transport', 'Air transport', 'Private transport: Rental, taxi', 'Water transport']
for item in idx:
    sns.scatterplot(data=new_cat_shp[2017], x='AI2015', y=item); 
    #plt.xscale('log')
    plt.title(str(year) + ' ' + item); plt.show()
    
    sns.scatterplot(data=new_cat_shp[2017], x='AI2015_ln', y=item); 
    plt.title(str(year) + ' ' + item); plt.show()
    
    sns.boxplot(data=new_cat_shp[2017].sort_values('AI2015'), x='PTAL2015', y=item); 
    plt.title(str(year) + ' ' + item); plt.show()


#temp = new_cat_shp[2017][idx + ['geometry', 'population', 'AI2015_ln', 'AI2015']].reset_index()
#temp[idx] = temp[idx].apply(lambda x: x*temp['population'])
#temp.columns = ['MSOA11CD', 'Petrol', 'other_priv', 'rail_bus', 'air', 'rental_taxi', 'water', 'geometry', 'pop', 'AI2015_ln', 'AI2015']
#temp.to_file(wd + 'data/processed/GWR_data/transport_access.shp')

all_data_shp = pd.DataFrame()
for year in years:
    temp = cp.copy(new_cat_shp[year])
    temp['year'] = year
    temp = temp.join(lookup[['MSOA11CD', 'RGN11NM']].set_index('MSOA11CD'))
    all_data_shp = all_data_shp.append(temp)
    
all_data = all_data_shp.drop('geometry', axis=1)
    
by_year = cp.copy(all_data)
by_year['London'] = True; by_year.loc[by_year['RGN11NM'] != 'London', 'London'] = False
by_year = by_year.set_index(['year', 'London'], append=True)
by_year[idx] = by_year[idx].apply(lambda x: x*by_year['population'])
by_year = by_year.sum(axis=0, level=['year', 'London'])
by_year[idx] = by_year[idx].apply(lambda x: x/by_year['population'])
by_year = by_year[idx].unstack(level='London')

by_year_pct = cp.copy(by_year)
for year in years:
    by_year_pct.loc[year,:] = by_year.loc[year,:] / by_year.loc[2007,:] * 100
by_year_pct = by_year_pct.stack(level='London')

data = by_year_pct[idx].stack().reset_index().rename(columns={'level_2':'product', 0:'ghg_pct'})
for item in [True, False]:
    temp = data.loc[data['London'] == item]
    sns.lineplot(data=temp, x='year', y='ghg_pct', hue='product')#, legend=False)
    plt.title(str(item)); plt.ylim(25, 175); plt.show()
    
data = by_year[idx].stack(level=[0, 1]).reset_index().rename(columns={'level_1':'product', 0:'ghg_pct'})
for item in [True, False]:
    temp = data.loc[data['London'] == item]
    sns.lineplot(data=temp, x='year', y='ghg_pct', hue='product')
    plt.title(str(item)); plt.ylim(0, 3); 
    plt.show()

change = by_year[idx].reset_index().corr()[['year']]
    
