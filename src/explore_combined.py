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
import mapclassify
import random
import math
import statsmodels.api as sm

data_directory = "/Users/lenakilian/Documents/Ausbildung/UoLeeds/PhD/Analysis"
output_directory = "/Users/lenakilian/Documents/Ausbildung/UoLeeds/PhD/Analysis/Spatial_Emissions"


ptal_2015_tab = pd.read_csv(eval("r'" + data_directory + "/data/raw/PTAL/2015_Grid/2015  PTALs Contours 280515.TAB'"))

ptal_2015_grid = pd.read_excel(eval("r'" + data_directory + "/data/raw/PTAL/2015_Grid/2015_PTALs_Grid_Values_280515.xlsx'"))
msoa_2011 = gpd.read_file(eval("r'" + data_directory + "/data/raw/Geography/Shapefiles/UK/msoa_2011_uk_all.shp'")).set_index('MSOA11CD')[['geometry']]
lookup = pd.read_csv(eval("r'" + data_directory + "/data/raw/Geography/Conversion_Lookups/UK_full_lookup_2001_to_2011.csv'"))
msoa_2011 = msoa_2011.join(lookup[['MSOA01CD', 'MSOA11CD', 'RGN11NM']].drop_duplicates().set_index('MSOA11CD')).reset_index().to_crs(epsg=3035)

london_2011 = msoa_2011.loc[msoa_2011['RGN11NM'] == 'London']

ptal_2015_points = gpd.GeoDataFrame(ptal_2015_grid, geometry=gpd.points_from_xy(ptal_2015_grid['X'], ptal_2015_grid['Y']))
ptal_2015_points.loc[ptal_2015_points['AI2015'] > 0].plot(column='AI2015')

new_london = london_2011.to_crs(epsg=32610); new_london['geometry']

london_2011.to_file(eval("r'" + data_directory + "/data/raw/PTAL/2015_Grid/London_MSOAs_2011.shp'"))

pointInPoly = gpd.sjoin(ptal_2015_points, london_2011.to_crs(epsg=27700), op='within') 

ptal_dict = {'0':[np.nan, 0], '1a':[0, 2.5], '1b':[2.5, 5.0], '2':[5, 10], '3':[10, 15], '4':[15, 20], 
             '5':[20, 25], '6a':[25, 40], '6b':[40, np.nan]}

ptal_2015_msoa = pointInPoly.groupby(['MSOA11CD']).mean()
ptal_2015_msoa = london_2011.set_index('MSOA11CD').join(ptal_2015_msoa)
ptal_2015_msoa['PTAL2015'] = '0'

for item in ['1a', '1b', '2', '3', '4', '5', '6a', '6b']:
    ptal_2015_msoa.loc[ptal_2015_msoa['AI2015'] > ptal_dict[item][0], 'PTAL2015'] = item
    
fig, axs = plt.subplots(ncols=2, nrows=1, figsize=(15, 5))
ptal_2015_msoa.plot(column='AI2015', legend=True, ax=axs[0], cmap='RdBu'); axs[0].set_title('AI 2015')
ptal_2015_msoa.plot(column='PTAL2015', legend=True, ax=axs[1], cmap='RdBu'); axs[1].set_title('PTAL 2015')





# check 2013 and 2014

data_13 = {}; data_13_all = {}
for year in [2013, 2014]:
    # import ghg and income
    data_13[year] = pd.read_csv(eval("r'" + data_directory + "/data/processed/GHG_Estimates/MSOA_" + str(year) + ".csv'"))
    data_13[year]['total_ghg'] = data_13[year].loc[:,'1.1.1.1':'12.5.3.5'].sum(1)
    data_13[year] = data_13[year].rename(columns={'MSOA11CD':'MSOA', 'MSOA01CD':'MSOA'})
    
    data_13_all[year] = data_13[year].set_index('MSOA')
    data_13_all[year].loc[:,'1.1.1.1':'12.5.3.5'] = data_13_all[year].loc[:,'1.1.1.1':'12.5.3.5'].apply(lambda x: x * data_13_all[year]['population'])
    data_13_all[year] = data_13_all[year].sum() / data_13_all[year]['population'].sum()
    data_13_all[year]['total_ghg'] = data_13_all[year]['1.1.1.1':'12.5.3.5'].sum()

data_1314 = pd.DataFrame(data_13_all[2013]).join(pd.DataFrame(data_13_all[2014]), lsuffix='_2013', rsuffix='_2014')

temp = data_1314.loc['1.1.1.1':'12.5.3.5', :]
plt.scatter(x=temp['0_2013'], y=temp['0_2014'])


"""
years = list(range(2007, 2017, 2))

data_old = {}
for year in years:
    # import ghg and income
    data_old[year] = pd.read_csv(eval("r'" + data_directory + "/data/processed/GHG_Estimates/MSOA_mean_" + str(year) + '-' + str(year+1) + ".csv'"))
    data_old[year]['total_ghg'] = data_old[year].loc[:,'1.1.1.1':'12.5.3.5'].sum(1)
"""
    
years = list(range(2007, 2018, 2))

data = {}
for year in list(range(2007, 2018, 2)):
    # import ghg and income
    data[year] = pd.read_csv(eval("r'" + data_directory + "/data/processed/GHG_Estimates/MSOA_" + str(year) + '-' + str(year+1) + ".csv'"))
    data[year]['total_ghg'] = data[year].loc[:,'1.1.1.1':'12.5.3.5'].sum(1)
    data[year] = data[year].rename(columns={'MSOA11CD':'MSOA', 'MSOA01CD':'MSOA'})

lookup = pd.read_csv(eval("r'" + data_directory + "/data/raw/Geography/Conversion_Lookups/UK_full_lookup_2001_to_2011.csv'"))
regions = {}
for year in years:
    if year < 2014:
        regions[year] = data[year].set_index('MSOA').join(lookup[['RGN11NM', 'MSOA01CD']].drop_duplicates().set_index('MSOA01CD'))
    else:
        regions[year] = data[year].set_index('MSOA').join(lookup[['RGN11NM', 'MSOA11CD']].drop_duplicates().set_index('MSOA11CD'))
    regions[year].loc[:,'1.1.1.1':'12.5.3.5'] = regions[year].loc[:,'1.1.1.1':'12.5.3.5'].apply(lambda x: x* regions[year]['population'])
    regions[year] = regions[year].groupby('RGN11NM').sum().reset_index()
    regions[year].loc[:,'1.1.1.1':'12.5.3.5'] = regions[year].loc[:,'1.1.1.1':'12.5.3.5'].apply(lambda x: x/ regions[year]['population'])
    regions[year]['total_ghg'] = regions[year].loc[:,'1.1.1.1':'12.5.3.5'].sum(1)

regions_1 = {}
for year in years:
    idx = regions[year].loc[:,'1.1.1.1':'12.5.3.5'].columns.tolist()
    idx0 = [x.split('.')[0] for x in idx] + ['population', 'total_ghg']
    regions_1[year] = cp.copy(regions[year].set_index('RGN11NM'))
    regions_1[year].columns = [x.split('.')[0] for x in idx] + ['population', 'total_ghg']
    regions_1[year] = regions_1[year].sum(axis=1, level=0)
    #regions_1[year] = regions_1[year].set_index(['total_ghg', 'population'], append=True).stack().reset_index().rename(columns={'level_3':'ccp1', 0:'ghg_pc'})

for year in years:
    temp = regions_1[year].loc[:,'1':'12']
    bottom = [0] * len(temp.index)
    for ccp in range(1, 13):
        height = temp[str(ccp)]
        plt.bar(x=temp.index, height=height, bottom=bottom)
        bottom += temp[str(ccp)]
        print(height)
    plt.title(str(year)); plt.xticks(rotation=90); plt.show()
    #sns.barplot(data=regions_1[year], x='ccp1', y='ghg_pc', hue='RGN11NM'); plt.show()

fig, axs = plt.subplots(nrows=2, ncols=3, sharex=True, sharey=True, figsize=(10,10))
for i in range(len(years)):
    year = years[i]
    r = abs(i%2)
    c = math.floor(i/2) 
    temp = regions_1[year].loc[:,'1':'12']
    bottom = [0] * len(temp.index)
    for ccp in range(1, 13):
        height = temp[str(ccp)]
        axs[r, c].bar(x=temp.index, height=height, bottom=bottom)
        bottom += temp[str(ccp)]
    axs[r, c].set_title(str(year))
    if r == 1:
        plt.sca(axs[r, c])
        plt.xticks(rotation=90)
plt.savefig(eval("r'" + output_directory + "region_ccp1_plots.png'"))

writer = pd.ExcelWriter(eval("r'" + output_directory + "region_ccp1_data.xlsx'"))
# write dataframe to excel
for year in years:
    regions_1[year].to_excel(writer, sheet_name=str(year) + '-' + str(year +1))
# save the excel
writer.save()




for year in years:
    data[year][['total_ghg']].hist(); plt.title(str(year)); plt.show()

"""    
both = {}
for year in list(data_old.keys()):
    both[year] = data[year][['total_ghg']].join(data_old[year][['total_ghg']], lsuffix='_new', rsuffix='_old')
    plt.scatter(both[year]['total_ghg_old'], both[year]['total_ghg_new']); plt.title(str(year)); 
    plt.xlabel('UKMRIO 2020'); plt.ylabel('UKMRIO 2021')
    plt.show()
    print(both[year].mean())

fig, axs = plt.subplots(nrows=2, ncols=3, sharex=True, sharey=True, figsize=(10,7))
years2 = list(both.keys())
for i in range(len(both)):
    year = years2[i]
    r = abs(i%2)
    c = math.floor(i/2) 
    axs[r,c].scatter(both[year]['total_ghg_old'], both[year]['total_ghg_new'], s=0.5); plt.title(str(year)); 
    axs[r,c].set_xlabel('UKMRIO 2020'); axs[r,c].set_ylabel('UKMRIO 2021')
    axs[r,c].set_xlim(5, 19); axs[r,c].set_ylim(4, 20)
    axs[r, c].set_title(str(year))
plt.savefig(eval("r'" + output_directory + "old_vs_new_MSOA.png'"))

"""

msoa_2011 = gpd.read_file(eval("r'" + data_directory + "/data/raw/Geography/Shapefiles/UK/msoa_2011_uk_all.shp'")).set_index('MSOA11CD')[['geometry']]
lookup = pd.read_csv(eval("r'" + data_directory + "/data/raw/Geography/Conversion_Lookups/UK_full_lookup_2001_to_2011.csv'"))
msoa_2011 = msoa_2011.join(lookup[['MSOA01CD', 'MSOA11CD', 'RGN11NM']].drop_duplicates().set_index('MSOA11CD')).reset_index().to_crs(epsg=3035)

for year in years:
    if year < 2013:
        data[year] = msoa_2011.set_index('MSOA01CD')[['geometry', 'RGN11NM']].join(data[year].set_index('MSOA'), how='right')
    else:
        data[year] = msoa_2011.set_index('MSOA11CD')[['geometry', 'RGN11NM']].join(data[year].set_index('MSOA'), how='left')
    data[year] = data[year].loc[(data[year]['RGN11NM'] != 'Scotland') & (data[year]['RGN11NM'] != 'Northern Ireland') & (data[year]['RGN11NM'] != 'Wales')] 


# try different product categories
new_cat = {}
cat_dict = pd.read_excel(eval("r'" + data_directory + "/data/processed/LCFS/Meta/lcfs_desc_anne&john.xlsx'"))
cats = cat_dict[['category_4']].drop_duplicates()['category_4']
cat_dict['ccp_code'] = [x.split(' ')[0] for x in cat_dict['ccp']]
cat_dict = dict(zip(cat_dict['ccp_code'], cat_dict['category_4']))
for year in years:
    new_cat[year] = data[year].rename(columns=cat_dict).sum(axis=1, level=0)
    new_cat[year] = gpd.GeoDataFrame(new_cat[year], geometry='geometry')
    
transport = {}; transport_all = pd.DataFrame()
for year in years:
    transport[year] = new_cat[year].loc[new_cat[year]['RGN11NM'] != 'London']
    transport[year] = transport[year][['trsprt (priv.)', 'trsprt (rail, bus)', 'trsprt (air)', 'trsprt (water)']].apply(lambda x:x*new_cat[year]['population'])
    temp = pd.DataFrame(transport[year].sum(axis=0)).T
    temp['year'] = year
    transport_all = transport_all.append(temp)
  
transport_all = transport_all.set_index('year')   

transport_pct = cp.copy(transport_all)
years.reverse()
for item in transport_all.columns:
    for year in years:
        transport_pct.loc[year, item] = transport_pct.loc[year, item]/transport_pct.loc[2007, item] * 100
years.reverse()  

title='London Region' #'London Region' 'Rest of England'
transport_pct2 = transport_all.T.apply(lambda x: x/sum(x) * 100).T
bottom = [0] * len(transport_pct2)
for item in transport_pct2.columns:
    h = transport_pct2[item]
    plt.bar(x=years, height=transport_pct2[item], bottom=bottom)
    bottom += h
plt.xlabel('Year'); plt.ylabel('Percentage of Transport Type'); plt.title(title)


transport_pct.plot(); plt.ylabel('Change in emissions since 2007'); plt.title(title); plt.show() #'London Region' 'Rest of England'
transport_all.plot(); plt.ylabel('Total emissions'); plt.title(title); plt.show()

new_cat_all = pd.DataFrame(columns=new_cat[2007].columns)
for year in years:
    temp = cp.copy(new_cat[year]); temp['year'] = year
    new_cat_all = new_cat_all.append(temp)

#new_cat_all = gpd.GeoDataFrame(new_cat_all, geometry='geometry')

new_cat_ = new_cat_all.drop(['total_ghg', 'population', 'geometry'], axis=1).set_index(['RGN11NM', 'year', 'Income anonymised'], append=True).stack().reset_index()
new_cat_.columns = ['MSOA', 'RGN',  'year', 'income', 'product', 'ghg']
new_cat_ = new_cat_.set_index('MSOA').join(lookup[['MSOA11CD', 'LAD17NM']].drop_duplicates().set_index('MSOA11CD'))


new_cat_ = new_cat_all[['geometry']].join(new_cat_)

maxmin = msoa_2011.loc[msoa_2011['RGN11NM'] == 'Northern Ireland'].iloc[:2,:][['geometry']]

for item in new_cat_[['product']].drop_duplicates().dropna()['product'][5:]:
    fig, axs = plt.subplots(ncols=len(years), nrows=1, figsize=(len(years)*10, 8), sharex=True, sharey=True)
    temp = new_cat_.loc[new_cat_['product'] == item]
    temp_max = temp['ghg'].max(); temp_min = temp['ghg'].min()
    temp_maxmin = cp.copy(maxmin); temp_maxmin['ghg'] = [temp_max, temp_min]
    for i in range(len(years)):
        year = years[i]
        temp2 = temp.loc[temp['year'] == year].append(temp_maxmin)
        gpd.GeoDataFrame(temp2, geometry='geometry').plot(column='ghg', legend=True, ax=axs[i])
        axs[i].set_title(item + ', ' + str(year))
        axs[i].set_xlim(3100000, 3800000); axs[i].set_ylim(3075000, 3720000)
    plt.savefig(eval("r'" + data_directory + "/Spatial_Emissions/outputs/facets/MSOA_map_" + item + ".png'"), dpi=300)


'''
g = sns.FacetGrid(new_cat_, row='year', col='product', hue='RGN')
g.map(sns.scatterplot, 'income', 'ghg')
plt.savefig(eval("r'" + data_directory + "/Spatial_Emissions/outputs/facets/MSOA_facet_scatterplot.png'"))
'''

for item in new_cat_[['product']].drop_duplicates()['product']:
    fig, axs = plt.subplots(ncols=len(years), nrows=1, figsize=(len(years)*5, 5), sharex=True, sharey=True)
    temp = new_cat_.loc[new_cat_['product'] == item]
    for i in range(len(years)):
        year = years[i]
        sns.scatterplot(data=temp.loc[temp['year'] == year], y='ghg', x='income', hue='RGN', legend=False, ax=axs[i])
        axs[i].set_title(item + ', ' + str(year))
    plt.savefig(eval("r'" + data_directory + "/Spatial_Emissions/outputs/facets/MSOA_scatterplot_" + item + ".png'"))



new_cat_ldn = new_cat_all.loc[new_cat_all['RGN11NM'] == 'London']
new_cat_ldn = new_cat_ldn.drop(['RGN11NM', 'total_ghg', 'population', 'geometry'], axis=1).set_index(['year', 'Income anonymised'], append=True).stack().reset_index()
new_cat_ldn.columns = ['MSOA', 'year', 'income', 'product', 'ghg']
new_cat_ldn = new_cat_ldn.set_index('MSOA').join(lookup[['MSOA11CD', 'LAD17NM']].drop_duplicates().set_index('MSOA11CD'))

'''
g = sns.FacetGrid(new_cat_ldn, row='year', col='product', hue='LAD17NM')
g.map(sns.scatterplot, 'income', 'ghg')
plt.savefig(eval("r'" + data_directory + "/Spatial_Emissions/outputs/facets/London_MSOA_facet_scatterplot.png'"))
'''

for item in new_cat_ldn[['product']].drop_duplicates()['product']:
    fig, axs = plt.subplots(ncols=len(years), nrows=1, figsize=(len(years)*5, 5), sharex=True, sharey=True)
    temp = new_cat_ldn.loc[new_cat_ldn['product'] == item]
    for i in range(len(years)):
        year = years[i]
        sns.scatterplot(data=temp.loc[temp['year'] == year], y='ghg', x='income', hue='LAD17NM', legend=False, ax=axs[i])
        axs[i].set_title(item + ', ' + str(year))
    plt.savefig(eval("r'" + data_directory + "/Spatial_Emissions/outputs/facets/London_MSOA_scatterplot_" + item + ".png'"))
    

new_cat_ldn = new_cat_all[['geometry']].join(new_cat_ldn)

maxmin = new_cat_all.loc[new_cat_all['RGN11NM'] == 'North West']; maxmin = maxmin.iloc[:2,:1]

for item in new_cat_ldn[['product']].drop_duplicates().dropna()['product']:
    fig, axs = plt.subplots(ncols=len(years), nrows=1, figsize=(len(years)*7, 4), sharex=True, sharey=True)
    temp = new_cat_ldn.loc[new_cat_ldn['product'] == item]
    temp_max = temp['ghg'].max(); temp_min = temp['ghg'].min()
    temp_maxmin = cp.copy(maxmin); temp_maxmin['ghg'] = [temp_max, temp_min]
    for i in range(len(years)):
        year = years[i]
        temp2 = temp.loc[temp['year'] == year].append(temp_maxmin)
        gpd.GeoDataFrame(temp2, geometry='geometry').plot(column='ghg', legend=True, ax=axs[i])
        axs[i].set_title(item + ', ' + str(year))
        axs[i].set_xlim(3585000, 3660000); axs[i].set_ylim(3175000, 3230000)
    plt.savefig(eval("r'" + data_directory + "/Spatial_Emissions/outputs/facets/London_MSOA_map_" + item + ".png'"))

#new_cat_all.to_file(eval("r'" + data_directory + "/data/processed/new_cat_for_gwr.shp'"), driver = 'ESRI Shapefile')

# use other cats
new_cat = {}
cat_dict = pd.read_excel(eval("r'" + data_directory + "/data/processed/LCFS/Meta/lcfs_desc_anne&john.xlsx'"))
cats = cat_dict[['category_3']].drop_duplicates()['category_3']
cat_dict['ccp_code'] = [x.split(' ')[0] for x in cat_dict['ccp']]
cat_dict = dict(zip(cat_dict['ccp_code'], cat_dict['category_3']))
for year in years:
    new_cat[year] = data[year].rename(columns=cat_dict).sum(axis=1, level=0)
    new_cat[year] = gpd.GeoDataFrame(new_cat[year], geometry='geometry')
    
new_cat_all = pd.DataFrame(columns=new_cat[2007].columns)
for year in years:
    temp = cp.copy(new_cat[year]); temp['year'] = year
    new_cat_all = new_cat_all.append(temp)


'''
keep = ['grains', 'other food', 'meat', 'dairy and eggs',
       'fruit and veg', 'drinks', 'miscellaneous', 'clothing', 'other home',
       'home energy', 'private transport (land)',
       'public transport (land and water)', 'air transport', 
       'Income anonymised', 'total_ghg']
'''

keep = ['grains, fruit, veg', 'other food and drinks',
       'food (animal origin)', 'miscellaneous', 'clothing', 'other home',
       'home energy', 'private transport (land)',
       'public transport (land and water)', 'air transport', 
       'Income anonymised', 'total_ghg']

cat3 = ['private transport (land)', 'rail transport', 'bus transport', 'combined transport', 'air transport', 'school transport', 'water transport']

fig, axs = plt.subplots(nrows=len(years), ncols=len(cat3), figsize=(5*len(cat3), 5*len(years)), sharex=True, sharey=True)
for y in range(len(years)):
    year = years[y]
    for i in range(len(cat3)):
        item = cat3[i]
        temp = new_cat_all.loc[(new_cat_all['year'] == year)].sort_values('RGN11NM')
        sns.scatterplot(ax=axs[y, i], data=temp, x='Income anonymised', y=item, hue='RGN11NM', legend=False)
        axs[y, i].set_title(item + ' ' + str(year))
plt.savefig(eval("r'" + data_directory + "/Spatial_Emissions/outputs/facets/LAD_facet_scatter_grid_transport.png'"))

check = new_cat_all.set_index(['RGN11NM', 'year'], append=True)[cat3].stack().reset_index()
check.columns = ['MSOA', 'RGN', 'year', 'product', 'ghg']

g = sns.FacetGrid(check, row='RGN', col='product')
g.map(sns.boxplot, 'year', 'ghg')
plt.savefig(eval("r'" + data_directory + "/Spatial_Emissions/outputs/facets/MSOA_facet_boxplot.png'"))



check = pd.DataFrame()
for i in range(33):
    check = check.append(concs_dict2[str(i)].T)
    
check2 = check[['UK Rail transport services             ',
 'UK Land transport services and transport services via pipelines, excluding rail transport     ',
 'UK Water transport services             ',
 'UK Air transport services             ',]]


keep = ['food (other)', 'food (ab)', 'other',
       'other home', 'home energy', 'trsprt (priv.)', 'trsprt (rail, bus)',
       'trsprt (air)', 'trsprt (water)', 'ccp 9', 'eating out', 'ccp 12',
       'Income anonymised', 'total_ghg']
# LAD!!
lad_avg = {}; lad_avg_all = pd.DataFrame(); lad_avg_product = pd.DataFrame()
for year in list(new_cat.keys()):
    lad_avg[year] = new_cat[year].join(lookup[['MSOA11CD', 'LAD17NM']].drop_duplicates().set_index('MSOA11CD'))
    lad_avg[year][keep] = lad_avg[year][keep].apply(lambda x: x*lad_avg[year]['population'])
    lad_avg[year] = lad_avg[year].groupby(['LAD17NM', 'RGN11NM']).sum()
    lad_avg[year] = lad_avg[year][keep].apply(lambda x: x/lad_avg[year]['population'])
    lad_avg[year]['year'] = year
    lad_avg_product = lad_avg_product.append(lad_avg[year])
    lad_avg[year] = lad_avg[year].set_index(['year', 'Income anonymised'], append=True).stack().reset_index()
    lad_avg[year].columns = ['LAD17NM', 'RGN11NM', 'year', 'income', 'product', 'ghg']
    lad_avg_all = lad_avg_all.append(lad_avg[year])
lad_avg_all.to_csv(eval("r'" + data_directory + "/data/processed/lad_avg_all.csv'"))
    
g = sns.FacetGrid(lad_avg_all.loc[lad_avg_all['product'] != 'total_ghg'], row='year', col='product', hue='RGN11NM')
g.map(sns.scatterplot, 'income', 'ghg', legend='brief')
plt.savefig(eval("r'" + data_directory + "/Spatial_Emissions/outputs/facets/LAD_facet_scatter.png'"))

  
g = sns.FacetGrid(lad_avg_all.loc[(lad_avg_all['product'] != 'total_ghg') & (lad_avg_all['RGN11NM'] == 'London')], row='year', col='product')
g.map(sns.scatterplot, 'income', 'ghg', legend='brief')
plt.savefig(eval("r'" + data_directory + "/Spatial_Emissions/outputs/facets/LAD_London_facet_scatter.png'"))

 
g = sns.FacetGrid(lad_avg_all.loc[lad_avg_all['product'] != 'total_ghg'], col='RGN11NM', row='product', hue='year')
g.map(sns.scatterplot, 'income', 'ghg', legend='brief'); plt.xscale('log')
plt.savefig(eval("r'" + data_directory + "/Spatial_Emissions/outputs/facets/LAD_facet_scatter2.png'"))


g = sns.FacetGrid(lad_avg_all.loc[lad_avg_all['product'] != 'total_ghg'].sort_values('ghg'), col='RGN11NM', row='product')
g.map(sns.boxplot, 'ghg', 'LAD17NM'); #plt.xticks(rotation=90)
plt.savefig(eval("r'" + data_directory + "/Spatial_Emissions/outputs/facets/LAD_facet_boxplot.png'"))
 
   

items = ['grains, fruit, veg', 'other food and drinks', 'food (animal origin)', 'miscellaneous', 'clothing', 'other home', 'home energy', 'private transport (land)', 'public transport (land and water)', 'air transport', 'total_ghg']
for item in items:
    g = sns.FacetGrid(lad_avg_all.loc[lad_avg_all['product'] == item].sort_values('RGN11NM'), row=None, col='RGN11NM', hue='year')
    g.map(sns.scatterplot, 'income', 'ghg'); #plt.xticks(rotation=90);
    plt.ylabel(item + ' GHG')
    plt.savefig(eval("r'" + data_directory + "/Spatial_Emissions/outputs/facets/LAD_facet_scatter_" + item + ".png'"))


items = ['grains, fruit, veg', 'other food and drinks', 'food (animal origin)', 'miscellaneous', 'clothing', 'other home', 'home energy', 'private transport (land)', 'public transport (land and water)', 'air transport', 'total_ghg']
for item in items:
    g = sns.FacetGrid(lad_avg_all.loc[lad_avg_all['product'] == item].sort_values('RGN11NM'), row=None, col='year', hue='RGN11NM')
    g.map(sns.regplot, 'income', 'ghg', size=0.5); #plt.xticks(rotation=90);
    plt.ylabel(item + ' GHG')
    plt.legend()
    plt.savefig(eval("r'" + data_directory + "/Spatial_Emissions/outputs/facets/LAD_facet_scatter_" + item + "_2.png'"))


items = ['grains, fruit, veg', 'other food and drinks', 'food (animal origin)', 'miscellaneous', 'clothing', 'other home', 'home energy', 'private transport (land)', 'public transport (land and water)', 'air transport', 'total_ghg']
fig, axs = plt.subplots(nrows=len(years), ncols=len(items), figsize=(5*len(items), 5*len(years)), sharex=True)
for y in range(len(years)):
    year = years[y]
    for i in range(len(items)):
        item = items[i]
        temp = lad_avg_all.loc[(lad_avg_all['product'] == item) & (lad_avg_all['year'] == year)].sort_values('RGN11NM')
        sns.scatterplot(ax=axs[y, i], data=temp, x='income', y='ghg', hue='RGN11NM', legend=False)
        axs[y, i].set_title(item + ' ' + str(year))
plt.savefig(eval("r'" + data_directory + "/Spatial_Emissions/outputs/facets/LAD_facet_scatter_grid_2.png'"))



items = ['grains, fruit, veg', 'other food and drinks', 'food (animal origin)', 'miscellaneous', 'clothing', 'other home', 'home energy', 'private transport (land)', 'public transport (land and water)', 'air transport', 'total_ghg']
for i in range(len(items)):
    item = items[i]
    fig, axs = plt.subplots(nrows=1, ncols=len(years), figsize=(5*len(years), 5), sharex=True, sharey=True)
    for y in range(len(years)):
        year = years[y]
        temp = lad_avg_all.loc[(lad_avg_all['product'] == item) & (lad_avg_all['year'] == year)].sort_values('RGN11NM')
        sns.scatterplot(ax=axs[y], data=temp, x='income', y='ghg', hue='RGN11NM', legend=False)
        axs[y].set_title(item + ' ' + str(year))
    plt.savefig(eval("r'" + data_directory + "/Spatial_Emissions/outputs/facets/LAD_facet_scatter_grid_2" + item + ".png'"))



items = ['grains, fruit, veg', 'other food and drinks', 'food (animal origin)', 'miscellaneous', 'clothing', 'other home', 'home energy', 'private transport (land)', 'public transport (land and water)', 'air transport', 'total_ghg']
for i in range(len(items)):
    item = items[i]
    fig, axs = plt.subplots(nrows=1, ncols=len(years), figsize=(5*len(years), 5), sharex=True, sharey=True)
    for y in range(len(years)):
        year = years[y]
        for region in lookup[['RGN11NM']].drop_duplicates()['RGN11NM']:
            temp = lad_avg_all.loc[(lad_avg_all['product'] == item) & (lad_avg_all['year'] == year) & (lad_avg_all['RGN11NM'] == region)]
            sns.regplot(ax=axs[y], data=temp, x='income', y='ghg')
            axs[y].set_title(item + ' ' + str(year))
    plt.savefig(eval("r'" + data_directory + "/Spatial_Emissions/outputs/facets/LAD_facet_scatter_grid_3_" + item + ".png'"))






 
for item in ['other food and drinks', 'food (animal origin)', 'home energy', 'private transport (land)', 'public transport (land and water)', 'air transport', 
             'miscellaneous', 'total_ghg']:
    for region in lad_avg_all[['RGN11NM']].drop_duplicates()['RGN11NM']:
        fig, axs = plt.subplots(nrows=2, ncols=1, figsize=(20,8), sharex=True)
        data = lad_avg_product.reset_index()
        data = data.loc[data['RGN11NM'] == region].sort_values(item, ascending=False)
        sns.boxplot(ax=axs[0], data=data, x='LAD17NM', y=item)
        sns.boxplot(ax=axs[1], data=data, x='LAD17NM', y='Income anonymised')
        plt.xticks(rotation=90)
        plt.savefig(eval("r'" + data_directory + "/Spatial_Emissions/outputs/facets/LAD_facet_boxplot_" + item + "_" + region + ".png'"), bbox_inches='tight')
    
    
for item in['other food and drinks', 'food (animal origin)', 'home energy', 'private transport (land)', 'public transport (land and water)', 'air transport', 
             'miscellaneous', 'total_ghg']:
    fig, axs = plt.subplots(ncols=5, nrows=1, figsize=(50,10), sharey=True)
    for year in years:
        i = years.index(year)
        data = cp.copy(lad_avg_product.reset_index())
        data = data.loc[data['year'] == year].drop_duplicates()
        sns.scatterplot(ax=axs[i], data=data, x='Income anonymised', y=item, hue='RGN11NM')
        axs[i].set_title(str(year))
        axs[i].set_xlim(200,550)
    plt.savefig(eval("r'" + data_directory + "/Spatial_Emissions/outputs/facets/LAD_facet_scatter_" + item + ".png'"), bbox_inches='tight')
    



for item in['total_ghg', 'miscellaneous', 'food (animal origin)']:
    fig, axs = plt.subplots(ncols=5, nrows=1, figsize=(50,10), sharey=True)
    for year in years:
        i = years.index(year)
        data = cp.copy(lad_avg_product.reset_index())
        data = data.loc[(data['year'] == year) & (data['RGN11NM'] == 'London')].drop_duplicates()
        sns.scatterplot(ax=axs[i], data=data, x='Income anonymised', y=item, hue='RGN11NM')
        axs[i].set_title(str(year))
        axs[i].set_xlim(200, 700)
        for j in range(len(data)):
            axs[i].text(data['Income anonymised'].tolist()[j], data[item].tolist()[j], data['LAD17NM'].tolist()[j])
    plt.savefig(eval("r'" + data_directory + "/Spatial_Emissions/outputs/facets/London_LAD_facet_scatter_" + item + ".png'"), bbox_inches='tight')



for region in ['London', 'South East', 'South West']:
    for item in['air transport']:
        fig, axs = plt.subplots(ncols=5, nrows=1, figsize=(50,10), sharey=True)
        for year in years:
            i = years.index(year)
            data = cp.copy(lad_avg_product.reset_index())
            data = data.loc[(data['year'] == year) & (data['RGN11NM'] == region)].drop_duplicates()
            sns.scatterplot(ax=axs[i], data=data, x='Income anonymised', y=item, hue='RGN11NM')
            axs[i].set_title(str(year))
            axs[i].set_xlim(200, 700)
            for j in range(len(data)):
                axs[i].text(data['Income anonymised'].tolist()[j], data[item].tolist()[j], data['LAD17NM'].tolist()[j])
    plt.savefig(eval("r'" + data_directory + "/Spatial_Emissions/outputs/facets/" + region + "_LAD_facet_scatter_" + item + ".png'"), bbox_inches='tight')

for region in ['London', 'South East', 'South West']:
    for item in['public transport (land and water)', 'private transport (land)', 'home energy']:
        fig, axs = plt.subplots(ncols=5, nrows=1, figsize=(50,10), sharey=True)
        for year in years:
            i = years.index(year)
            data = cp.copy(lad_avg_product.reset_index())
            data = data.loc[(data['year'] == year) & (data['RGN11NM'] == region)].drop_duplicates()
            sns.scatterplot(ax=axs[i], data=data, x='Income anonymised', y=item, hue='RGN11NM')
            axs[i].set_title(str(year))
            axs[i].set_xlim(200, 700)
            for j in range(len(data)):
                axs[i].text(data['Income anonymised'].tolist()[j], data[item].tolist()[j], data['LAD17NM'].tolist()[j])
    plt.savefig(eval("r'" + data_directory + "/Spatial_Emissions/outputs/facets/" + region + "_LAD_facet_scatter_" + item + ".png'"), bbox_inches='tight')





# LONDON SPIDERPLOT

ldn_avg = cp.copy(new_cat_all)
ldn_avg['Area'] = 'London'; ldn_avg.loc[ldn_avg['RGN11NM'] != 'London', 'Area'] = 'Other UK'
ldn_avg[keep] = ldn_avg[keep].apply(lambda x: x*ldn_avg['population'])
ldn_avg = ldn_avg.groupby(['year', 'Area']).sum()
ldn_avg[keep] = ldn_avg[keep].apply(lambda x: x/ldn_avg['population'])

import spiderplot as sp

sns.set_style("whitegrid")
# Load some demo data.
df = ldn_avg.drop(['population', 'Income anonymised', 'total_ghg'], axis=1).stack().reset_index()
df.columns = ['year', 'Area', 'product', 'ghg']
df = df.loc[df['year'] == 2015]
df = df.sort_values('ghg')
# Create spider plot.
ax = sp.spiderplot(x="product", y="ghg", hue="Area", legend='full', data=df)#, palette="husl", rref=0)
# Adjust limits in radial direction.
ax.set_rlim([0, 2.5])
plt.show()


# REGIONS SPIDERPLOT
rgn_avg = cp.copy(new_cat_all)
rgn_avg[keep] = rgn_avg[keep].apply(lambda x: x*rgn_avg['population'])
rgn_avg = rgn_avg.groupby(['year', 'RGN11NM']).sum()
rgn_avg[keep] = rgn_avg[keep].apply(lambda x: x/rgn_avg['population'])

sns.set_style("whitegrid")
# Load some demo data.
df = rgn_avg.drop(['population', 'Income anonymised', 'total_ghg'], axis=1).stack().reset_index()
df.columns = ['year', 'Area', 'product', 'ghg']
df = df.loc[df['year'] == 2015]
df = df.sort_values('ghg')
# Create spider plot.
ax = sp.spiderplot(x="product", y="ghg", hue="Area", legend=False, data=df)#, palette="husl", rref=0, legend='full')
# Adjust limits in radial direction.
#ax.set_rlim([0, 2.5])
plt.show()


uk_avg = cp.copy(new_cat_all)
uk_avg[keep] = uk_avg[keep].apply(lambda x: x*uk_avg['population'])
uk_avg = uk_avg.groupby('year').sum()
uk_avg[keep] = uk_avg[keep].apply(lambda x: x/uk_avg['population'])


uk_avg[['grains, fruit, veg', 'other food and drinks', 'food (animal origin)']].plot()
#uk_avg[['grains', 'other food', 'meat', 'dairy and eggs', 'fruit and veg', 'drinks']].plot()

uk_avg[['private transport (land)', 'public transport (land and water)', 'air transport']].plot()

#items = ['other food', 'meat', 'dairy and eggs', 'clothing', 'home energy', 'private transport (land)', 'public transport (land and water)', 'air transport', 'total_ghg']

items = ['grains, fruit, veg', 'food (animal origin)', 'clothing', 'home energy', 
         'private transport (land)', 'public transport (land and water)', 'air transport', 'total_ghg']

for item in items:
    g=sns.FacetGrid(new_cat_all, row='year', col='RGN11NM')
    g.map(sns.scatterplot, 'Income anonymised', item)
    plt.savefig(eval("r'" + data_directory + "/Spatial_Emissions/outputs/facets/UK_regions_yrs_combined_scatter_" + item + ".png'"))

corr = new_cat_all.drop('population', axis=1).groupby(['RGN11NM', 'year']).corr()[['Income anonymised']].reset_index()
corr = corr.loc[corr['level_2'] != 'Income anonymised']

sns.scatterplot(data=corr, x='level_2', y='Income anonymised', hue='RGN11NM')

fig, ax = plt.subplots(figsize=(15,5))
sns.boxplot(ax=ax, data=corr, x='level_2', y='Income anonymised', hue='RGN11NM'); plt.xticks(rotation=45)

fig, ax = plt.subplots(figsize=(15,5))
sns.boxplot(ax=ax, data=corr, x='level_2', y='Income anonymised', hue='year'); plt.xticks(rotation=45)

for year in years:
    for item in items:
        temp = new_cat[year].loc[new_cat[year]['RGN11NM'] == 'London']
        temp.plot(column=item, legend=True)
        plt.title(item + '_' + str(year))
        plt.show()


fig, ax = plt.subplots(figsize=(15,5))
sns.lineplot(ax=ax, data=corr.loc[corr['RGN11NM'] == 'London'], x='year', y='Income anonymised', hue='level_2')

# by income decile
new_cat_all = pd.DataFrame(columns=new_cat[2017].columns)
for year in range(2007, 2018):
    temp = cp.copy(new_cat[year]); temp['year'] = year
    temp['q10'] = temp['Income anonymised'].map(mapclassify.Quantiles(temp['Income anonymised'], k=10))
    temp['q10'] = [x[0] for x in temp['q10']]
    new_cat_all = new_cat_all.append(temp)


uk_avg = cp.copy(new_cat_all)
uk_avg[keep] = uk_avg[keep].apply(lambda x: x*uk_avg['population'])
uk_avg = uk_avg.groupby(['year', 'q10']).sum()
uk_avg[keep] = uk_avg[keep].apply(lambda x: x/uk_avg['population'])

rgn_avg = cp.copy(new_cat_all)
rgn_avg[keep] = rgn_avg[keep].apply(lambda x: x*rgn_avg['population'])
rgn_avg = rgn_avg.groupby(['year', 'RGN11NM']).sum()
rgn_avg[keep] = rgn_avg[keep].apply(lambda x: x/rgn_avg['population'])

temp = rgn_avg[items].stack().reset_index()
temp.columns = ['year', 'rgn', 'product', 'ghg']
g=sns.FacetGrid(temp, col='rgn', row='product')
g.map(sns.barplot, 'year', 'ghg')

sns.barplot(data=rgn_avg.reset_index(), x='year', y='Income anonymised', hue='RGN11NM')

sns.lineplot(data=rgn_avg.reset_index(), x='year', y='total_ghg', hue='RGN11NM')
sns.lineplot(data=rgn_avg.reset_index(), x='year', y='Income anonymised', hue='RGN11NM')
fig, ax = plt.subplots(figsize=(15,5))
sns.scatterplot(ax=ax, data=rgn_avg.reset_index(), x='Income anonymised', y='total_ghg', hue='RGN11NM', size='year')

g=sns.facetgri

fig, ax = plt.subplots(figsize=(15,5))
sns.scatterplot(ax=ax, data=new_cat_all, x='Income anonymised', y='total_ghg', hue='RGN11NM', size='year')


categories = ['grains', 'other food', 'meat', 'dairy and eggs', 'fruit and veg', 'drinks']
data = uk_avg[categories].stack().reset_index(); data.columns = ['year', 'q10', 'category', 'ghg']; data['col'] = 'col'

g = sns.FacetGrid(data, row='col', col='q10', hue='category')
g.map(sns.lineplot, 'year', 'ghg')

g = sns.FacetGrid(data, row='col', col='category', hue='q10')
g.map(sns.lineplot, 'year', 'ghg')


uk_avg[['grains', 'other food', 'meat', 'dairy and eggs', 'fruit and veg', 'drinks']].plot()

uk_avg[['private transport (land)', 'public transport (land and water)', 'air transport']].plot()


# by region

uk_avg = cp.copy(new_cat_all)
uk_avg[keep] = uk_avg[keep].apply(lambda x: x*uk_avg['population'])
uk_avg = uk_avg.groupby(['year', 'RGN11NM']).sum()
uk_avg[keep] = uk_avg[keep].apply(lambda x: x/uk_avg['population'])


categories = ['grains', 'other food', 'meat', 'dairy and eggs', 'fruit and veg', 'drinks']
data = uk_avg[categories].stack().reset_index(); data.columns = ['year', 'q10', 'category', 'ghg']; data['col'] = 'col'

g = sns.FacetGrid(data, row='col', col='q10', hue='category')
g.map(sns.lineplot, 'year', 'ghg')

g = sns.FacetGrid(data, col='col', row='category', hue='q10')
g.map(sns.lineplot, 'year', 'ghg')


uk_avg[['grains', 'other food', 'meat', 'dairy and eggs', 'fruit and veg', 'drinks']].plot()

uk_avg[['private transport (land)', 'public transport (land and water)', 'air transport']].plot()




"""
data_2y = {}
for year in range(2007, 2017, 2):
    temp = lookup[['MSOA11CD', 'MSOA01CD']].drop_duplicates()
    temp = temp.loc[temp['MSOA11CD'].isin(new_cat[2017].index) == True]
    if (year != 2013):
        if year < 2014:
            oac_year = 'MSOA01CD'
        else: 
            oac_year = 'MSOA11CD'
        data_2y[year] = temp.set_index(oac_year)
        for cat in cats.tolist() + ['total_ghg', 'Income anonymised']:
            temp2 = new_cat[year][[cat, 'population']].join(new_cat[year + 1][[cat, 'population']], rsuffix='_+1')
            temp2 = (((temp2[cat] * temp2['population']) + (temp2[cat + '_+1'] * temp2['population_+1'])) / (temp2['population'] + temp2['population_+1']))
            data_2y[year] = data_2y[year].join(pd.DataFrame(temp2)).rename(columns={0:cat})

        data_2y[year]['population'] = data_2y[year][['population']].join(new_cat[year + 1][['population']], rsuffix='_+1').mean(1)
        
        if year < 2014:
            data_2y[year] = data_2y[year].set_index('MSOA11CD')
        else: 
            data_2y[year] = data_2y[year].drop('MSOA01CD', axis=1)
    else:
        data_2y[year] = temp.set_index('MSOA01CD').join(new_cat[year]).set_index('MSOA11CD')
        for cat in cats.tolist() + ['total_ghg', 'Income anonymised', 'population']:
            data_2y[year][cat] = (((data_2y[year][cat] * data_2y[year]['population']) + (new_cat[year + 1][cat] * new_cat[year + 1]['population'])) / 
                                  (data_2y[year]['population'] + new_cat[year + 1]['population']))
    print(year)
 """   
 
 
nw = {}
for cat in cats:
    nw[cat] = lookup[['MSOA11CD', 'MSOA01CD', 'LAD17NM', 'RGN11NM']].drop_duplicates()
    nw[cat] = nw[cat].loc[(nw[cat]['MSOA11CD'].isin(new_cat[2017].index) == True) & (nw[cat]['RGN11NM'] == 'North West')]
    for year in range(2007, 2018):
        temp = new_cat[year].loc[new_cat[year]['RGN11NM'] == 'North West'][[cat, 'Income anonymised']].rename(columns={cat:'ghg_' + str(year), 'Income anonymised':'income_' + str(year)})
        if year < 2014:
            nw[cat] = nw[cat].set_index('MSOA01CD').join(temp).reset_index()
        else:
            nw[cat] = nw[cat].set_index('MSOA11CD').join(temp).reset_index()
    nw[cat] = nw[cat].set_index(['MSOA11CD', 'MSOA01CD', 'LAD17NM', 'RGN11NM'])
    nw[cat].columns = pd.MultiIndex.from_arrays([[int(x.split('_')[1]) for x in nw[cat].columns], [x.split('_')[0] for x in nw[cat].columns]])
    nw[cat] = nw[cat].stack(level=0).reset_index().rename(columns={'level_4':'year'})
    
nw_all = pd.DataFrame(columns = nw[cat].columns.tolist() + ['category'])
for cat in cats:
    temp = cp.copy(nw[cat])
    temp['category'] = cat
    nw_all = nw_all.append(temp)
    
"""
g = sns.FacetGrid(nw_all, col='category',  row="LAD17NM")
g.map(sns.boxplot, "year", "ghg")
plt.savefig(eval("r'" + data_directory + "/Spatial_Emissions/outputs/facets/north_west_boxplot.png'"))
"""

g = sns.FacetGrid(nw_all, col='category',  row="LAD17NM")
g.map(sns.scatterplot, "income", "ghg")
plt.savefig(eval("r'" + data_directory + "/Spatial_Emissions/outputs/facets/north_west_scatter.png'"))

manchester = nw_all.loc[nw_all['LAD17NM'] == 'Manchester']
liverpool = nw_all.loc[nw_all['LAD17NM'] == 'Liverpool']

for cat in cats:
    fig, ax = plt.subplots()
    sns.scatterplot(ax=ax, data=nw_all, x='Income anonymised', y='ghg')
    sns.scatterplot(ax=ax, data=manchester, x='Income anonymised', y='ghg', c='red')
    plt.show()
    
nw_all['manchester'] = False; nw_all.loc[nw_all['LAD17NM'] == 'Manchester', 'manchester'] = True
g = sns.FacetGrid(nw_all, col='category',  row="year", hue="manchester")
g.map(sns.scatterplot, "income", "ghg")
plt.savefig(eval("r'" + data_directory + "/Spatial_Emissions/outputs/facets/manchester_scatter.png'"))


nw_all['liverpool'] = False; nw_all.loc[nw_all['LAD17NM'] == 'Liverpool', 'liverpool'] = True
g = sns.FacetGrid(nw_all, col='category',  row="year", hue="liverpool")
g.map(sns.scatterplot, "income", "ghg")
plt.savefig(eval("r'" + data_directory + "/Spatial_Emissions/outputs/facets/liverpool_scatter.png'"))


    
    
    

# check petrol emissions
keep = ['7.2.2.1', '7.2.2.2', '7.2.2.3']
for year in range(2007, 2018):
    temp = data[year][keep + ['geometry']]
    fig, axs = plt.subplots(ncols=3)
    for i in range(3):
        temp.plot(ax=axs[i], column=keep[i], legend=True)
        axs[i].set_title(str(year))
        
for year in range(2007, 2018):
    temp = pd.DataFrame(data[year][keep].stack()).reset_index()
    temp.columns = [temp.columns.tolist()[0], 'ccp', 'ghg']
    temp = temp.set_index(temp.columns.tolist()[0])
    temp = temp.join(data[year][['Income anonymised']])
    sns.scatterplot(data=temp, x='Income anonymised', y='ghg', hue='ccp'); plt.title(str(year)); plt.show()


# add income deciles from 2007
q_07 = mapclassify.Quantiles(data[2007]['Income anonymised'], k=10)
q_07_msoas = cp.copy(data[2007])
q_07_msoas['q_07'] = q_07_msoas['Income anonymised'].map(q_07); q_07_msoas['q_07'] = ['Q' + str(x[0] + 1) for x in q_07_msoas['q_07']]
q_07_dict = dict(zip(q_07_msoas.index, q_07_msoas['q_07']))


all_data = pd.DataFrame(columns= data[2007].columns.to_list() + ['year', 'q_07'])
for year in range(2007, 2018):
    temp = cp.copy(data[year])
    temp['year'] = year
    temp['q_07'] = temp.index.map(q_07_dict)
    all_data = all_data.append(temp)
    
# facetgrid
temp = all_data[['RGN11NM', 'year', 'Income anonymised']]
temp['petrol'] = all_data[['7.2.2.1', '7.2.2.2', '7.2.2.3']].sum(1)
g = sns.FacetGrid(temp, col='RGN11NM',  row="year")
g.map(sns.scatterplot, "Income anonymised", "petrol")


facet_data = all_data.set_index(['year', 'RGN11NM'], append=True).loc[:, '1.1.1.1':'12.5.3.5']
facet_data.columns = [x.split('.')[0] for x in facet_data.columns]
facet_data = facet_data.sum(axis=1, level=0).reset_index(level=[1, 2]).join(all_data['Income anonymised'])
for item in range(1, 13):
    g = sns.FacetGrid(facet_data, col='RGN11NM',  row='year')
    g.map(sns.scatterplot, 'Income anonymised', str(item))
    plt.savefig(eval("r'" + data_directory + "/Spatial_Emissions/outputs/facets/" + str(item) + ".png'"))



    
all_data_corr = all_data[['Income anonymised', 'total_ghg', 'year']].groupby('year').corr()[['Income anonymised']].reset_index()
all_data_corr = all_data_corr.loc[all_data_corr['level_1'] == 'total_ghg']


# plot product emissions over time
temp = all_data.loc[:,'1.1.1.1':'year']
temp.columns = [x.split('.')[0] for x in temp.loc[:,'1.1.1.1':'12.5.3.5'].columns] + ['population', 'Income anonymised', 'total_ghg', 'year']
temp = temp.sum(axis=1, level=0)
save  = temp.drop('population', axis=1)
keep = temp.loc[:,'1':'12'].columns.tolist() + ['Income anonymised']
temp.loc[:,keep] = temp.loc[:,keep].apply(lambda x: x*temp['population'])
temp = temp.groupby('year').sum()
temp = temp.apply(lambda x: x/temp['population']).loc[:,keep]
temp.plot(); plt.show();
plot_data = temp

ccp_labels = ['Food & Drinks', 'Alcohol & Tobacco', 'Clothing & Footwear', 'Housing', 'Furnishings', 'Health', 'Transport', 'Communication', 'Recreation & Culture', 
              'Education', 'Restaurants & Hotels', 'Miscellaneous']
ccp1_dict = dict(zip([str(x) for x in range(1,13)], ccp_labels))
product_year = temp.stack().reset_index(); product_year.columns = ['Year', 'Product/Service (COICOP 1)', 'tCO2e per capita']
product_year['Year'] = product_year['Year'].astype(int)
income_year = product_year.loc[product_year['Product/Service (COICOP 1)'] == 'Income anonymised']; income_year.columns = ['Year', 'Income', 'Mean income']
product_year = product_year.loc[product_year['Product/Service (COICOP 1)'] != 'Income anonymised']
product_year['Product/Service (COICOP 1)'] = product_year['Product/Service (COICOP 1)'].map(ccp1_dict)


# Look at correlations
ccp1_corr = pd.DataFrame(save.groupby('year').corr()[['Income anonymised']]).join(pd.DataFrame(plot_data.stack())).reset_index()\
    .rename(columns={0:'ghg', 'Income anonymised':'pearson_r', 'level_1':'ccp1'})
ccp1_corr = ccp1_corr.loc[(ccp1_corr['ccp1'] != 'Income anonymised') & (ccp1_corr['ccp1'] != 'total ghg')]
ccp1_corr['Product'] = ccp1_corr['ccp1'].map(ccp1_dict)
fig, ax = plt.subplots(figsize=(15, 10)); sns.scatterplot(data=ccp1_corr, x='ghg', y='pearson_r', hue='Product', size='year', palette='colorblind');
ax.set_xlabel('tCO2e per capita (UK mean)'); ax.set_ylabel('Correlation Coefficient'); ax.set_xlim(0, 5)
plt.savefig(eval("r'" + output_directory + "/outputs/Graphs/ghg_pearson_scatter.png'"), bbox_inch='tight', dpi=150)


transport_lookup = pd.read_csv(eval("r'" + data_directory + "/data/processed/transport_ccp4_lookup.csv'"))
transport_lookup['Kind']= 'Land_Public'
transport_lookup.loc[transport_lookup['kind'] == 'Air', 'Kind'] = 'Air'
transport_lookup.loc[transport_lookup['owned'] == 'Private', 'Kind'] = 'Land_Private'
transport_dict = dict(zip(transport_lookup['ccp4'], transport_lookup['Kind']))
ccp4_corr = all_data[all_data.loc[:,'7.1.1.1':'7.3.4.8'].columns.tolist() + ['year', 'Income anonymised']]\
    .rename(columns=transport_dict).sum(axis=1, level=0).groupby('year').corr()[['Income anonymised']]
ccp4_ghg = all_data[all_data.loc[:,'7.1.1.1':'7.3.4.8'].columns.tolist() + ['year', 'Income anonymised', 'population']].rename(columns=transport_dict).sum(axis=1, level=0)

plot_data = pd.DataFrame(ccp4_ghg.set_index(['Income anonymised', 'year'], append=True).drop('population', axis=1).stack()).reset_index()\
    .rename(columns={0:'ghg', 'level_3':'Kind', 'level_0':'MSOA'})
fig, ax = plt.subplots(figsize=(8, 8)); sns.scatterplot(data=plot_data.loc[plot_data['Kind']=='Air'], y='ghg', x='Income anonymised', hue='Kind');

ccp4_ghg.iloc[:,:-3] = ccp4_ghg.iloc[:,:-3].apply(lambda x: x*ccp4_ghg['population'])
ccp4_ghg = ccp4_ghg.groupby('year').sum()
ccp4_ghg = ccp4_ghg.iloc[:,:-1].apply(lambda x: x/ccp4_ghg['population'])
ccp4_corr = ccp4_corr.join(pd.DataFrame(ccp4_ghg.stack())).reset_index().rename(columns={0:'ghg', 'Income anonymised':'pearson_r', 'level_1':'Kind'})
ccp4_corr = ccp4_corr.loc[(ccp4_corr['Kind'] != 'Income anonymised')]
fig, ax = plt.subplots(figsize=(8, 8)); sns.scatterplot(data=ccp4_corr, x='ghg', y='pearson_r', hue='Kind', size='year');

ccp4_ghg.columns = [x.split('.')[0] for x in temp.loc[:,'1.1.1.1':'12.5.3.5'].columns] + ['population', 'Income anonymised', 'total_ghg', 'year']
temp = temp.sum(axis=1, level=0)
save  = temp.drop('population', axis=1)
keep = temp.loc[:,'1':'12'].columns.tolist() + ['Income anonymised']
temp.loc[:,keep] = temp.loc[:,keep].apply(lambda x: x*temp['population'])
temp = temp.groupby('year').sum()
temp = temp.apply(lambda x: x/temp['population']).loc[:,keep]
temp.plot(); plt.show();
plot_data = temp





product_year = product_year.loc[product_year['Product/Service (COICOP 1)'] != 'Income anonymised']

sns.lineplot(data=product_year, x='Year', y='tCO2e per capita', hue='Product/Service (COICOP 1)', palette='colorblind'); plt.show();

# Creating plot with dataset_1
fig, ax1 = plt.subplots(figsize=(12,8)) 
# ghg
sns.lineplot(data=product_year, x='Year', y='tCO2e per capita', hue='Product/Service (COICOP 1)', palette="Paired", ax=ax1, legend=False);
ax1.set_xlabel('Year') 
ax1.set_ylabel('tCO2e per capita', color = 'k') 
ax1.set_ylim(0, 6)
#plt.savefig(eval("r'" + output_directory + "/outputs/GISRUK_legend.png'"), bbox_inch='tight', dpi=150)
# Adding Twin Axes to plot using dataset_2
ax2 = ax1.twinx() 
sns.lineplot(data=income_year, x='Year', y='Mean income', ax=ax2, color='k', legend=False);
ax2.lines[0].set_linestyle(":")
ax2.set_ylabel('Income per capita', color = 'k')
ax2.set_ylim(0, 400)
# Show plot
plt.savefig(eval("r'" + output_directory + "/outputs/GISRUK_plot.png'"), bbox_inch='tight', dpi=150)
plt.show();

#stacked plot

# set seaborn style
fig, ax1 = plt.subplots(figsize=(12,8)) 
# ghg
sns.lineplot(data=product_year, x='Year', y='tCO2e per capita', hue='Product/Service (COICOP 1)', palette="Paired", ax=ax1, legend=False);
for item in ['Housing', 'Transport', 'Food & Drinks', 'Recreation & Culture', 'Restaurants & Hotels']:
    y = product_year.loc[(product_year['Product/Service (COICOP 1)'] == item) & (product_year['Year'] <= 2008)]['tCO2e per capita'].tolist()
    if y[0] < y[1]:
        y = y[0] + 0.25
    else:
        y = y[0]
    ax1.text(x=2007.25, y=y, s=item)
ax1.set_xlabel('Year') 
ax1.set_ylabel('tCO2e per capita', color = 'k') 
ax1.set_ylim(0, 6)
#plt.savefig(eval("r'" + output_directory + "/outputs/GISRUK_legend.png'"), bbox_inch='tight', dpi=150)
# Adding Twin Axes to plot using dataset_2
ax2 = ax1.twinx() 
sns.lineplot(data=income_year, x='Year', y='Mean income', ax=ax2, color='k', legend=False);
ax2.lines[0].set_linestyle(":")
ax2.set_ylabel('Income per capita', color = 'k')
ax2.set_ylim(0, 400)
ax2.text(x=2016, y=370, s='Income')
# Show plot
plt.savefig(eval("r'" + output_directory + "/outputs/GISRUK_plot.png'"), bbox_inch='tight', dpi=150)
plt.show();



# stacked plot
years = list(range(2007, 2018))
fig, ax1 = plt.subplots(figsize=(12,8)) 
# ghg
plot_data = plot_data.rename(columns=ccp1_dict) 
plot_data.iloc[:, :-1].plot.area(cmap='Paired', ax=ax1)
ax1.legend(fontsize=10, ncol=4)
ax1.text(x=2007.25, y=0.5, s='Food & Drinks')
ax1.text(x=2007.25, y=3.75, s='Housing')
ax1.text(x=2007.25, y=8, s='Transport')
ax1.set_xlabel('Year') 
ax1.set_ylabel('tCO2e per capita', color = 'k') 
ax1.set_ylim(0, 16)
ax2.set_xlim(2007, 2017)
# Adding Twin Axes to plot using dataset_2
ax2 = ax1.twinx() 
sns.lineplot(data=income_year, x='Year', y='Mean income', ax=ax2, color='k', legend=False);
ax2.lines[0].set_linestyle(":")
ax2.set_ylabel('Income per capita', color = 'k')
ax2.set_ylim(0, 450)
ax2.set_xlim(2007, 2017)
ax2.text(x=2016, y=370, s='Income')
# Show plot
plt.savefig(eval("r'" + output_directory + "/outputs/GISRUK_plot_stacked.png'"), bbox_inch='tight', dpi=150)
plt.show();



all_data = all_data[['RGN11NM', 'population', 'Income anonymised', 'total_ghg', 'year', 'q_07']]



sns.lineplot(x='year', y='total_ghg', hue='q_07', data=all_data.dropna(how='any'))

# add income deciles from each year individually
all_data = pd.DataFrame(columns= data[2007].columns.to_list() + ['year', 'q_inc'])
for year in range(2007, 2018):
    temp = cp.copy(data[year])
    temp['year'] = year
    
    q = mapclassify.Quantiles(data[year]['Income anonymised'], k=10)
    temp['q_inc'] = temp['Income anonymised'].map(q_07); temp['q_inc'] = ['Q' + str(x[0] + 1) for x in temp['q_inc']]
    
    all_data = all_data.append(temp)

all_data.index.name = 'MSOA'
all_data = all_data[['RGN11NM', 'population', 'Income anonymised', 'total_ghg', 'year', 'q_inc']]
sns.lineplot(x='year', y='total_ghg', hue='q_inc', data=all_data.dropna(how='any'))


sns.lineplot(x='year', y='total_ghg', hue='q_inc', data=all_data.dropna(how='any'))

sns.lmplot(x='total_ghg', y='Income anonymised', hue='year', data=all_data, scatter_kws ={'s':0.1, 'alpha':0.2})
 


check3 = sm.OLS(all_data['total_ghg'], all_data[['Income anonymised', 'year']].astype(float)).fit()
check3.summary()


# Model GHG totals over time!
models = {}
models['all'] = sm.OLS(all_data['total_ghg'], all_data['Income anonymised']).fit()
for year in range(2007, 2018):
    temp = all_data.loc[all_data['year'] == year]
    models[year] = sm.OLS(temp['total_ghg'], temp['Income anonymised']).fit()
    print(models[year].summary())
  

cross_validation = {year:data[year][['total_ghg', 'Income anonymised']] for year in range(2007, 2018)}
for year in range(2007, 2018):
    random.seed(year)
    cross_validation[year] = cross_validation[year].sample(frac=1)
    cross_validation[year]['group'] = np.repeat(list(range(10)), math.ceil(len(cross_validation[year])/10), axis=0)[:len(cross_validation[year])]

results = {}; models = {}
for year in range(2007, 2018):
    results[year] = pd.DataFrame()
    models[year] = {}
    for i in range(10):
        train = cross_validation[year].loc[cross_validation[year]['group'] != i]
        test = cross_validation[year].loc[cross_validation[year]['group'] == i]
        models[year][i] = sm.OLS(train['total_ghg'], train['Income anonymised']).fit()
        test['predict'] = models[year][i].predict(test['Income anonymised'])
        results[year] = results[year].append(test)
    results[year]['difference'] = results[year]['total_ghg'] - results[year]['predict']
 
    
for year in range(2007, 2018):
    results[year]['group'] = 'G' + results[year]['group'].astype(str)
    sns.scatterplot(data=results[year], x='total_ghg', y='predict', hue='group')
    plt.show()
    print(results[year].groupby('group').mean())
    
results_rmse = pd.DataFrame(index=list(range(2007, 2018)))
import math
for year in range(2007, 2018):
    MSE = np.square(results[year]['difference']).mean()
    RMSE = math.sqrt(MSE)
    results_rmse.loc[year, 'Predict own year'] = RMSE
    
results_2017 = data[2017][['total_ghg']]
for year in range(2007, 2018):
    temp = pd.DataFrame(index= data[2017].index)
    for i in range(10):
        temp[i] = models[year][i].predict(data[2017]['Income anonymised'])
    results_2017[year] = temp.mean(1)
    
for year in range(2007, 2018):
    MSE = np.square(np.subtract(results_2017['total_ghg'], results_2017[year])).mean()
    RMSE = math.sqrt(MSE)
    results_rmse.loc[year, 'Predict 2017'] = RMSE

fig, ax = plt.subplots(figsize=(5,5))
sns.heatmap(ax=ax, data=results_rmse, cmap='Greens', annot=True)
plt.savefig(eval("r'" + output_directory + "/outputs/model_heatmap.png'"), bbox_inches='tight', dpi=150)


# Model 2020 products by 2017 data

models_2017 = {}
data_2017 = cp.copy(data[2017]).drop('geometry', axis=1)
data_2017.columns = ['RGN11NM'] + [x.split('.')[0] for x in data_2017.loc[:,'1.1.1.1':'12.5.3.5'].columns] + ['population', 'Income anonymised', 'total_ghg']
data_2017 = data_2017.sum(axis=1, level=0).set_index(['RGN11NM', 'population', 'Income anonymised', 'total_ghg'], append=True).stack().reset_index()\
    .rename(columns={'level_5':'ccp1', 0:'ghg'})


cross_validation = {x:data_2017.loc[data_2017['ccp1'] == str(x)] for x in range(1, 13)}
for x in range(1, 13):
    random.seed(x)
    cross_validation[x] = cross_validation[x].sample(frac=1)
    cross_validation[x]['group'] = np.repeat(list(range(10)), math.ceil(len(cross_validation[x])/10), axis=0)[:len(cross_validation[x])]

results = {}
for x in range(1, 13):
    results[x] = pd.DataFrame()
    models_2017[x] = {}
    for i in range(10):
        train = cross_validation[x].loc[cross_validation[x]['group'] != i]
        test = cross_validation[x].loc[cross_validation[x]['group'] == i]
        models_2017[x][i] = sm.OLS(train['ghg'], train['Income anonymised']).fit()
        test['predict'] = models_2017[x][i].predict(test['Income anonymised'])
        results[x] = results[x].append(test)
    results[x]['difference'] = results[x]['ghg'] - results[x]['predict']
        
for x in range(1, 13):
    results[x]['group'] = 'G' + results[x]['group'].astype(str)
    sns.scatterplot(data=results[x], x='ghg', y='predict', hue='group')
    plt.show()
    print(results[x].groupby('group').mean())
    

####### 2020 income data:
    
# pct_change = [4, -0.5, -2, -4, -5, -5, -6, -7, -7.5, -16]
# import income data
    
change = {}; change['may'] = {}; change['nov'] = {}
change['may']['w_policy'] = [4, -0.5, -2, -4, -5, -5, -6, -7, -7.5, -7.5]
change['may']['wo_policy'] = [-29, -29, -30, -30.5, -19.5, -30.5, -30.5, -31, -27, -27]
change['nov']['w_policy'] = [4.5, -0.5, -2, -4, -5, -5, -6, -7.5, -7.5, -7.5]
change['nov']['wo_policy'] = [-15.5, -15.5, -15.5, -17.5, -15.5, -15.5, -17.5, -17, -17.5, -17.5]
    
imd_2019 = pd.read_excel(eval("r'" + data_directory + "/data/raw/imd_2019.xlsx'"), sheet_name='IoD2019 Domains').set_index('LSOA code (2011)')
imd_2019 = imd_2019.join(lookup[['LSOA11CD', 'MSOA11CD']].drop_duplicates().set_index('LSOA11CD'))
imd_2019 = imd_2019[['MSOA11CD', 'Income Rank (where 1 is most deprived)', 'Income Decile (where 1 is most deprived 10% of LSOAs)']].groupby('MSOA11CD').median()
imd_2019['msoa_decile'] = imd_2019['Income Decile (where 1 is most deprived 10% of LSOAs)'].round(0).astype(int)

incomes_2020 = imd_2019.join(data[2017]['Income anonymised'])
for month in ['may', 'nov']:
    for policy in ['w_policy', 'wo_policy']:
        income_change = incomes_2020['msoa_decile'].map(dict(zip(list(range(1, 11)), change[month][policy])))
        incomes_2020['income_' + month + '_' + policy] = incomes_2020['Income anonymised'] * (1 + (income_change / 100))
        

cols = pd.MultiIndex.from_arrays([['may_2020' for x in range(24)] + ['nov_2020' for x in range(24)],
                                  ((['w_policy'] * 12) + (['wo_policy'] * 12)) * 2,
                                  [str(x) for x in range(1,13)] * 4])
        


total_ghg_2020 = pd.DataFrame(index = incomes_2020.index)
for month in ['may', 'nov']:
    for policy in ['w_policy', 'wo_policy']:
        temp = pd.DataFrame(index=incomes_2020.index)
        for i in list(models[2017].keys()):
            temp[i] = models[2017][i].predict(incomes_2020['income_' + month + '_' + policy])
        total_ghg_2020[(month, policy)] = temp.mean(axis=1)

check3 = total_ghg_2020.join(data[2017][['total_ghg', 'population']]).drop_duplicates()
check3.iloc[:,:-1] = check3.iloc[:,:-1].apply(lambda x: x*check3['population'])
check3 = pd.DataFrame(check3.sum()).T
check3 = check3.iloc[:,:-1].apply(lambda x: x/check3['population'])
check3.columns = ['May_policy', 'May_reg', 'Nov_policy', 'Nov_reg', 'Control_2017']; check3.index=['mean_ghg']
check3.T.to_csv(eval("r'" + data_directory + "/data/processed/pred_values_means.csv'"))

check3.plot.bar()

income_means = income_2020_all.set_index(['date', 'month'])[['pcincome_week']].astype(float).mean(level=[0,1])
uss_ghg = cp.copy(income_means)
temp = pd.DataFrame(index=income_means.index)
for i in list(models[2017].keys()):
    temp[i] = models[2017][i].predict(income_means['pcincome_week'])
uss_ghg['predict'] = temp.mean(axis=1)   

temp = data[2017][['population', 'Income anonymised', 'total_ghg']]
temp.iloc[:,1:] = temp.iloc[:,1:].apply(lambda x: x*temp['population'])
temp = temp.sum()
uss_ghg.loc[('2017-06', '2017'), 'pcincome_week'] = temp['Income anonymised'] / temp['population']
uss_ghg.loc[('2017-06', '2017'), 'predict'] = temp['total_ghg'] / temp['population']

from datetime import datetime
uss_ghg = uss_ghg.reset_index()
uss_ghg['datetime'] = pd.to_datetime(uss_ghg['date']).dt.date

sns.barplot(data=uss_ghg.sort_values('datetime'), x='month', y='predict', color='r')
# twin

fig, ax1 = plt.subplots(figsize=(5,6.5)) 
# ghg
uss_ghg.sort_values('datetime').set_index('date')[['predict']].plot.bar(cmap='Paired', ax=ax1, legend=False)
#ax1.legend(fontsize=10, ncol=4)
ax1.set_xlabel('') 
ax1.set_ylabel('tCO2e per capita', color = '#00698b') 
ax1.set_ylim(0, 10)
# Adding Twin Axes to plot using dataset_2
ax2 = ax1.twinx() 
sns.lineplot(data=uss_ghg.sort_values('datetime'), x='date', y='pcincome_week', ax=ax2, color='#8b0000', legend=False);
#ax2.lines[0].set_linestyle(":")
ax2.set_ylabel('Income per capita', color = '#8b0000')
ax2.set_ylim(0, 500)
# Show plot
plt.savefig(eval("r'" + output_directory + "/outputs/GISRUK_plot_stacked_covidincome.png'"), bbox_inches='tight', dpi=150)
plt.show();

temp = {}; temp_msoa = {}
for year in [2007, 2008, 2009]:
    temp[year] = data[year].loc[:,'1.1.1.1':'population']
    temp[year].columns = [x.split('.')[0] for x in temp[year].loc[:,:'12.5.3.5'].columns] + ['population']
    temp[year] = temp[year].sum(axis=1, level=0)
    temp_msoa[year] = cp.copy(temp[year])
    
    temp[year].loc[:,:'12'] = temp[year].loc[:,:'12'].apply(lambda x: x* temp[year]['population'])
    temp[year] = temp[year].sum(axis=0)
    for i in range(1,13):
        temp[year][str(i)] = temp[year][str(i)] / temp[year]['population']
    
    
econ_crisis = pd.DataFrame(temp[2007]).join(pd.DataFrame(temp[2008]), lsuffix='_07', rsuffix='_08').join(pd.DataFrame(temp[2009])).T
econ_crisis.index = [2007, 2008, 2009]

econ_crisis.drop('population', axis=1).plot()

econ_crisis.drop('population', axis=1).plot.area(cmap='Paired')

econ_msoa = pd.DataFrame(index=temp_msoa[2007].index, columns=pd.MultiIndex.from_arrays([['test'], ['test']]))
for year in [2007, 2008, 2009]:
    temp = temp_msoa[year].drop('population', axis=1)
    temp.columns = pd.MultiIndex.from_arrays([[year]*len(temp.columns), temp.columns.tolist()])
    econ_msoa = econ_msoa.join(temp)
econ_msoa = econ_msoa.drop(('test', 'test'), axis=1) 


temp = econ_msoa.sum(axis=1, level=0)

temp = econ_msoa.stack(level=[0,1]).reset_index(); temp.columns=['MSOA', 'year', 'Product/Service', 'tCO2e per capita']
temp['Product/Service'] = temp['Product/Service'].map(ccp1_dict)

fig, ax=plt.subplots(figsize=(7,4))
sns.boxplot(ax=ax, data=temp, hue='year', y='tCO2e per capita', x='Product/Service', palette='Paired'); #ax.set_xscale('log')


sns.lmplot(data=all_data, x='Income anonymised', y='total_ghg', hue='year')

all_data.to_csv(eval("r'" + output_directory + "/outputs/all_data_for_plot_GISRUK.csv'"))




check2 = total_ghg_2020.join(data[2017][['total_ghg']])
check2.columns = ['May_policy', 'May_reg', 'Nov_policy', 'Nov_reg', 'Control_2017']
check2.to_csv(eval("r'" + data_directory + "/data/processed/pred_values_total_ghg.csv'"))

check_msoa = check2.join(imd_2019[['msoa_decile']]).join(data[2017][['population']])
check_msoa.iloc[:,:-2] = check_msoa.iloc[:,:-2].apply(lambda x: x*check_msoa['population'])
check_msoa = check_msoa.groupby('msoa_decile').sum()
check_msoa.iloc[:,:-1] = check_msoa.iloc[:,:-1].apply(lambda x: x/check_msoa['population'])

for item in check_msoa.columns[:-2]:
    check_msoa['pct_change_' + item] = (check_msoa['Control_2017'] - check_msoa[item]) / check_msoa['Control_2017'] * 100

check_msoa.to_csv(eval("r'" + data_directory + "/data/processed/pred_values_total_ghg_byIMD.csv'"))

income_2020_all.set_index('month')[['hhincome_week', 'pcincome_week', 'ghhincome_week', 'gpcincome_week']].astype(float).mean(level=0)


ghg_2020 = pd.DataFrame(columns = cols, index = incomes_2020.index)
for month in ['may', 'nov']:
    for x in range(1, 13):
        for policy in ['w_policy', 'wo_policy']:
            temp = pd.DataFrame(index=incomes_2020.index)
            for i in list(models_2017[x].keys()):
                temp[i] = models_2017[x][i].predict(incomes_2020['income_' + month + '_' + policy])
            ghg_2020[(month + '_2020', policy, str(x))] = temp.mean(axis=1)

temp = data[2017][['population']]; temp.columns = pd.MultiIndex.from_arrays([['pop'], ['pop'], ['pop']])
check = ghg_2020.join(temp)
check.iloc[:,:-1] = check.iloc[:,:-1].apply(lambda x: x*check[('pop', 'pop', 'pop')])
check = pd.DataFrame(check.sum(axis=0)).T
check.iloc[:,:-1] = check.iloc[:,:-1].apply(lambda x: x/check[('pop', 'pop', 'pop')])
check = check.drop(('pop', 'pop', 'pop'), axis=1).T.unstack(level=2).reset_index()

fig, ax = plt.subplots()
bottom = [0, 0, 0, 0]
for i in range(1, 13):
    top = check[(0, str(i))]
    ax.bar(height=top, bottom=bottom, x=check['level_0'] + '_' + check['level_1'])
    bottom += top

temp = data[2017].loc[:,'1.1.1.1':'12.5.3.5']; temp.columns = [x.split('.')[0] for x in temp.columns]
temp = temp.sum(axis=1, level=0).join(data[2017][['population']]).join(imd_2019[['msoa_decile']]); 
temp.columns = pd.MultiIndex.from_arrays([['baseline']*len(temp.columns.tolist()), ['baseline']*len(temp.columns.tolist()), temp.columns.tolist()])
by_imd = ghg_2020.join(temp)
by_imd.iloc[:,:-2] = by_imd.iloc[:,:-2].apply(lambda x: x*by_imd[('baseline', 'baseline', 'population')])
by_imd = by_imd.groupby(('baseline', 'baseline', 'msoa_decile')).sum()
by_imd.iloc[:,:-1] = by_imd.iloc[:,:-1].apply(lambda x: x/by_imd[('baseline', 'baseline', 'population')])

plot = by_imd.drop(('baseline', 'baseline', 'population'), axis=1).stack(level=2).unstack(level=0).T.reset_index()
plot2 = plot.set_index(['level_0', 'level_1', ('baseline', 'baseline', 'msoa_decile')]).unstack(level=[0,1])
plot = plot.loc[plot['level_1'] != 'w_policy']
plot = plot.loc[plot['level_0'] != 'may_2020']
fig, ax = plt.subplots(figsize=(15, 5))
bottom = [0] * len(plot)
for i in range(1, 13):
    top = plot[str(i)]
    x= plot['level_0'].str[0] + plot[('baseline', 'baseline', 'msoa_decile')].astype(str)
    ax.bar(height=top, bottom=bottom, x=x)
    bottom += top
    
plot = by_imd.drop(('baseline', 'baseline', 'population'), axis=1).stack(level=2).unstack(level=0).T.reset_index()
plot2 = plot.set_index(['level_0', 'level_1', ('baseline', 'baseline', 'msoa_decile')]).unstack(level=[0,1])
plot = plot.loc[plot['level_1'] == 'baseline']
fig, ax = plt.subplots(figsize=(7.5, 5))
bottom = [0] * len(plot)
for i in range(1, 13):
    top = plot[str(i)]
    x= plot['level_0'].str[0] + plot[('baseline', 'baseline', 'msoa_decile')].astype(str)
    ax.bar(height=top, bottom=bottom, x=x)
    bottom += top
    
plot.loc[:,'1':].rename(columns=ccp1_dict).plot(cmap='Paired')

    
plot3 = plot.set_index(('baseline', 'baseline', 'msoa_decile')).drop(['level_0', 'level_1'], axis=1).stack().reset_index()
plot3.columns = ['Income Decile', 'Product/Service', 'tCO2e per capita']
plot3['Product / Service'] = plot3['Product/Service'].map(ccp1_dict)

sns.lineplot(data=plot3, x='Income Decile', y='tCO2e per capita', hue='Product / Service', palette='Paired'); #plt.yscale('log')

temp = plot3.groupby('Product/Service').mean()[['tCO2e per capita']]; temp.columns=['mean']

plot3=plot3.merge(temp.reset_index(), on='Product/Service')
fig, ax = plt.subplots(figsize=(15, 10))
sns.barplot(ax=ax, data=plot3.sort_values('mean'), x='Income Decile', y='tCO2e per capita', hue='Product / Service', palette='Paired')
 
fig, ax = plt.subplots(figsize=(7.5, 5))
sns.barplot(ax=ax, data=plot3.sort_values('mean'), hue='Income Decile', x='tCO2e per capita', y='Product / Service', palette='Paired_r')
  
fig, ax = plt.subplots(figsize=(15, 5))
sns.barplot(ax=ax, data=plot3.sort_values('mean'), hue='Income Decile', y='tCO2e per capita', x='Product / Service', palette='Paired')
plt.xticks(rotation=90);
plt.savefig(eval("r'" + output_directory + "/outputs/Graphs/income_decile_2017_ghg.png'"), bbox_inches='tight', dpi=150)

  
   
for month in ['may_2020', 'nov_2020']:
    for policy in ['w_policy', 'wo_policy']:
        for i in range(1, 13):
            plot2[('pct_change_' + str(i), month, policy)] = (plot2[(str(i), 'baseline', 'baseline')] - plot2[(str(i), month, policy)]) / plot2[(str(i), 'baseline', 'baseline')] * 100
plot2.to_csv(eval("r'" + data_directory + "/data/processed/pred_values_product_ghg_byIMD.csv'"))
check_msoa.to_csv(eval("r'" + data_directory + "/data/processed/pred_values_total_ghg_byIMD.csv'"))

temp = by_imd.drop(('baseline', 'baseline', 'population'), axis=1).sum(axis=1, level=[0,1])
temp.plot.bar()

temp = by_imd.sum(axis=1, level=[0,1]).drop('pop', axis=1).unstack().reset_index(); temp.columns=['month', 'policy', 'imd', 'ghg']

sns.barplot(data=temp.loc[temp['month'] == 'may_2020'], x='imd', y='ghg', hue='policy')
sns.barplot(data=temp.loc[temp['month'] == 'nov_2020'], x='imd', y='ghg', hue='policy')

plot = by_imd.drop(('baseline', 'baseline', 'population'), axis=1).stack(level=2).unstack(level=0).T.sum(axis=1).reset_index()
plot.columns = ['year', 'policy', 'decile', 'ghg']
plot['group'] = plot['year'].str[0] + plot['policy'].str[:2]
sns.barplot(data=plot, x='decile', y='ghg', hue='group')
sns.barplot(data=temp.loc[temp['month'] == 'nov_2020'], x='imd', y='ghg', hue='policy')


stacked_2017 = data_2017[['MSOA11CD', 'ccp1', 'ghg']].rename(columns={'ghg':2017}).drop_duplicates().rename(columns={2017:'ghg'})
stacked_2017['year'] = '2017'
     

# with policy
w_policy = ghg_2020.stack(level=2).stack(level=1).stack(level=0).reset_index(); w_policy.columns = ['MSOA11CD', 'ccp1', 'policy',  'year', 'ghg']
w_policy = w_policy.loc[w_policy['policy'] == 'w_policy'].append(stacked_2017)
    
sns.boxplot(data=w_policy, x='ccp1', y='ghg', hue='year'); plt.show();

temp = w_policy.groupby(['MSOA11CD', 'year']).sum().join(imd_2019[['msoa_decile']]).reset_index()
sns.boxplot(data=temp, x='msoa_decile', y='ghg', hue='year'); plt.show();

temp2 = data[2017][['geometry']].join(temp.set_index('MSOA11CD'))

for year in ['2017', 'may_2020', 'nov_2020']:
    mean = temp2.loc[temp2['year'] == year]['ghg'].mean()
    sd = temp2.loc[temp2['year'] == year]['ghg'].std()
    temp2.loc[(temp2['year'] == year) & (temp2['ghg'] > mean + 3 * sd), 'ghg'] = mean + 3 * sd
    temp2.loc[(temp2['year'] == year) & (temp2['ghg'] < mean - 3 * sd), 'ghg'] = mean - 3 * sd
    print(year, mean, sd)

minmax = msoa_2011.loc[msoa_2011['RGN11NM'] == 'Northern Ireland'].iloc[:2, :].set_index('MSOA11CD')
minmax['ghg'] = [temp2['ghg'].min(), temp2['ghg'].max()]

fig, axs = plt.subplots(ncols=3, figsize=(20,7))
for i in range(3):
    year = ['2017', 'may_2020', 'nov_2020'][i]
    temp2.loc[temp2['year'] == year].append(minmax[['geometry', 'ghg']]).plot(column='ghg', legend=True, cmap='Greens', ax=axs[i]); #scheme='quantiles',
    axs[i].set_title(year)
    axs[i].set_xlim(3000000, 3820000);
    axs[i].set_ylim(3000000, 3720000);


# no policy
wo_policy = ghg_2020.stack(level=2).stack(level=1).stack(level=0).reset_index(); wo_policy.columns = ['MSOA11CD', 'ccp1', 'policy',  'year', 'ghg']
wo_policy = wo_policy.loc[wo_policy['policy'] == 'wo_policy'].append(stacked_2017)

sns.boxplot(data=wo_policy, x='ccp1', y='ghg', hue='year'); plt.show();

temp = wo_policy.groupby(['MSOA11CD', 'year']).sum().join(imd_2019[['msoa_decile']]).reset_index()
sns.boxplot(data=temp, x='msoa_decile', y='ghg', hue='year'); plt.show();

    
temp2 = data[2017][['geometry']].join(temp.set_index('MSOA11CD'))

for year in ['2017', 'may_2020', 'nov_2020']:
    mean = temp2.loc[temp2['year'] == year]['ghg'].mean()
    sd = temp2.loc[temp2['year'] == year]['ghg'].std()
    temp2.loc[(temp2['year'] == year) & (temp2['ghg'] > mean + 3 * sd), 'ghg'] = mean + 3 * sd
    temp2.loc[(temp2['year'] == year) & (temp2['ghg'] < mean - 3 * sd), 'ghg'] = mean - 3 * sd
    print(year, mean, sd)

minmax = msoa_2011.loc[msoa_2011['RGN11NM'] == 'Northern Ireland'].iloc[:2, :].set_index('MSOA11CD')
minmax['ghg'] = [temp2['ghg'].min(), temp2['ghg'].max()]

fig, axs = plt.subplots(ncols=3, figsize=(20,7))
for i in range(3):
    year = ['2017', 'may_2020', 'nov_2020'][i]
    temp2.loc[temp2['year'] == year].append(minmax[['geometry', 'ghg']]).plot(column='ghg', legend=True, cmap='Greens', ax=axs[i]); #scheme='quantiles',
    axs[i].set_title(year)
    axs[i].set_xlim(3000000, 3820000);
    axs[i].set_ylim(3000000, 3720000);

# reduce by 20% income of poor households
temp = data[2017].loc[temp.loc[temp['msoa_decile'] < 3]['MSOA11CD']][['Income anonymised']]
temp['income_2020'] = temp['Income anonymised'] * 0.8
ghg_2020 = pd.DataFrame(columns = pd.MultiIndex.from_arrays([[2020 for x in range(12)], [str(x) for x in range(1,13)]]), index = temp.index)
for x in range(1, 13):
    ghg_2020[(2020, str(x))] = models_2017[x][0].predict(temp['income_2020'])
    
ghg_2020 = ghg_2020.join(data_2017[['MSOA11CD', 'ccp1', 'ghg']].rename(columns={'ghg':2017}).drop_duplicates().set_index(['MSOA11CD', 'ccp1']).unstack(level='ccp1'))

ghg_2020.sum(axis=1,level=0).boxplot()

"""   
for year in range(2007, 2018):
    fig, axs = plt.subplots(ncols=2, nrows=1)
    data[year].plot(column='total_ghg', ax=axs[0], legend=True)
    axs[0].set_title(str(year) +' GHG')
    data[year].plot(column='Income anonymised', ax=axs[1], legend=True)
    axs[1].set_title(str(year) +' Income')
"""

all_data['year_str'] = 'Y' + all_data['year'].astype(str)
sns.scatterplot(data=all_data, x='total_ghg', y='Income anonymised', hue='year_str', size=0.5)

fname = "r'" + data_directory + "/data/processed/modelling_data.csv'"
all_data[['RGN11NM', 'population', 'Income anonymised', 'total_ghg', 'year', 'year_str']].rename(columns={'Income anonymised':'income'}).reset_index()\
    .drop_duplicates().to_csv(eval(fname))

temp = all_data.set_index(['RGN11NM', 'year_str'], append=True)[['Income anonymised', 'total_ghg']]
for var in ['Income anonymised', 'total_ghg']:
    temp[var] = temp[var] / temp[var].sum()
temp = temp.stack().reset_index()
temp.columns = ['MSOA', 'RGN11NM', 'year_str', 'var', 'value']

sns.boxplot(data=temp, x='year_str', y='value', hue='var')

for reg in temp[['RGN11NM']].drop_duplicates()['RGN11NM']:
    sns.boxplot(data=temp.loc[temp['RGN11NM'] == reg], x='year_str', y='value', hue='var')
    plt.title(reg); plt.ylim(0, temp['value'].max()); plt.show()

sns.boxplot(data=all_data, x='year_str', y='Income anonymised')
sns.boxplot(data=all_data, x='year_str', y='total_ghg')


for year in range(2007, 2018):
    print(data[year][['total_ghg', 'Income anonymised']].corr())
    plt.scatter(data[year]['total_ghg'], data[year]['Income anonymised'], s=0.5)
plt.show()


for year in range(2007, 2018):
    sns.scatterplot(data=data[year], x='total_ghg', y='Income anonymised', hue='RGN11NM', size=0.1, legend=False)
    plt.show()


coicop1 = {year : data[year].loc[:,'1.1.1.1':'Income anonymised'] for year in range(2007, 2018)}
for year in range(2007, 2018):
    coicop1[year].columns = [x.split('.')[0] for x in coicop1[year].columns[:-2]] + ['population', 'income']
    coicop1[year] = coicop1[year].sum(axis=1, level=0)

for i in range(12):
    for year in range(2007, 2018):
        plt.scatter(coicop1[year][str(i+1)], coicop1[year]['income'], s=0.5)
    plt.title('COICOP ' + str(i+1)); plt.xlim(0, 8)
    plt.show()
    
for year in range(2007, 2018):
    print(coicop1[year].loc[:,'1':'12'].max().max())
    
    