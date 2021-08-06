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
income = pickle.load(open(wd + 'data/processed/LCFS/Income/MSOA_income.p', 'rb'))

# income from ONS
temp = pd.read_csv(wd + 'data/raw/Geography/Census_Populations/no_households_england.csv').set_index('geography code')[['Household Composition: All categories: Household composition; measures: Value']]
temp = temp.join(pd.read_csv(wd + 'data/raw/Geography/Census_Populations/census2011_pop_england_wales_msoa.csv').set_index('MSOA11CD'))

income['2017_ons'] = pd.read_csv(wd + 'data/raw/Income_Data/equivalised_income_2017-18.csv', header=4).set_index('MSOA code')\
    [['Net annual income after housing costs']]\
        .join(temp)
income['2017_ons'].columns = ['hhld_income', 'no_hhlds', 'pop']
income['2017_ons']['hhld_income'] = pd.to_numeric(income['2017_ons']['hhld_income'].astype(str).str.replace(',', ''), errors='coerce')
income['2017_ons']['income'] = income['2017_ons']['hhld_income'] * income['2017_ons']['no_hhlds'] / income['2017_ons']['pop'] / (365/7)

# check if income estimates match
temp = income['2017_ons'][['income']].join(income[2017][['Income anonymised']])
sns.scatterplot(data=temp, x='Income anonymised', y='income')

new_cat = {}
cat_dict = pd.read_excel(wd + '/data/processed/LCFS/Meta/lcfs_desc_anne&john.xlsx')
cats = cat_dict[['category']].drop_duplicates()['category']
cat_dict['ccp_code'] = [x.split(' ')[0] for x in cat_dict['ccp']]
cat_dict = dict(zip(cat_dict['ccp_code'], cat_dict['category_5']))
for year in years:
    new_cat[year] = emissions[year].rename(columns=cat_dict).sum(axis=1, level=0)
    new_cat[year] = new_cat[year].join(income[year][['Income anonymised']]).rename(columns={'Income anonymised':'income'})
new_cat['2017_ons']= new_cat[2017].drop('income', axis=1).join(income['2017_ons'][['income']])


new_cat_shp = {}    
for year in years + ['2017_ons']:
    if year in years and year < 2014:
        new_cat_shp[year] = ew_shp.reset_index().set_index('MSOA01CD').join(new_cat[year]).set_index('index')
    else:
        new_cat_shp[year] = ew_shp.join(new_cat[year])
    new_cat_shp[year] = gpd.GeoDataFrame(new_cat_shp[year], geometry='geometry')


idx = ['Private transport: Petrol, diesel, motoring oils', 'Private transport: other', 
       'Rail, bus transport', 'Air transport', 'Private transport: Rental, taxi', 'Water transport']
for year in [2017, '2017_ons']:
    for item in idx:
        sns.scatterplot(data=new_cat_shp[2017], x='income', y=item, hue='RGN11NM'); 
        plt.title(str(year) + ' ' + item); plt.show()

    
all_data_shp = pd.DataFrame()
for year in years + ['2017_ons']:
    temp = cp.copy(new_cat_shp[year])
    if year != '2017_ons':
        temp['year'] = str(year)
        temp['year_no'] = year
        temp['from'] = 'LCFS'
    else:
        temp['year'] = year
        temp['year_no'] = 2017
        temp['from'] = 'ONS'
    all_data_shp = all_data_shp.append(temp)
all_data_shp = gpd.GeoDataFrame(all_data_shp, geometry='geometry')

#temp = all_data_shp[idx + ['year', 'geometry', 'income', 'RGN11NM']].reset_index()
#temp.columns = ['MSOA11CD', 'Petrol', 'other_priv', 'rail_bus', 'air', 'rental_taxi', 'water', 'year', 'geometry', 'income', 'RGN11NM']
#temp.to_file(wd + 'data/processed/GWR_data/all_data_transport.shp')

    
all_data = all_data_shp.drop('geometry', axis=1)
    
by_year = cp.copy(all_data)
by_year['London'] = True; by_year.loc[by_year['RGN11NM'] != 'London', 'London'] = False
by_year = by_year.set_index(['year', 'London'], append=True)
by_year[idx] = by_year[idx].apply(lambda x: x*by_year['population'])
by_year = by_year.sum(axis=0, level=['year', 'London'])
by_year[idx] = by_year[idx].apply(lambda x: x/by_year['population'])
by_year = by_year[idx].unstack(level='London')

by_year_pct = cp.copy(by_year)
for yr in years + ['2017_ons']:
    year = str(yr)
    by_year_pct.loc[year,:] = by_year.loc[year,:] / by_year.loc['2007',:] * 100
by_year_pct = by_year_pct.stack(level='London')

data = by_year_pct[idx].stack().reset_index().rename(columns={'level_2':'product', 0:'ghg_pct'})
for item in [True, False]:
    temp = data.loc[data['London'] == item]
    sns.lineplot(data=temp, x='year', y='ghg_pct', hue='product')#, legend=False)
    plt.title('Is London? - ' + str(item)); plt.ylim(25, 175); plt.show()
    
data = by_year[idx].stack(level=[0, 1]).reset_index().rename(columns={'level_1':'product', 0:'ghg_pct'})
for item in [True, False]:
    temp = data.loc[data['London'] == item]
    sns.lineplot(data=temp, x='year', y='ghg_pct', hue='product')
    plt.title('Is London? - ' + str(item)); plt.ylim(0, 3); 
    plt.show()

change = by_year[idx].reset_index().corr()[['year']]
    
