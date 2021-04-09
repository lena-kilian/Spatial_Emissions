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


ew_shp = gpd.read_file('Geography/Shapefiles/EnglandWales/msoa_2011_ew.shp').set_index('msoa11cd')

emissions = {}
for year in range(2011, 2018):
    emissions[year] = pd.read_csv('Estimating_Emissions/Outputs/MSOA/ghg_detailed_' + str(year) + '.csv').set_index('MSOA11CD')
    emissions[year]['total_ghg'] = emissions[year].drop('population', axis=1).sum(1)

equ_income = {}
for year in [2012, 2014, 2016, 2018]:
    year_name = str(year-1) + '-' + str(year-2000)
    equ_income[year] = pd.read_csv('Income_Data/equivalised_income_' + year_name + '.csv', 
                                   header=4, encoding='windows-1252')
    equ_income[year] = equ_income[year].set_index('MSOA code').dropna(how='all')
    equ_income[year] = equ_income[year].rename(
        columns={'Net income after housing costs (£)':'income_equ', 
                 'Net annual income after housing costs (£)':'income_equ'})
    equ_income[year]['income_equ'] = equ_income[year]['income_equ'].astype(str).str.replace(',', '').astype(float)

# ward level
temp = pd.read_csv('Geography/Conversion Lookups/Middle_Layer_Super_Output_Area_(2011)_to_Ward_(2015)_Lookup_in_England_and_Wales.csv').set_index('MSOA11CD')
geog_lookup = equ_income[2012][['Region name']].join(temp)
ward_shp = ew_shp.join(temp[['WD15CD']]).dissolve(by='WD15CD')[['geometry']]
ward_shp = ward_shp.loc[ward_shp.index[[item[0] == 'E' for item in ward_shp.index]]]

ward_data = {}
for year in range(2011, 2018):
    if year not in [2012, 2014, 2016, 2018]:
        inc_year = year+1
    ward_data[year] = temp[['WD15CD', 'LAD15NM']].join(equ_income[inc_year][['income_equ']]).join(emissions[year])\
        .set_index(['WD15CD', 'LAD15NM'], append=True).drop(['total_ghg'], axis=1)
    ward_data[year].iloc[:,:-1] = ward_data[year].iloc[:,:-1].apply(lambda x: x * ward_data[year]['population'])
    ward_data[year] =  ward_data[year].sum(axis=0, level=1)
    ward_data[year].iloc[:,:-1] = ward_data[year].iloc[:,:-1].apply(lambda x: x / ward_data[year]['population'])
    ward_data[year] = ward_shp.join(ward_data[year], how='inner').dropna(how='any')
    ward_data[year]['total_ghg'] = ward_data[year].iloc[:,2:-1].sum(1)

q1=0.1
for year in range(2011, 2018):
    q = ward_data[year][['total_ghg', 'income_equ']].quantile(q=[q1, 1-q1], axis=0, numeric_only=True)
        
    fig, axs = plt.subplots(ncols=3, figsize=(15, 5))
    
    sns.scatterplot(ax=axs[0], data=ward_data[year], x='income_equ', y='total_ghg', color='grey')
    #sns.scatterplot(ax=axs[0], data=example, x='income_equ', y='total_ghg', color='b')
    axs[0].axvline(q.loc[q1, 'income_equ'], color='r'); axs[0].axvline(q.loc[1-q1, 'income_equ'], color='r')
    axs[0].axhline(q.loc[q1, 'total_ghg'], color='r'); axs[0].axhline(q.loc[1-q1, 'total_ghg'], color='r')
    #axs[0].set_xlim(19000, 106000); axs[0].set_ylim(5, 18)
    axs[0].set_title(str(year))
        
    ward_data[year].plot(column='total_ghg', ax=axs[1], legend=True)
    axs[1].set_title('GHG')
        
    ward_data[year].plot(column='income_equ', ax=axs[2], legend=True)
    axs[2].set_title('Income (Equivalised)')

temp = ward_data[2013].join(geog_lookup.set_index('WD15CD')[['WD15NM', 'Region name']].drop_duplicates())
sns.scatterplot(data=temp, x='income_equ', y='total_ghg', hue='Region name')
for region in geog_lookup[['Region name']].drop_duplicates()['Region name'][:-1]:
    sns.scatterplot(data=temp.loc[temp['Region name'] == region], x='income_equ', y='total_ghg')
    plt.title(region)
    plt.show()
    



data = ew_shp[['geometry']].join(equ_income[2016][['Local authority name', 'Region name']])
for year in [2012, 2014, 2016]:
    temp = equ_income[year][['income_equ']].join(emissions[year][['total_ghg']])
    temp['ghg_per_gbp'] = temp['total_ghg'] / temp['income_equ']
    data[year] = temp['ghg_per_gbp']
data[2016] = data[2016] * 100


regions= ['North East', 'North West', 'Yorkshire and The Humber', 'East Midlands', 'West Midlands', 
          'East of England', 'London', 'South East', 'South West', 'Wales']
q1 = 0.1
geogs = regions #['Manchester', 'Liverpool', 'Birmingham'] 
var = 'Region name'#'Local authority name'
for geog in geogs:
    for year in [2012, 2014, 2016]:
        temp = equ_income[year].join(emissions[year][['total_ghg']])
        if year == 2016:
            temp['income_equ'] = temp['income_equ'] / (365.25 / 7)
        example = temp.loc[temp[var] == geog]
        q = temp.quantile(q=[q1, 1-q1], axis=0, numeric_only=True)
        
        fig, axs = plt.subplots(ncols=3, figsize=(15, 5))
    
        sns.scatterplot(ax=axs[0], data=temp, x='income_equ', y='total_ghg', color='grey')
        sns.scatterplot(ax=axs[0], data=example, x='income_equ', y='total_ghg', color='b')
        axs[0].axvline(q.loc[q1, 'income_equ'], color='r'); axs[0].axvline(q.loc[1-q1, 'income_equ'], color='r')
        axs[0].axhline(q.loc[q1, 'total_ghg'], color='r'); axs[0].axhline(q.loc[1-q1, 'total_ghg'], color='r')
        #axs[0].set_xlim(19000, 106000); axs[0].set_ylim(5, 18)
        axs[0].set_title(geog + ' ' + str(year))
        
        temp = ew_shp.join(example, how='inner')
        temp.plot(column='total_ghg', ax=axs[1], legend=True)
        axs[1].set_title('GHG')
        
        temp.plot(column='income_equ', ax=axs[2], legend=True)
        axs[2].set_title('Income (Equivalised)')
        


temp = data.drop('geometry', axis=1).set_index(['Region name', 'Local authority name'], append=True)\
    .stack().reset_index().rename(columns={0:'ghg_per_gbp', 'level_3':'year'})
temp['year'] = temp['year'].astype(str)
sns.boxplot(data=temp, x='Region name', y='ghg_per_gbp', hue='year')
sns.boxplot(data=temp, hue='Region name', y='ghg_per_gbp', x='year')


la_data = data.groupby(['Region name', 'Local authority name']).mean()
temp = la_data.stack().reset_index().rename(columns={0:'ghg_per_gbp', 'level_2':'year'}); temp['year'] = temp['year'].astype(str)
sns.boxplot(data=temp, x='Region name', y='ghg_per_gbp', hue='year')
sns.boxplot(data=temp, hue='Region name', y='ghg_per_gbp', x='year')

sns.boxplot(data=temp, hue='Region name', y='ghg_per_gbp', x='year')
    
for year in [2012, 2014, 2016]:
    data.plot(column=year, legend=True)
    
plt.scatter(data[2012], data[2014], c='b', s=0.1); 
plt.scatter(data[2012], data[2016], c='g', s=0.1); 
plt.scatter(data[2014], data[2016], c='r', s=0.1); 
plt.xlim(0.01, 0.07); plt.ylim(0.01, 0.07); plt.show()



