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


years = list(range(2007,2018))
lsoa_lookup = pd.read_csv('Geography/Conversion Lookups/UK_geography_conversions.csv')
msoa_lookup = lsoa_lookup[['MSOA11CD', 'RGN11NM']].drop_duplicates().set_index('MSOA11CD')
msoa_shp = gpd.read_file('Geography/Shapefiles/EnglandWales/msoa_2011_ew.shp')

data = {}
for year in years:
    data[year] = pd.read_csv('Estimating_Emissions/Outputs/MSOA/ghg_detailed_' + str(year) + '.csv').set_index('MSOA11CD')
    
london_msoa = pd.DataFrame(index=msoa_lookup.loc[msoa_lookup['RGN11NM']=='London'].index)
for year in years:
    temp = pd.DataFrame(data[year].drop('population', axis=1).sum(1))
    temp.columns = [str(year)]
    london_msoa = london_msoa.join(temp)

london_msoa.to_csv('Estimating_Emissions/Outputs/MSOA_London.csv')

london_shp = msoa_shp.set_index('msoa11cd').loc[london_msoa.index]
    

f = libpysal.io.open('Estimating_Emissions/Outputs/MSOA_London.csv')

print(f.header[0:10])

name = f.by_col('MSOA11CD')
print(name[:10])

y2007 = f.by_col('2007')
print(y2007[:10])

y2017 = f.by_col('2017')
print(y2017[:10])
y2017 = np.array(y2017)

# turn income values into array
Y = np.array([f.by_col(str(year)) for year in range(2007,2018)]) * 1.0
Y = Y.transpose() # transpose to have years in columns

plt.plot(years,Y[0])

RY = Y / Y.mean(axis=0)
plt.plot(years,RY[0])

name = np.array(name)

for msoa in list(name[:5]):
    plt.plot(years, RY[np.nonzero(name==msoa)[0][0]], label=msoa)
plt.legend()


# Spaghetti plot
for row in RY:
    plt.plot(years, row)
    
# Kernel Density (univariate, aspatial)
density = gaussian_kde(Y[:,0])
minY0 = Y[:,0].min()*.90
maxY0 = Y[:,0].max()*1.10
x = np.linspace(minY0, maxY0, 100)
plt.plot(x,density(x))

d2017 = gaussian_kde(Y[:,-1])
minY0 = Y[:,-1].min()*.90
maxY0 = Y[:,-1].max()*1.10
x = np.linspace(minY0, maxY0, 100)
plt.plot(x,d2017(x))

minR0 = RY.min()
maxR0 = RY.max()
x = np.linspace(minR0, maxR0, 100)
d2007 = gaussian_kde(RY[:,0])
d2017 = gaussian_kde(RY[:,-1])
plt.plot(x, d2007(x), label='2007')
plt.plot(x, d2017(x), label='2017')
plt.legend()


for y in range(2017-2007):
    sns.kdeplot(Y[:,y])

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
W = libpysal.weights.Queen.from_dataframe(london_shp)
W.transform = 'r'

pci = np.array([f.by_col[str(y)] for y in range(2007, 2018)])
pci.shape
pci = pci.T
pci.shape

cnames = f.by_col('MSOA11CD')
cnames[:10]


# join shape data to emissions
london = london_shp[['geometry']].join(london_msoa)

# 2007
pci07 = mapclassify.Quantiles(pci[:,0], k=5)

f, ax = plt.subplots(1, figsize=(10, 5))
london.assign(cl=pci07.yb + 1).plot(column='cl', categorical=True, k=5, cmap='Greens', linewidth=0.1, 
                                    ax=ax, edgecolor='grey', legend=True)
ax.set_axis_off()
plt.title('Per Capita Emissions 2007 Quintiles')
plt.show()

# 2017
pci17 = mapclassify.Quantiles(pci[:,-1], k=5)

f, ax = plt.subplots(1, figsize=(10, 5))
london.assign(cl=pci17.yb + 1).plot(column='cl', categorical=True, k=5, cmap='Greens', linewidth=0.1, 
                                    ax=ax, edgecolor='grey', legend=True)
ax.set_axis_off()
plt.title('Per Capita Emissions 2017 Quintiles')
plt.show()

# convert to a code cell to generate a time series of the maps
q5 = np.array([mapclassify.Quantiles(y).yb for y in pci.T]).transpose()
q5.shape
q5[:,0]

pci.shape
pci[0]

m5 = giddy.markov.Markov(q5)
m5.classes

m5.transitions

np.set_printoptions(3, suppress=True)
m5.p
# The 5 diagonals are between 0.440-0.685 shows medium stability over time

m5.steady_state #steady state distribution

# Get first mean passage time: the average number of steps to go from a state/class to another state for the first time
fmpt = giddy.ergodic.fmpt(m5.p) #first mean passage time
fmpt

# For a state with income in the first quintile, it takes on average 11.5 years for it to first enter the 
# second quintile, 29.6 to get to the third quintile, 53.4 years to enter the fourth, and 103.6 years to reach 
# the richest quintile.
# But, this approach assumes the movement of a state in the income distribution is independent of the movement 
# of its neighbors or the position of the neighbors in the distribution. Does spatial context matter?

# Dynamics of Spatial Dependence

w = libpysal.weights.Queen.from_dataframe(london_shp)
w.transform = 'R'

'''
mits = [esda.moran.Moran(cs, w) for cs in Y.T]
res = np.array([(m.I, m.EI, m.p_sim, m.z_sim) for m in mits])
plt.plot(years, res[:,0], label='I')
plt.plot(years, res[:,1], label='E[I]')
plt.title("Moran's I")
plt.legend()

plt.plot(years, res[:,-1])
plt.ylim(0,7.0)
plt.title('z-values, I')
'''

# Spatial Markov
pci.shape
rpci = pci / pci.mean(axis=0)
rpci[:,0]

rpci[:,0].mean()
sm = giddy.markov.Spatial_Markov(rpci, W, fixed=True, k=5)
sm.p

for p in sm.P:
    print(p)
    
sm.S

for f in sm.F:
    print(f)
    
sm.summary()

# visualise
fig, ax = plt.subplots(figsize = (5,5))
im = ax.imshow(sm.p,cmap = "coolwarm",vmin=0, vmax=1)
# Loop over data dimensions and create text annotations.
for i in range(len(sm.p)):
    for j in range(len(sm.p)):
        text = ax.text(j, i, round(sm.p[i, j], 2),
                       ha="center", va="center", color="w")
ax.figure.colorbar(im, ax=ax)

fig, axes = plt.subplots(2,3,figsize = (15,10)) 
for i in range(2):
    for j in range(3):
        ax = axes[i,j]
        if i==1 and j==2:
            ax.axis('off')
            continue
        # Loop over data dimensions and create text annotations.
        p_temp = sm.P[i*2+j]
        for x in range(len(p_temp)):
            for y in range(len(p_temp)):
                text = ax.text(y, x, round(p_temp[x, y], 2),
                               ha="center", va="center", color="w")
        im = ax.imshow(p_temp,cmap = "coolwarm",vmin=0, vmax=1)
        ax.set_title("Spatial Lag %d"%(i*3+j),fontsize=18) 
fig.subplots_adjust(right=0.92)
cbar_ax = fig.add_axes([0.95, 0.228, 0.01, 0.5])
fig.colorbar(im, cax=cbar_ax)


fig, axes = plt.subplots(2,3,figsize = (15,10)) 
for i in range(2):
    for j in range(3):
        ax = axes[i,j]
        if i==0 and j==0:
            p_temp = sm.p
            im = ax.imshow(p_temp,cmap = "coolwarm",vmin=0, vmax=1)
            ax.set_title("Pooled",fontsize=18) 
        else:
            p_temp = sm.P[i*2+j-1]
            im = ax.imshow(p_temp,cmap = "coolwarm",vmin=0, vmax=1)
            ax.set_title("Spatial Lag %d"%(i*3+j),fontsize=18) 
        for x in range(len(p_temp)):
            for y in range(len(p_temp)):
                text = ax.text(y, x, round(p_temp[x, y], 2),
                               ha="center", va="center", color="w")
        
fig.subplots_adjust(right=0.92)
cbar_ax = fig.add_axes([0.95, 0.228, 0.01, 0.5])
fig.colorbar(im, cax=cbar_ax)
#fig.savefig('spatial_markov_us.png', dpi = 300)


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


