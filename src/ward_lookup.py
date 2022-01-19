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


ward_shp = gpd.read_file(wd + 'data/processed/GWR_data/ward_emissions_london_2015.shp') 
ward_shp = ward_shp.set_index('WD15CD')[['geometry']]

# create lookup for wellbeing
lookup = pd.read_csv(wd + 'data/raw/Geography/Conversion_Lookups/Middle_Layer_Super_Output_Area_(2011)_to_Ward_(2015)_Lookup_in_England_and_Wales.csv')\
    [['WD15CD', 'WD15NM', 'LAD15NM']].drop_duplicates()
lookup = lookup.merge(ward_shp.reset_index(), on='WD15CD').drop('geometry', axis=1)

# import wellbeing
check = pd.read_excel(wd + 'data/raw/Wellbeing/london-ward-well-being-probability-scores.xlsx', 
                          sheet_name='Dashboard', header=12).dropna(how='all').iloc[:,:3]
check['ID'] = list(range(len(check)))
# merge to new wards

def clean(series):
    new = series.str.lower().str.replace(' ', '').str.replace('&', 'and').str.replace('.', '').str.replace("'", '').str.replace('-', '')
    return(new)

names = ward_shp.join(lookup.set_index('WD15CD'), how='left').reset_index()
for i in range(2):
    item = ['LAD', 'WD'][i]
    names[item] = clean(names[['LAD15NM', 'WD15NM'][i]])
    check[item] = clean(check[['Borough name', 'Ward name'][i]])
    
temp = names.set_index(['LAD', 'WD']).join(check.set_index(['LAD', 'WD']), how = 'left')
missing_wards = temp[temp.isna().any(axis=1)].reset_index()
have_match = temp.dropna(how='any', axis=0).reset_index()
print(len(have_match))

temp = missing_wards[['WD15CD', 'geometry', 'WD15NM', 'LAD15NM']].set_index(['WD15CD']).join(check.set_index('Ward Code'), how = 'left')
missing_wards = temp[temp.isna().any(axis=1)]
have_match = have_match.append(temp.dropna(how='any', axis=0).reset_index())
print(len(have_match))

# import wellbeing
wellbeing = have_match[['ID', 'geometry']].set_index('ID').join(check.set_index('ID'), how='right')

missing = wellbeing[wellbeing.isna().any(axis=1)].reset_index().drop('geometry', axis=1)

# match to old wards
old_ward = gpd.read_file(wd + '/data/raw/Geography/Shapefiles/EnglandWales/London-wards-2014/London-wards-2014_ESRI/London_Ward.shp')
old_ward = old_ward.to_crs(epsg=4326)

names = old_ward[['NAME', 'GSS_CODE', 'BOROUGH', 'geometry']]
for i in range(2):
    item = ['LAD', 'WD'][i]
    names[item] = clean(names[['BOROUGH', 'NAME'][i]])
    missing[item] = clean(missing[['Borough name', 'Ward name'][i]])
    
temp = names.set_index(['LAD', 'WD']).join(missing.set_index(['LAD', 'WD']), how = 'right')
missing_wards = temp[temp.isna().any(axis=1)].reset_index()
have_match = have_match.append(temp.dropna(how='any', axis=0).reset_index())
print(len(have_match))

temp = names.set_index('GSS_CODE').join(missing_wards.loc[:,'ID':].set_index(['Ward Code']), how = 'right')
missing_wards = temp[temp.isna().any(axis=1)]
have_match = have_match.append(temp.dropna(how='any', axis=0).reset_index())
print(len(have_match))


final_match = have_match[['ID', 'geometry']].merge(check, on='ID')

"""
missing = have_match[['ID', 'geometry']].merge(check, on='ID', how='right')
missing = missing[missing.isna().any(axis=1)].reset_index()

difference = gpd.overlay(ward_shp.join(lookup.set_index('WD15CD')), final_match, how='difference')
difference2 = difference.reset_index().drop('geometry', axis=1)
"""

missing = pd.read_csv(wd + '/data/processed/Geography/ward_09_15_conversion.csv')
missing = ward_shp.join(missing.set_index('WD15CD'), how='right')


final_match = final_match.append(missing).dropna(how='any', axis=1)
final_match.to_file(wd + 'data/processed/Wellbeing/wwellbeing_london_geography.shp')
