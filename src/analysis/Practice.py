#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 19 14:24:09 2021

@author: lenakilian

Sources:
    http://darribas.org/gds_scipy16/ipynb_md/05_spatial_dynamics.html
    https://pysal.org/notebooks/explore/giddy/Markov_Based_Methods.html
    https://pysal.org/notebooks/lib/libpysal/weights.html
"""

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

f = libpysal.io.open(libpysal.examples.get_path('usjoin.csv'), 'r')

print(f.header[0:10])

name = f.by_col('Name')
print(name[:10])

y1929 = f.by_col('1929')
print(y1929[:10])

y2009 = f.by_col('2009')
print(y2009[:10])
y2009 = np.array(y2009)

# turn income values into array
Y = np.array( [ f.by_col(str(year)) for year in range(1929,2010) ] ) * 1.0
Y = Y.transpose() # transpose to have years in columns

years = np.arange(1929,2010)
plt.plot(years,Y[0])

RY = Y / Y.mean(axis=0)
plt.plot(years,RY[0])

name = np.array(name)

for state in ['Ohio', 'Alabama']:
    plt.plot(years, RY[np.nonzero(name==state)[0][0]], label=state)
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

d2009 = gaussian_kde(Y[:,-1])
minY0 = Y[:,-1].min()*.90
maxY0 = Y[:,-1].max()*1.10
x = np.linspace(minY0, maxY0, 100)
plt.plot(x,d2009(x))

minR0 = RY.min()
maxR0 = RY.max()
x = np.linspace(minR0, maxR0, 100)
d1929 = gaussian_kde(RY[:,0])
d2009 = gaussian_kde(RY[:,-1])
plt.plot(x, d1929(x), label='1929')
plt.plot(x, d2009(x), label='2009')
plt.legend()


for y in range(2010-1929):
    sns.kdeplot(RY[:,y])
#sns.kdeplot(data.HR80)
#sns.kdeplot(data.HR70)
#sns.kdeplot(data.HR60)

for cs in RY.T: # take cross sections
    plt.plot(x, gaussian_kde(cs)(x))
    
cs[0]
sigma = RY.std(axis=0)
plt.plot(years, sigma)
plt.ylabel('s')
plt.xlabel('year')
plt.title("Sigma-Convergence")

# Conclusion: So the distribution is becoming less dispersed over time.

# But what about internal mixing? Do poor (rich) states remain poor (rich), 
# or is there movement within the distribuiton over time?

# Markov Chains
c = np.array([['b','a','c'], 
              ['c','c','a'], 
              ['c','b','c'], 
              ['a','a','b'], 
              ['a','b','c']])
c

m = giddy.markov.Markov(c)

m.classes
m.transitions
m.p

# State Per Capita Incomes

libpysal.examples.explain('us_income')
    
data = gpd.read_file(libpysal.examples.get_path('us48.dbf'))
W = libpysal.weights.Queen.from_dataframe(data)
W.transform = 'r'

data.STATE_NAME

f = libpysal.io.open(libpysal.examples.get_path('usjoin.csv'))
pci = np.array([f.by_col[str(y)] for y in range(1929,2010)])
pci.shape
pci = pci.T
pci.shape

cnames = f.by_col('Name')
cnames[:10]


ids = [cnames.index(name) for name in data.STATE_NAME]
ids[:10]

pci = pci[ids]
RY = RY[ids]

# 1929
shp_link = libpysal.io.open(libpysal.examples.get_path('us48.shp'))
tx = gpd.read_file(libpysal.examples.get_path('us48.shp'))
pci29 = mapclassify.Quantiles(pci[:,0], k=5)
f, ax = plt.subplots(1, figsize=(10, 5))
tx.assign(cl=pci29.yb+1).plot(column='cl', categorical=True, \
        k=5, cmap='Greens', linewidth=0.1, ax=ax, \
        edgecolor='grey', legend=True)
ax.set_axis_off()
plt.title('Per Capita Income 1929 Quintiles')
plt.show()

# 2009
pci2009 = mapclassify.Quantiles(pci[:,-1], k=5)
f, ax = plt.subplots(1, figsize=(10, 5))
tx.assign(cl=pci2009.yb+1).plot(column='cl', categorical=True, \
        k=5, cmap='Greens', linewidth=0.1, ax=ax, \
        edgecolor='grey', legend=True)
ax.set_axis_off()
plt.title('Per Capita Income 2009 Quintiles')
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
# The fact that each of the 5 diagonal elements is larger than  0.78 indicates a 
# high stability of US regional income dynamics system.

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
w = libpysal.weights.Queen.from_shapefile(libpysal.examples.get_path('us48.shp'))
w.transform = 'R'


mits = [esda.moran.Moran(cs, w) for cs in RY.T]
res = np.array([(m.I, m.EI, m.p_sim, m.z_sim) for m in mits])
plt.plot(years, res[:,0], label='I')
plt.plot(years, res[:,1], label='E[I]')
plt.title("Moran's I")
plt.legend()

plt.plot(years, res[:,-1])
plt.ylim(0,7.0)
plt.title('z-values, I')

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


