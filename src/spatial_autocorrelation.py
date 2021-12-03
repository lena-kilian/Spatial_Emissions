#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov 24 10:56:45 2021

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

ghg_year = 2015 # 2017

dict_cat = 'category_8' # replacement for new_cats

wd = r'/Users/lenakilian/Documents/Ausbildung/UoLeeds/PhD/Analysis/'
years = list(range(2007, 2018, 2))
geog = 'MSOA'

lookup = pd.read_csv(wd + 'data/raw/Geography/Conversion_Lookups/UK_full_lookup_2001_to_2011.csv')\
    [['MSOA11CD', 'RGN11NM']].drop_duplicates()
lookup = lookup.loc[(lookup['RGN11NM'] != 'Northern Ireland') & 
                    (lookup['RGN11NM'] != 'Wales') & 
                    (lookup['RGN11NM'] != 'Scotland')]
lookup['London'] = False; lookup.loc[lookup['RGN11NM'] =='London', 'London'] = True

ew_shp = gpd.read_file(wd + 'data/raw/Geography/Shapefiles/EnglandWales/msoa_2011_ew.shp')\
    .set_index('msoa11cd').join(lookup.set_index('MSOA11CD'), how='left')

emissions = {}
for year in [ghg_year]:
    year_difference = years[1] - years[0]
    year_str = str(year) + '-' + str(year + year_difference - 1)
    emissions[year] = pd.read_csv(wd + 'data/processed/GHG_Estimates/' + geog + '_' + year_str + '.csv', index_col=0)
    

# combine all with emissions data
cat_dict = pd.read_excel(wd + '/data/processed/LCFS/Meta/lcfs_desc_anne&john.xlsx')
cat_dict['ccp_code'] = [x.split(' ')[0] for x in cat_dict['ccp']]

# save index
idx = cat_dict[[dict_cat]].drop_duplicates()[dict_cat].tolist()
idx.remove('other')

cat_dict = dict(zip(cat_dict['ccp_code'], cat_dict[dict_cat]))
temp = emissions[ghg_year].rename(columns=cat_dict).sum(axis=1, level=0)
new_cat = ew_shp[['geometry']].join((lookup.set_index('MSOA11CD').join(temp, how='left')))

# split into London & RoE
data = {}
data['London'] = new_cat.loc[new_cat['London'] == True].reset_index()
data['RoE'] = new_cat.loc[new_cat['London'] == False].reset_index()

# queen weight (if border is shared value is 1, otherwise 0)
weights = {area : libpysal.weights.Queen.from_dataframe(data[area], geom_col='geometry') for area in ['London', 'RoE']}

# remove islands
data = {area : data[area].drop(weights[area].islands) for area in ['London', 'RoE']}

# redefine weights - because islands are now missing
# transform weights - now neighbour weights are proportional to how many neighbours each MSOA has
for area in ['London', 'RoE']:
    weights[area] = libpysal.weights.Queen.from_dataframe(data[area], geom_col='geometry')
    weights[area].transform = 'R'
    
    

moran = pd.DataFrame()
for area in ['London', 'RoE']:
    for item in idx:
        temp = pd.DataFrame(index=[1], columns=['Area', 'Category', 'MI', 'p_val'])
        temp['Area'] = area; temp['Category'] = item
        mi = pysal.Moran(data[area][item], weights[area])
        temp['MI'] = mi.I
        temp['p_val'] = mi.p_sim
        moran = moran.append(temp)
        print(area, item)
        
        # LISA plot
        check = cp.copy(data[area])
        check[item + '_std'] = (check[item] - check[item] .mean()) / check[item].std()
        check['w_' + item + '_std'] = pysal.weights.lag_spatial(weights[area], check[item + '_std'])
        
        lisa = pysal.Moran_Local(check[item], weights[area])
        # Break observations into significant or not
        check['significant'] = lisa.p_sim < 0.05
        # Store the quadrant they belong to
        check['quadrant'] = lisa.q
        check.loc[check['significant'] == False, 'quadrant'] = 0
        check['quadrant2'] = check['quadrant'].map({1:'HH', 2:'LH', 3:'LL', 4:'HL', 0:'NS'})
        check['col'] = check['quadrant'].map({1:'red', 2:'#83cef4', 3:'blue', 4:'#e59696', 0:'grey'})
        
        check = check.sort_values('quadrant')
        
        # Setup the figure and axis
        fig, axs = plt.subplots(ncols=2, figsize=(10, 5))
        # Plot values
        sns.regplot(x=item + '_std', y='w_' + item + '_std', data=check, ci=None, ax=axs[0])
        sns.scatterplot(x=item + '_std', y='w_' + item + '_std', data=check, ci=None, hue='quadrant2', 
                        palette = check[['col']].drop_duplicates()['col'].tolist(), ax=axs[0])
        # Add vertical and horizontal lines
        axs[0].axvline(0, c='k', alpha=0.5)
        axs[0].axhline(0, c='k', alpha=0.5)
        
        axs[0].set_title(area + ' ' + item)
        
        check.plot(column='quadrant2', 
                   cmap=matplotlib.colors.ListedColormap(check[['col']].drop_duplicates()['col'].tolist()),
                   ax=axs[1], legend=False)
        # Display
        plt.show()
        
