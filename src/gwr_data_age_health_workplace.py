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
import geopandas as gpd

ghg_year = 2015 # 2017

wd = r'/Users/lenakilian/Documents/Ausbildung/UoLeeds/PhD/Analysis/'
years = list(range(2007, 2018, 2))
geog = 'MSOA'

dict_cat = 'category_8'

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
    
# income data
income = {}
income[2017] = pd.read_csv(wd + 'data/raw/Income_Data/equivalised_income_2017-18.csv', header=4, encoding='latin1')
income[2015] = pd.read_csv(wd + 'data/raw/Income_Data/equivalised_income_2015-16.csv', skiprows=5, header=None,  encoding='latin1')
income[2015].columns = income[2017].columns

# import household numbers to adjust income
temp = pd.read_csv(wd + 'data/raw/Geography/Census_Populations/no_households_england.csv').set_index('geography code')[['Household Composition: All categories: Household composition; measures: Value']]
temp = temp.join(pd.read_csv(wd + 'data/raw/Geography/Census_Populations/census2011_pop_england_wales_msoa.csv').set_index('MSOA11CD'))

for year in [2015, 2017]:
    income[year] = income[year].set_index('MSOA code')[['Net annual income after housing costs']].join(temp)
    income[year].columns = ['hhld_income', 'no_hhlds', 'pop']
    income[year]['hhld_income'] = pd.to_numeric(income[year]['hhld_income'].astype(str).str.replace(',', ''), errors='coerce')
    income[year]['income'] = income[year]['hhld_income'] * income[year]['no_hhlds'] / income[year]['pop'] / (365/7)
    income[year] = income[year].dropna(how='all')
    
# import census data
# age
age = pd.read_csv(wd + 'data/raw/Census/age_england_wales_msoa.csv', index_col=0, header=7)\
    .apply(lambda x: pd.to_numeric(x, errors='coerce')).dropna(how='all')
age.index = [str(x).split(' :')[0] for x in age.index]
# disability
disability = pd.read_csv(wd + 'data/raw/Census/DC3201EW - Long-term health problem or disability.csv', index_col=0, header=10)\
    .apply(lambda x: pd.to_numeric(x, errors='coerce')).dropna(how='all').sum(axis=0, level=0).apply(lambda x: x/2)
disability.index = [str(x).split(' :')[0] for x in disability.index]
# ethnicity
ethnicity = pd.read_excel(wd + 'data/raw/Census/KS201EW - Ethnic group.xlsx', index_col=0, header=8)\
    .apply(lambda x: pd.to_numeric(x, errors='coerce')).dropna(how='all')
ethnicity.index = [str(x).split(' :')[0] for x in ethnicity.index]
# workplace
workplace = pd.read_csv(wd + 'data/raw/Census/QS702EW - Distance to work.csv', index_col=0, header=8)\
    .apply(lambda x: pd.to_numeric(x.astype(str).str.replace(',', ''), errors='coerce')).dropna(how='any')
workplace.index = [str(x).split(' :')[0] for x in workplace.index]
workplace.columns = ['pop', 'total_workplace_dist', 'avg_workplace_dist']
# household composition
hhlds = pd.read_csv(wd + 'data/raw/Census/hhldcomp_england_wales_msoa.csv', index_col=0, header=7)\
    .apply(lambda x: pd.to_numeric(x, errors='coerce')).dropna(how='all')
hhlds.index = [str(x).split(' :')[0] for x in hhlds.index]
hhlds = hhlds.rename(columns=dict(zip([hhlds.columns[x] for x in range(1, len(hhlds.columns), 2)], 
                                      [hhlds.columns[x-1] + '_pct' for x in range(1, len(hhlds.columns), 2)])))
# combine all census data
age = age[['All usual residents']]\
    .join(pd.DataFrame(age.loc[:, 'Age 65 to 74':'Age 90 and over'].sum(axis=1))).rename(columns={0:'pop_65+'})\
    .join(pd.DataFrame(age.loc[:, 'Age 0 to 4':'Age 10 to 14'].sum(axis=1))).rename(columns={0:'pop_14-'})
age['pop_65+_pct'] = age['pop_65+'] / age['All usual residents'] * 100
age['pop_14-_pct'] = age['pop_14-'] / age['All usual residents'] * 100

disability['not_lim_pct'] = disability['Day-to-day activities not limited'] / disability['All categories: Long-term health problem or disability'] * 100
disability = disability[['Day-to-day activities not limited', 'not_lim_pct']].rename(columns = {'Day-to-day activities not limited':'not_lim'})

ethnicity['bame_pct'] = ethnicity.drop('White', axis=1).sum(1) / ethnicity.sum(1) * 100

census_data = age[['pop_65+_pct', 'pop_65+', 'pop_14-_pct', 'pop_14-']].join(disability).join(ethnicity[['bame_pct']])\
    .join(workplace[['total_workplace_dist', 'avg_workplace_dist']]).dropna(how='any')
    
    
# add transport access
ptal_2015_tab = pd.read_csv(wd + 'data/raw/PTAL/2015_Grid/2015  PTALs Contours 280515.TAB')

ptal_2015_grid = pd.read_excel(wd + 'data/raw/PTAL/2015_Grid/2015_PTALs_Grid_Values_280515.xlsx')
msoa_2011 = gpd.read_file(wd + 'data/raw/Geography/Shapefiles/UK/msoa_2011_uk_all.shp').set_index('MSOA11CD')[['geometry']]
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


# combine all with emissions data
cat_dict = pd.read_excel(wd + '/data/processed/LCFS/Meta/lcfs_desc_anne&john.xlsx')
cats = cat_dict[['category']].drop_duplicates()['category']
cat_dict['ccp_code'] = [x.split(' ')[0] for x in cat_dict['ccp']]

# save index
idx = cat_dict[[dict_cat]].drop_duplicates()[dict_cat].tolist()
idx.remove('other')

cat_dict = dict(zip(cat_dict['ccp_code'], cat_dict[dict_cat]))
temp = emissions[ghg_year].rename(columns=cat_dict).sum(axis=1, level=0)
new_cat_shp = ptal_2015_msoa[['geometry', 'RGN11NM', 'AI2015', 'PTAL2015', 'AI2015_ln']]\
    .join(temp, how='left').join(census_data, how='left').join(income[ghg_year][['income']])

# scatterplots
for cen_var in ['pop_65+_pct', 'not_lim_pct', 'avg_workplace_dist', 'AI2015', 'pop_14-_pct', 'bame_pct']:
    for item in idx:
        sns.scatterplot(data=new_cat_shp, x=cen_var, y=item); 
        #plt.xscale('log')
        plt.title(cen_var + ' ' + item); plt.show()

#new_cat_shp = new_cat_shp.rename(columns=dict(zip(idx, ['Petrol', 'other_priv', 'rail_bus', 'air', 'rental_tax', 'water'])))
for item in idx:
    new_cat_shp['pc_' + item] = new_cat_shp[item]
    new_cat_shp[item] = new_cat_shp[item] * new_cat_shp['population']

# adjust to population from emissions
new_cat_shp['pop_65+'] = (new_cat_shp['pop_65+_pct'] / 100) * new_cat_shp['population']
new_cat_shp['pop_14-'] = (new_cat_shp['pop_14-_pct'] / 100) * new_cat_shp['population']
new_cat_shp['bame'] = (new_cat_shp['bame_pct'] / 100) * new_cat_shp['population']
new_cat_shp['total_workplace_dist'] = new_cat_shp['avg_workplace_dist'] * new_cat_shp['population'] / 1000
new_cat_shp['lim'] = ((100-new_cat_shp['not_lim_pct']) / 100) * new_cat_shp['population']
    
new_cat_shp.to_file(wd + 'data/processed/GWR_data/gwr_data_london_' + str(ghg_year) + '.shp')


new_cat_shp.plot(column='avg_workplace_dist', legend=True)
