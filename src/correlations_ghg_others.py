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
from scipy.stats import pearsonr

ghg_year = 2015 # 2017

dict_cat = 'category_8' # replacement for new_cats

wd = r'/Users/lenakilian/Documents/Ausbildung/UoLeeds/PhD/Analysis/'
years = list(range(2007, 2018, 2))
geog = 'MSOA'

lookup = pd.read_csv(wd + 'data/raw/Geography/Conversion_Lookups/UK_full_lookup_2001_to_2011.csv')\
    [['MSOA11CD', 'MSOA01CD', 'RGN11NM']].drop_duplicates()
lookup = lookup.loc[(lookup['RGN11NM'] != 'Northern Ireland') & 
                    (lookup['RGN11NM'] != 'Wales') & 
                    (lookup['RGN11NM'] != 'Scotland')]
lookup['London'] = False; lookup.loc[lookup['RGN11NM'] =='London', 'London'] = True

emissions = {}
for year in [ghg_year]:
    year_difference = years[1] - years[0]
    year_str = str(year) + '-' + str(year + year_difference - 1)
    emissions[year] = pd.read_csv(wd + 'data/processed/GHG_Estimates/' + geog + '_' + year_str + '.csv', index_col=0)
    
# income data
income = {}
income[2017] = pd.read_csv(wd + 'data/raw/Income_Data/equivalised_income_2017-18.csv', header=4, encoding='latin1')
income[2015] = pd.read_csv(wd + 'data/raw/Income_Data/equivalised_income_2015-16.csv', skiprows=5, header=None, encoding='latin1')
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
# combine all census data
age = age[['All usual residents']]\
    .join(pd.DataFrame(age.loc[:, 'Age 65 to 74':'Age 90 and over'].sum(axis=1))).rename(columns={0:'pop_65+'})\
    .join(pd.DataFrame(age.loc[:, 'Age 0 to 4':'Age 10 to 14'].sum(axis=1))).rename(columns={0:'pop_14-'})
age['pop_65+_pct'] = age['pop_65+'] / age['All usual residents'] * 100
age['pop_14-_pct'] = age['pop_14-'] / age['All usual residents'] * 100

disability['not_lim_pct'] = disability['Day-to-day activities not limited'] / disability['All categories: Long-term health problem or disability'] * 100
disability = disability[['Day-to-day activities not limited', 'not_lim_pct']].rename(columns = {'Day-to-day activities not limited':'not_lim'})
disability['lim_pct'] = 100 - disability['not_lim_pct']

ethnicity['bame_pct'] = ethnicity.drop('White', axis=1).sum(1) / ethnicity.sum(1) * 100

census_data = age[['pop_65+_pct', 'pop_65+', 'pop_14-_pct', 'pop_14-']].join(disability).join(ethnicity[['bame_pct']])\
    .join(workplace[['total_workplace_dist', 'avg_workplace_dist']], how='left')
    
# add transport access
ptal_2015 = gpd.read_file(wd + 'data/processed/GWR_data/gwr_data_london_' + str(ghg_year) + '.shp')
ptal_2015 = ptal_2015.set_index('index')[['AI2015', 'PTAL2015', 'AI2015_ln']]


# combine all with emissions data
cat_dict = pd.read_excel(wd + '/data/processed/LCFS/Meta/lcfs_desc_anne&john.xlsx')
cats = cat_dict[[dict_cat]].drop_duplicates()[dict_cat]
cat_dict['ccp_code'] = [x.split(' ')[0] for x in cat_dict['ccp']]

# save index
idx = cat_dict[[dict_cat]].drop_duplicates()[dict_cat].tolist()
idx.remove('other')

cat_dict = dict(zip(cat_dict['ccp_code'], cat_dict[dict_cat]))
temp = emissions[ghg_year].rename(columns=cat_dict).sum(axis=1, level=0)
new_cat = lookup.set_index('MSOA11CD').join(temp, how='left').join(ptal_2015, how='left')\
    .join(census_data, how='left').join(income[ghg_year][['income']])
new_cat['avg_workplace_dist'] = new_cat['avg_workplace_dist']/1000

# correlation
keep = idx + ['AI2015', 'AI2015_ln', 'pop_65+_pct', 'pop_14-_pct', 'bame_pct',  'lim_pct', 'avg_workplace_dist', 'income']

#for item in keep:
#    sns.distplot(new_cat[item]); plt.show()

# Correlations
corr = new_cat[keep].corr().loc[idx]\
    [['AI2015_ln', 'pop_65+_pct', 'pop_14-_pct', 'bame_pct', 'lim_pct', 'avg_workplace_dist', 'income']]
    
corr_reg = new_cat[keep + ['London']].groupby('London').corr().swaplevel(axis=0).loc[idx]\
    [['AI2015_ln', 'pop_65+_pct', 'pop_14-_pct', 'bame_pct', 'lim_pct', 'avg_workplace_dist', 'income']]
    
corr_reg.to_csv(wd + '/Spatial_Emissions/outputs/Stats/correlation_london_roe.csv')

# P-values
def pearsonr_pval(x,y):
    return pearsonr(x,y)[1]
    
corr_reg_p = new_cat[keep + ['London']].groupby('London').corr(method=pearsonr_pval).swaplevel(axis=0).loc[idx]\
    [['AI2015_ln', 'pop_65+_pct', 'pop_14-_pct', 'bame_pct', 'lim_pct', 'avg_workplace_dist', 'income']]
    
for item in ['AI2015_ln', 'pop_65+_pct', 'pop_14-_pct', 'bame_pct', 'lim_pct', 'avg_workplace_dist', 'income']:
    corr_reg_p.loc[corr_reg_p[item] >= 0.05, item] = 1
    corr_reg_p.loc[(corr_reg_p[item] < 0.05) & (corr_reg_p[item] >= 0.01), item] = 0.05
    corr_reg_p.loc[corr_reg_p[item] < 0.01, item] = 0.01

corr_reg_p = corr_reg_p.rename(index={True:'London', False:'RoE'})

corr_reg_p.to_csv(wd + '/Spatial_Emissions/outputs/Stats/correlation_pvals_london_roe.csv')


# make scatterplot
data = new_cat.set_index(['MSOA01CD', 'RGN11NM', 'London', 'income'], append=True)[idx].stack().reset_index()\
    .rename(columns={'level_0':'MSOA11CD', 'level_5':'Transport Mode', 0:'tCO2e per capita', 'income':'Income'})
    
fig, axs = plt.subplots(sharex=True, ncols=len(idx), nrows=2, figsize=(15, 10))#, sharey=True)
for i in range(2):
    reg = [True, False][i]
    for j in range(len(idx)):
        tm = idx[j]
        temp = data.loc[(data['London'] == reg) & (data['Transport Mode'] == tm)]
        sns.scatterplot(ax=axs[i, j], data=temp, x='Income', y='tCO2e per capita')
        axs[i, j].set_ylim(-0.1, [3, 2.5, 0.6, 0.2, 0.2, 2.5][j])

