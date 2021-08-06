#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 19 14:24:09 2021

@author: lenakilian

Applying 
    http://darribas.org/gds_scipy16/ipynb_md/05_spatial_dynamics.html
    https://pysal.org/notebooks/explore/giddy/Markov_Based_Methods.html
    https://pysal.org/notebooks/lib/libpysal/weights.html
    https://nbviewer.jupyter.org/github/pysal/mapclassify/blob/master/notebooks/03_choropleth.ipynb
to own data
"""

import pandas as pd
import numpy as np
import pysal as ps
import matplotlib.pyplot as plt
import libpysal
from scipy.stats.kde import gaussian_kde
import seaborn as sns
import giddy
import geopandas as gpd
import mapclassify
import esda
import copy as cp
import random
import math

data_directory = "/Users/lenakilian/Documents/Ausbildung/UoLeeds/PhD/Analysis"
output_directory = "/Users/lenakilian/Documents/Ausbildung/UoLeeds/PhD/Analysis/Spatial_Emissions"

years = list(range(2007, 2017, 2))

data = {}
for year in years:
    # import ghg and income
    data[year] = pd.read_csv(eval("r'" + data_directory + "/data/processed/GHG_Estimates/MSOA_mean_" + str(year) + '-' + str(year+1) + ".csv'"))
    data[year]['total_ghg'] = data[year].loc[:,'1.1.1.1':'12.5.3.5'].sum(1)

msoa_2011 = gpd.read_file(eval("r'" + data_directory + "/data/raw/Geography/Shapefiles/UK/msoa_2011_uk_all.shp'")).set_index('MSOA11CD')[['geometry']]
lookup = pd.read_csv(eval("r'" + data_directory + "/data/raw/Geography/Conversion_Lookups/UK_full_lookup_2001_to_2011.csv'"))
msoa_2011 = msoa_2011.join(lookup[['MSOA01CD', 'MSOA11CD', 'RGN11NM']].drop_duplicates().set_index('MSOA11CD')).reset_index().to_crs(epsg=3035)

# try different product categories
cat_dict = pd.read_excel(eval("r'" + data_directory + "/data/processed/LCFS/Meta/lcfs_desc_anne&john.xlsx'"))
cats = cat_dict[['category_2']].drop_duplicates()['category_2']
cat_dict['ccp_code'] = [x.split(' ')[0] for x in cat_dict['ccp']]
cat_dict = dict(zip(cat_dict['ccp_code'], cat_dict['category_2']))

for year in years:
    if year < 2013:
        data[year] = msoa_2011.set_index('MSOA01CD')[['geometry', 'RGN11NM']].join(data[year].set_index('MSOA'), how='right')
    else:
        data[year] = msoa_2011.set_index('MSOA11CD')[['geometry', 'RGN11NM']].join(data[year].set_index('MSOA'), how='left')
    data[year] = data[year].loc[(data[year]['RGN11NM'] != 'Scotland') & (data[year]['RGN11NM'] != 'Northern Ireland') & (data[year]['RGN11NM'] != 'Wales')] 
    data[year] = data[year].rename(columns=cat_dict).sum(axis=1, level=0)
    data[year] = gpd.GeoDataFrame(data[year], geometry='geometry')

items = ['grains, fruit, veg', 'other food and drinks', 'food (animal origin)', 'miscellaneous', 'clothing', 'other home', 'home energy', 'private transport (land)',
         'public transport (land and water)', 'air transport', 'total_ghg']
product_data = {}
for item in items:
    product_data[item] = data[years[-1]][['geometry']]
    for year in years:
        product_data[item] = product_data[item].join(data[year][[item]].rename(columns={item:year}))
    product_data[item] = product_data[item].fillna(product_data[item].median())
    product_data[item] = product_data[item].join(lookup[['MSOA11CD', 'RGN11NM']].drop_duplicates().set_index('MSOA11CD'))

# turn income values into array
Y = np.array(product_data['total_ghg'].drop(['geometry', 'RGN11NM'], axis=1).dropna(how='any')) 

for i in range(10):
    plt.plot([year-2007 for year in years], Y[i])
plt.legend()
plt.show()

for row in Y:
    plt.plot(years, row)
plt.show()

RY = Y / Y.mean(axis=0)
plt.plot(years, RY[0])

# Spaghetti plot
for row in RY:
    plt.plot(years, row)
    
# Kernel Density (univariate, aspatial)
for i in range(len(years)):
    density = gaussian_kde(Y[:,0])
    minY0 = Y[:,i].min()*.90
    maxY0 = Y[:,i].max()*1.10
    x = np.linspace(minY0, maxY0, 100)
    plt.plot(x,density(x))
    plt.title(str(years[i]))
    plt.show()
    
for i in range(len(years)):
    minR0 = RY.min()
    maxR0 = RY.max()
    x = np.linspace(minR0, maxR0, 100)
    d2007 = gaussian_kde(RY[:,i])
    plt.plot(x, d2007(x), label=years[i])
plt.legend()
plt.show()


for y in range(2017-2007):
    sns.kdeplot(Y[:,y], label=str(2007+y))
plt.legend()

for cs in RY.T: # take cross sections
    plt.plot(x, gaussian_kde(cs)(x))
    
cs[0]
sigma = Y.std(axis=0)
plt.plot(years, sigma)
plt.ylabel('s')
plt.xlabel('year')
plt.title("Sigma-Convergence")
# Conclusion: The distribution is varying over time

# Markov Chains    
def stability(product_data, item, k):
    results = {}

    pci = np.array(product_data[item][years].dropna(how='any'))

    # convert to a code cell to generate a time series of the maps
    q10 = np.array([mapclassify.Quantiles(pci[:,years.index(year)], k=k).yb for year in years]).transpose()
    m10 = giddy.markov.Markov(q10)
    
    results['q10'] = q10
    results['transitions'] = m10.transitions

    np.set_printoptions(3, suppress=True)
    results['stability'] = m10.p
    # The 5 diagonals are between 0.440-0.685 shows medium stability over time

    results['steady_state'] = m10.steady_state #steady state distribution

    # Get first mean passage time: the average number of steps to go from a state/class to another state for the first time
    results['steps'] = giddy.ergodic.fmpt(m10.p) #first mean passage time
    
    return(results)

k=5

res_products = {}; stability_results=pd.DataFrame(index=list(range(k)))
for item in items:
    res_products[item] = stability(product_data, item, k)
    temp = []
    for i in range(k):
        temp.append(round(res_products[item]['stability'][i, i], 3))
    stability_results[item] = temp
stability_results = stability_results.T

# For a state with income in the first quintile, it takes on average 11.5 years for it to first enter the 
# second quintile, 29.6 to get to the third quintile, 53.4 years to enter the fourth, and 103.6 years to reach 
# the richest quintile.
# But, this approach assumes the movement of a state in the income distribution is independent of the movement 
# of its neighbors or the position of the neighbors in the distribution. Does spatial context matter?

# Dynamics of Spatial Dependence
def dynamic_dependence(product_data, item, k, w):
    results = {}
    # Spatial Markov
    pci = np.array(product_data[item][years].dropna(how='any'))
    rpci = pci / pci.mean(axis=0)

    sm = giddy.markov.Spatial_Markov(rpci, w, fixed=True, k=k)
    
    results['pooled'] = sm.p
    results['lag'] = sm.P
    results['S'] = sm.S
    
    return(results)
"""    
    for f in sm.F:
        print(f)
    
    sm.summary()
    

    # visualise
    fig, axes = plt.subplots(ncols=2, nrows=math.ceil(k/2), figsize=(k, k*(len(years) - 1))
    for i in range(math.ceil((len(years) - 1)/2)):
        for j in range(2):
            while (i*2+j-1) <=  math.ceil(k/2):
                ax = axes[i, j]
                if i==0 & j==0:
                    p_temp = sm.p
                    im = ax.imshow(p_temp, cmap="coolwarm", vmin=0, vmax=1)
                    ax.set_title("Pooled",fontsize=18) 
                else:
                    p_temp = sm.P[i*2+j-1]
                    im = ax.imshow(p_temp,cmap="coolwarm", vmin=0, vmax=1)
                    ax.set_title("Spatial Lag %d"%(i*2+j-1),fontsize=18) 
                for x in range(len(p_temp)):
                    for y in range(len(p_temp)):
                        ax.text(y, x, round(p_temp[x, y], 2), ha="center", va="center", color="w")
    fig.subplots_adjust(right=0.92)
    cbar_ax = fig.add_axes([0.95, 0.228, 0.01, 0.5])
    fig.colorbar(im, cax=cbar_ax)
    #fig.savefig('spatial_markov_us.png', dpi = 300)
"""

items = ['grains, fruit, veg', 'other food and drinks', 'food (animal origin)', 'miscellaneous', 'clothing', 'other home', 'home energy', 'private transport (land)', 
         'public transport (land and water)', 'air transport', 'total_ghg']



w = libpysal.weights.Queen.from_dataframe(product_data[item])
w.transform = 'R'
k=5
res_products_d={}; pooled_stability=pd.DataFrame(index=list(range(k)))
for item in items:
    res_products_d[item] = dynamic_dependence(product_data, item, k, w)
    temp = []
    for i in range(k):
        temp.append(round(res_products_d[item]['pooled'][i, i], 3))
    pooled_stability[item] = temp
pooled_stability = pooled_stability.T


regional_data = {}; pooled_stability_regions = {}
for region in product_data['total_ghg'][['RGN11NM']].drop_duplicates()['RGN11NM']:
    pooled_stability_regions[region] = pd.DataFrame(index=list(range(k)))
    data = {item : product_data[item].loc[product_data[item]['RGN11NM'] == region] for item in items}
    w = libpysal.weights.Queen.from_dataframe(data[item])
    w.transform = 'R'
    for item in items:
        res_products_d[item] = dynamic_dependence(data, item, k, w)
        temp = []
        for i in range(k):
            temp.append(round(res_products_d[item]['pooled'][i, i], 3))
        pooled_stability_regions[region][item] = temp
    pooled_stability_regions[region] = pooled_stability_regions[region].T

regions = product_data['total_ghg'][['RGN11NM']].drop_duplicates()['RGN11NM'].tolist()
pooled_stability_regions_all = cp.copy(pooled_stability_regions[regions[0]])
pooled_stability_regions_all.columns = pd.MultiIndex.from_arrays([regions[:1] * len(pooled_stability_regions_all.columns), pooled_stability_regions_all.columns])
for region in regions[1:]:
    temp = cp.copy(pooled_stability_regions[region])
    temp.columns = pd.MultiIndex.from_arrays([[region] * len(temp.columns), temp.columns])
    pooled_stability_regions_all = pooled_stability_regions_all.join(temp)

check = pooled_stability_regions_all.T.stack().reset_index()
check.columns = ['region', 'group', 'product', 'stability']

g = sns.FacetGrid(check, row='product', col='group')
g.map(sns.barplot, 'stability', 'region')

"""
giddy.markov.Homogeneity_Results(sm.T).summary()
print(giddy.markov.kullback(sm.T))

# LISA Markov
lm = giddy.markov.LISA_Markov(pci, w)
print(lm.classes)
print(lm.transitions)
print(lm.p)
print(lm.steady_state)
print(giddy.ergodic.fmpt(lm.p))
print(lm.chi_2)
"""


