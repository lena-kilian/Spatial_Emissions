#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar  5 10:15:25 2021

@author: lenakilian
"""

import pandas as pd
import numpy as np
import copy as cp
import geopandas as gpd


wd = r'/Users/lenakilian/Documents/Ausbildung/UoLeeds/PhD/Analysis/'
years = list(range(2007, 2018, 2))
geog = 'MSOA'

# load region and 2001 to 2011 lookup
lookup = pd.read_csv(wd + 'data/raw/Geography/Conversion_Lookups/UK_full_lookup_2001_to_2011.csv')\
    [['MSOA11CD', 'MSOA01CD', 'RGN11NM']].drop_duplicates()

emissions = {}
for year in years:
    year_difference = years[1] - years[0]
    year_str = str(year) + '-' + str(year + year_difference - 1)
    emissions[year] = pd.read_csv(wd + 'data/processed/GHG_Estimates/MSOA_GHG_Estimates/' + geog + 's_' + year_str + '.csv', index_col=0)

shp = gpd.read_file(r'/Users/lenakilian/Documents/Ausbildung/UoLeeds/PhD/Analysis/data/raw/Geography/Shapefiles/UK/msoa_2011_uk_all.shp')

emissions_shp = {}

#/Users/lenakilian/Downloads/NI_SOA2011_Esri_Shapefile_0/