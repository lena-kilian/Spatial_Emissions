#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Dec  3 14:08:41 2021

@author: lenakilian
"""
import pandas as pd
import geopandas as gpd
import libpysal
import pysal
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
import copy as cp


wd = r'/Users/lenakilian/Documents/Ausbildung/UoLeeds/PhD/Analysis/'

# new with wide format
emissions = gpd.read_file(wd + 'data/processed/GWR_data/gwr_data_london_2015.shp') 

lookup = pd.read_csv(wd + 'data/raw/Geography/Conversion_Lookups/Middle_Layer_Super_Output_Area_(2011)_to_Ward_(2015)_Lookup_in_England_and_Wales.csv')\
    [['MSOA11CD', 'WD15CD', 'LAD15NM']].drop_duplicates()
    
keep = ['index', 'RGN11NM', 'population', 'income', 'Car/van pu', 'Other tran', 'Rail', 'Bus', 'Combined f', 'Flights', 'geometry']

emissions = emissions[keep].set_index('index').join(lookup.set_index('MSOA11CD'))
ward_shp = emissions[['geometry', 'WD15CD']].dissolve('WD15CD')
emissions = emissions.groupby(['WD15CD']).sum()
emissions = emissions.apply(lambda x: x/emissions['population'])
emissions['Total_transport'] = emissions[['Car/van pu', 'Other tran', 'Rail', 'Bus', 'Combined f', 'Flights']].sum(1)
emissions['land_transport'] = emissions[['Car/van pu', 'Other tran', 'Rail', 'Bus', 'Combined f']].sum(1)

wellbeing = pd.read_excel(wd + 'data/raw/Wellbeing/london-ward-well-being-probability-scores.xlsx', 
                          sheet_name='Data').dropna(how='all')

temp = pd.read_excel(wd + 'data/raw/Wellbeing/london-ward-well-being-probability-scores.xlsx', sheet_name='Ranked', header=3)
temp = temp.dropna(how='all', axis=0).dropna(how='all', axis=1).iloc[:,:4]

wellbeing = wellbeing.merge(temp, on=['Ward', 'Borough']).set_index('New ward code')

keep = ['London Rank 2013 (out of 625)', 'Index Score 2013', 
        'Life Expectancy 2009-13',
       'Childhood Obesity 2013', 
       'Incapacity Benefit rate - 2013',
       'Unemployment rate 2013', 
       'Crime rate - 2013',
       'Deliberate Fires - 2013', 'GCSE point scores - 2013',
       'Unauthorised Absence in All Schools (%) - 2013',
       '% dependent children in out-of-work households - 2013',
       'Public Transport Accessibility - 2013',
       'Homes with access to open space & nature, and % greenspace - 2013',
       'Subjective well-being average score, 2013']

# reverse = ['London Rank 2013 (out of 625)',
#            'Childhood Obesity 2013', 
#            'Incapacity Benefit rate - 2013', 
#            'Unemployment rate 2013', 
#            'Crime rate - 2013',
#            'Deliberate Fires - 2013', 
#            'Unauthorised Absence in All Schools (%) - 2013',
#            '% dependent children in out-of-work households - 2013']

# for item in reverse:
#     if item in wellbeing.columns.tolist():
#         print(item)
#         wellbeing[item] = -1 * wellbeing[item]

# CORRECT THIS - NOT ALL MATCH!!!
all_data = emissions.join(wellbeing[keep].dropna(how='all'), how='inner')

for x in ['Total_transport', 'Car/van pu', 'Other tran', 'Rail', 'Bus', 'Combined f', 'Flights']:
    for y in keep[:2]:
        plt.scatter(all_data[x], all_data[y])
        plt.xlabel(x), plt.ylabel(y)
        plt.axvline(all_data[x].median(), c='r'); plt.axhline(all_data[y].median(), c='r')
        plt.show()


# Categorise
cats = all_data.T
cats['Median'] = cats.median(1)
cats = cats.iloc[:, :-1].apply(lambda x: x > cats['Median']).T
for item in cats.columns:
    cats.loc[cats[item] == True, item] = 'H'
    cats.loc[cats[item] == False, item] = 'L'


ward = ward_shp.join(cats.dropna(how='all'), how='inner').dropna(how='any')


for x in ['Total_transport', 'land_transport', 'Car/van pu', 'Flights']: #, 'Car/van pu', 'Other tran', 'Rail', 'Bus', 'Combined f', 'Flights']:
    for y in ['Subjective well-being average score, 2013']: #keep[:2] + 
        ward['temp'] = ward[x] + ward[y]
        ward.plot(column='temp', legend=True)
        plt.title(x + ' - ' + y)
        plt.show()

