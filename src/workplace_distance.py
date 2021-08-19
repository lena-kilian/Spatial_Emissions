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
ew_shp = ew_shp.loc[ew_shp['RGN11NM'] == 'London']

# calculate distances between centroids
distances = cp.copy(ew_shp).drop('MSOA01CD', axis=1).drop_duplicates()
# get centroids
distances['centroid'] = distances.centroid

def calc_dist(a, b):
    temp = (a[0] - b[0])**2 + (a[1] - b[1])**2
    dist = np.sqrt(temp)
    return(dist)


# combine with workplace data
workplace = pd.read_csv(wd + 'data/raw/Census/WF02EW - Location of usual residence and place of work.csv', index_col=0, header=7).stack().dropna(how='all').reset_index()
workplace.columns = ['MSOA_live', 'MSOA_work', 'people']
workplace['MSOA_live'] = [str(x).split(' : ')[0] for x in workplace['MSOA_live']]
workplace['MSOA_work'] = [str(x).split(' : ')[0] for x in workplace['MSOA_work']]
workplace['people'] = pd.to_numeric(workplace['people'], errors='coerce')
workplace = workplace.dropna(how='any') # save for later
workplace_dist = cp.copy(workplace)
workplace = workplace.loc[workplace['people'] > 0]
# exclude doubles to save time
combo = []
for i in range(len(workplace)):
    temp = workplace.iloc[i,:]
    temp = [temp['MSOA_live'], temp['MSOA_work']]
    temp.sort()
    combo.append(temp)
workplace['MSOA_live'] = [x[0] for x in combo]; workplace['MSOA_work'] = [x[1] for x in combo]
workplace = workplace.drop('people', axis=1).drop_duplicates()
# calculate distances
dist_list = []
for i in range(len(workplace)):
    temp = workplace.iloc[i,:]
    item1 = temp['MSOA_live']; item2 = temp['MSOA_work']
    if item1 == item2:
        d = 0
    else:
        point1 = distances.loc[item1, 'centroid'].x, distances.loc[item1, 'centroid'].y
        point2 = distances.loc[item2, 'centroid'].x, distances.loc[item2, 'centroid'].y
        d = calc_dist(point1, point2)
    dist_list.append(d)

workplace['distances'] = dist_list
temp = cp.copy(workplace).rename(columns={'MSOA_live':'MSOA_1', 'MSOA_work':'MSOA_2'}).rename(columns={'MSOA_2':'MSOA_live', 'MSOA_1':'MSOA_work'})
workplace = workplace.append(temp)

workplace_dist = workplace_dist.merge(workplace, on=['MSOA_live', 'MSOA_work'])
workplace_dist = workplace_dist.fillna(0)
workplace_dist['total_dist'] = workplace_dist['distances'] * workplace_dist['people'] 
workplace_dist = workplace_dist.groupby('MSOA_live').sum()
workplace_dist['avg_dist'] = workplace_dist['total_dist'] / workplace_dist['people'] 

workplace_dist.drop('distances', axis=1).to_csv(wd + 'data/processed/Census/workplace_distances_avg.csv')
