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
from matplotlib import cm
from matplotlib.lines import Line2D
from matplotlib import rc



wd = r'/Users/lenakilian/Documents/Ausbildung/UoLeeds/PhD/Analysis/'
years = list(range(2007, 2018, 2))
geog = 'MSOA'

dict_cat = 'category_8'

# set font globally
plt.rcParams.update({'font.family':'Times New Roman'})

# load region and 2001 to 2011 lookup
lookup = pd.read_csv(wd + 'data/raw/Geography/Conversion_Lookups/UK_full_lookup_2001_to_2011.csv')\
    [['MSOA11CD', 'MSOA01CD', 'RGN11NM']].drop_duplicates()

emissions = {}
for year in years:
    year_difference = years[1] - years[0]
    year_str = str(year) + '-' + str(year + year_difference - 1)
    emissions[year] = pd.read_csv(wd + 'data/processed/GHG_Estimates/' + geog + '_' + year_str + '.csv', index_col=0)

new_cat = {}
cat_dict = pd.read_excel(wd + '/data/processed/LCFS/Meta/lcfs_desc_anne&john.xlsx')
cats = cat_dict[['category']].drop_duplicates()['category']
cat_dict['ccp_code'] = [x.split(' ')[0] for x in cat_dict['ccp']]
cat_dict = dict(zip(cat_dict['ccp_code'], cat_dict[dict_cat]))
for year in years:
    new_cat[year] = emissions[year].rename(columns=cat_dict).sum(axis=1, level=0)
    

idx = new_cat[2017].columns.tolist(); idx.remove('other'); idx.remove('population')
#idx = ['Private transport: Petrol, diesel, motoring oils', 'Private transport: other', 
#       'Rail, bus transport', 'Air transport', 'Private transport: Rental, taxi', 'Water transport']

all_data = pd.DataFrame()
for year in years:
    if year < 2014:
        temp = cp.copy(new_cat[year]).join(lookup.set_index('MSOA01CD'))
    else:
        temp = cp.copy(new_cat[year]).join(lookup.set_index('MSOA11CD')[['RGN11NM']])
    temp['year'] = year
    temp = temp.loc[(temp['RGN11NM'] != 'Wales') & (temp['RGN11NM'] != 'Northern Ireland') & (temp['RGN11NM'] != 'Scotland')]
    temp['RGN'] = 'London'
    temp.loc[temp['RGN11NM'] != 'London', 'RGN'] = 'Rest of England'
    all_data = all_data.append(temp)

all_data.to_csv(wd + 'data/processed/GHG_Estimates/all_msoa.csv')
