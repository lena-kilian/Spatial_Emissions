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

wd = r'/Users/lenakilian/Documents/Ausbildung/UoLeeds/PhD/Analysis/'

data = gpd.read_file(wd+ 'data/processed/GWR_data/LM_residuals.shp')

# queen weight (if border is shared value is 1, otherwise 0)
weights = libpysal.weights.Queen.from_dataframe(data, geom_col='geometry')

# remove islands
data = data.drop(weights.islands)

# redefine weights - because islands are now missing
# transform weights - now neighbour weights are proportional to how many neighbours each MSOA has
weights = libpysal.weights.Queen.from_dataframe(data, geom_col='geometry')
weights.transform = 'R'

idx = data.columns.tolist()[1:-1]
    
moran = pd.DataFrame()
for item in idx:
    temp = pd.DataFrame(index=[1], columns=['Category', 'MI', 'p_val'])
    temp['Category'] = item
    mi = pysal.Moran(data[item], weights)
    temp['MI'] = mi.I
    temp['p_val'] = mi.p_sim
    moran = moran.append(temp)
    print(item)
        
    # LISA plot
    check = cp.copy(data)
    check[item + '_std'] = (check[item] - check[item] .mean()) / check[item].std()
    check['w_' + item + '_std'] = pysal.weights.lag_spatial(weights, check[item + '_std'])
        
    lisa = pysal.Moran_Local(check[item], weights)
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
        
    axs[0].set_title(item)
        
    check.plot(column='quadrant2', 
               cmap=matplotlib.colors.ListedColormap(check[['col']].drop_duplicates()['col'].tolist()),
               ax=axs[1], legend=False)
    # Display
    plt.show()
        
moran['Transport'] = [x.split('_')[0] for x in moran['Category']]
moran['Product'] = [x.split('_')[1] for x in moran['Category']]