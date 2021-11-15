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

msoa_2011 = gpd.read_file(eval("r'" + data_directory + "/data/raw/Geography/Shapefiles/UK/msoa_2011_uk_all.shp'")).set_index('MSOA11CD')[['geometry']]
lookup = pd.read_csv(eval("r'" + data_directory + "/data/raw/Geography/Conversion_Lookups/UK_full_lookup_2001_to_2011.csv'"))
msoa_2011 = msoa_2011.join(lookup[['MSOA01CD', 'MSOA11CD', 'RGN11NM']].drop_duplicates().set_index('MSOA11CD')).reset_index().to_crs(epsg=3035)

ghg = {}; income = {}; data = {}
for year in range(2007, 2018):
    # import ghg and income
    ghg[year] = pd.read_csv(eval("r'" + data_directory + "/data/processed/GHG_Estimates/MSOA_" + str(year) + ".csv'"))
    income[year] = pd.read_csv(eval("r'" + data_directory + "/data/processed/Income/UK_Income_MSOA_" + str(year) + ".csv'"))
    # adjust for equivalised incomes (account for inflation)
    #income[year]['Income anonymised'] = income[year]['Income anonymised'] * income[year]['population']
    #total_income = income_equivalised.loc[year, 'Mean equivalised disposable income'] * income[year]['population'].sum()
    
    income[year]['Income anonymised'] = income[year]['Income anonymised'] *  inflation[year-2007]
    
    #income[year]['Income anonymised'] = ((income[year]['Income anonymised'] / income[year]['Income anonymised'].sum()) * total_income) / income[year]['population']
    # add income and ghg to one dataset
    data[year] = ghg[year].join(income[year][['Income anonymised']])
    data[year]['total_ghg'] = data[year].loc[:,'1.1.1.1':'12.5.3.5'].sum(1)



income_2020 = {}
for item in ['b', 'c', 'd', 'e', 'f', 'g']:
    income_2020[item] = pd.read_csv(eval("r'" + data_directory + "/data/raw/Income_Data/Income_2020/UKDA-8644-tab/tab/c" + item + "_indresp_w.tab'"), sep='\t', header=0)
    if item not in ['b', 'c', 'd']:
        keep = ['pidp', 'c' + item + '_hhnum',  'c' + item + '_hhincome_amount', 'c' + item + '_hhincome_period',
                'c' + item + '_ghhincome_amount', 'c' + item + '_ghhincome_period'] 
    else:
        keep = ['pidp', 'c' + item + '_hhnum',  'c' + item + '_hhincome_amount', 'c' + item + '_hhincome_period']
    income_2020[item] = income_2020[item][keep]
    
month_dict = {'b':'may', 'c':'june', 'd':'july', 'e':'sep.', 'f':'nov.', 'g':'jan.'}
month_dict2 = {'b':'2020-05', 'c':'2020-06', 'd':'2020-07', 'e':'2020-09', 'f':'2020-11', 'g':'2021-01'}
income_2020_all = pd.DataFrame(columns = [x[3:] for x in income_2020['g'].columns] + ['month', 'date'])
for item in ['b', 'c', 'd', 'e', 'f', 'g']:
    temp = cp.copy(income_2020[item]); temp.columns = [x[3:] for x in temp.columns]
    temp['month'] = month_dict[item]; temp['date'] = month_dict2[item]
    income_2020_all = income_2020_all.append(temp)

income_2020_all = income_2020_all.loc[(income_2020_all['hhincome_period'] <= 4) & (income_2020_all['hhincome_period'] >= 1)] 
    
# adjust for inflation
income_2020_all['hhincome_amount'] = income_2020_all['hhincome_amount'] * (1/1.08)
income_2020_all['ghhincome_amount'] = income_2020_all['hhincome_amount'] * (1/1.08)

period_dict = {1:1, 2:2, 3:(30.5/7), 4:(365.25/7)}  
income_2020_all['hhincome_dict'] = income_2020_all['hhincome_period'].map(period_dict)
income_2020_all['hhincome_week']= income_2020_all['hhincome_amount'] / income_2020_all['hhincome_dict']
income_2020_all['pcincome_week'] = income_2020_all['hhincome_week'] / income_2020_all['hhnum']

income_2020_all['ghhincome_dict'] = income_2020_all['ghhincome_period'].map(period_dict)
income_2020_all['ghhincome_week']= income_2020_all['ghhincome_amount'] / income_2020_all['ghhincome_dict']
income_2020_all['gpcincome_week'] = income_2020_all['ghhincome_week'] / income_2020_all['hhnum']

sns.boxplot(data=income_2020_all, x='month', y='pcincome_week')
sns.boxplot(data=income_2020_all, x='month', y='hhincome_week')

print(income_2020_all.set_index('month')[['hhincome_week', 'pcincome_week', 'ghhincome_week', 'gpcincome_week']].astype(float).mean(level=0))    
#HERE

inflation = [1.32, 1.27, 1.28, 1.22, 1.16, 1.12, 1.09, 1.06, 1.05, 1.04, 1.0]    
    


for year in range(2007, 2018):
    if year < 2014:
        data[year] = msoa_2011.set_index('MSOA01CD')[['geometry', 'RGN11NM']].join(data[year].set_index('MSOA01CD'), how='right')
    else:
        data[year] = msoa_2011.set_index('MSOA11CD')[['geometry', 'RGN11NM']].join(data[year].set_index('MSOA11CD'), how='left')
    data[year] = data[year].loc[(data[year]['RGN11NM'] != 'Scotland') & (data[year]['RGN11NM'] != 'Northern Ireland') & (data[year]['RGN11NM'] != 'Wales')] 

# try different product categories
new_cat = {}
cat_dict = pd.read_excel(eval("r'" + data_directory + "/data/processed/LCFS/Meta/lcfs_desc_anne&john.xlsx'"))
cats = cat_dict[['category_2']].drop_duplicates()['category_2']
cat_dict['ccp_code'] = [x.split(' ')[0] for x in cat_dict['ccp']]
cat_dict = dict(zip(cat_dict['ccp_code'], cat_dict['category_2']))
for year in range(2007, 2018):
    new_cat[year] = data[year].rename(columns=cat_dict).sum(axis=1, level=0)
    new_cat[year] = gpd.GeoDataFrame(new_cat[year], geometry='geometry')
    

new_cat_all = pd.DataFrame(columns=new_cat[2017].columns)
for year in range(2007, 2018):
    temp = cp.copy(new_cat[year]); temp['year'] = year
    new_cat_all = new_cat_all.append(temp)

new_cat_all = gpd.GeoDataFrame(new_cat_all, geometry='geometry')

new_cat_all.to_file(eval("r'" + data_directory + "/data/processed/new_cat_for_gwr.shp'"), driver = 'ESRI Shapefile')
