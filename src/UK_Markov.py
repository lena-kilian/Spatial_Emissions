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


years = list(range(2007,2018))
lsoa_lookup = pd.read_csv('Geography/Conversion Lookups/UK_geography_conversions.csv')
#msoa_lookup = lsoa_lookup[['MSOA11CD', 'RGN11NM']].drop_duplicates().set_index('MSOA11CD')
msoa_shp = gpd.read_file('Geography/Shapefiles/EnglandWales/msoa_2011_ew.shp')

lookup = pd.read_csv('Geography/Conversion Lookups/UK_full_lookup_2001_to_2011.csv')
msoa_lookup = lookup[['MSOA01CD', 'MSOA11CD', 'RGN11NM']].drop_duplicates()

data = {}
for year in years:
    if year < 2011:
        year_str = '01'
    else:
        year_str = '11'
    data[year] = pd.read_csv('Estimating_Emissions/Outputs/MSOA/ghg_detailed_' + str(year) + '.csv')\
        .set_index('MSOA' + year_str + 'CD')        
        
msoa = {}
msoa[2001] = msoa_lookup[['MSOA01CD']].set_index('MSOA01CD')
msoa[2011] = msoa_lookup[['MSOA11CD']].set_index('MSOA11CD')
for year in years: 
    temp = pd.DataFrame(data[year].drop('population', axis=1).sum(1))
    if year < 2011:
        msoa[2001][year] = temp
    else:
        msoa[2011][year] = temp
msoa = msoa_lookup.merge(msoa[2001].reset_index(), on='MSOA01CD').merge(msoa[2011].reset_index(), on='MSOA11CD')
        
product_msoa = {}; coicop1 = {}
for year in years: 
    if year < 2011:
        product_msoa[year] = msoa_lookup[['MSOA01CD']].set_index('MSOA01CD').join(data[year]).dropna(how='all')
    else:
        product_msoa[year] = msoa_lookup[['MSOA11CD']].set_index('MSOA11CD').join(data[year]).dropna(how='all')
    index = [x.split('.')[0] for x in product_msoa[year].columns[:-1]]
    product_msoa[year].columns = pd.MultiIndex.from_arrays([index + ['population'], product_msoa[year].columns])
    coicop1[year] = product_msoa[year].sum(axis=1, level=0)



check = msoa_shp.set_index('msoa11cd')[['geometry']]\
    .join(msoa.set_index('MSOA11CD')[list(range(2007, 2018))]).dropna(how='any') 

for i in range(2007, 2018):
    check.plot(column=i)
    
msoa_corr = check.drop('geometry', axis=1).stack().reset_index().groupby('level_0').corr()
msoa_corr.columns = ['corr_1', 'corr_2']
msoa_corr = msoa_corr.reset_index()
msoa_corr = check[['geometry']].join(msoa_corr.loc[msoa_corr['level_1'] == 0].set_index('level_0')[['corr_1']])

msoa_corr.plot(column='corr_1', legend=True, cmap='coolwarm')


check.index.names = ['MSOA11CD']
check.drop('geometry', axis=1).to_csv('Estimating_Emissions/Outputs/MSOA_EW.csv')

q07 = mapclassify.Quantiles(check[2007], k=10)
check['q07'] = check[2007].map(q07); check['q07'] = [x[0] for x in check['q07']]

income = {}
for year in years:
    income[year] = pd.read_csv('LCFS/Income/Income_MSOA_' + str(year) + '.csv')
    income[year]['income_pc_' + str(year)] = income[year]['income_pc']

pop = msoa.loc[msoa['MSOA11CD'].isin(check.index) == True][['MSOA11CD', 'MSOA01CD']].drop_duplicates()
for year in years:
    if year < 2011:
        code = 'MSOA01CD'
    else:
        code = 'MSOA11CD'
    pop = pop.set_index(code).join(data[year][['population']], how='left')\
        .rename(columns={'population':'pop_' + str(year)}).reset_index()
for year in years:
    if year < 2013:
        code = 'MSOA01CD'
    else:
        code = 'MSOA11CD'
    pop = pop.set_index(code).join(income[year].set_index(code)[['income_pc_' + str(year)]], how='left').reset_index()

transport = cp.copy(pop)
for year in years:
    if year < 2011:
        transport = transport.set_index('MSOA01CD').join(coicop1[year][['7']]).rename(columns={'7':year}).reset_index()
    else:
        transport = transport.set_index('MSOA11CD').join(coicop1[year][['7']]).rename(columns={'7':year}).reset_index()

transport = check[['geometry']].join(transport.drop_duplicates().set_index('MSOA11CD'))
for year in years:
    transport.plot(column=year, legend=True)
    
transport[list(range(2007, 2018))].drop(2013, axis=1).iloc[:1000,:].T.plot(legend=False) #

coicop_summary = pd.DataFrame(columns=years, index=[str(x) for x in range(1,13)])
for year in years:
    temp = coicop1[year].iloc[:,:-1].apply(lambda x: x*coicop1[year]['population'])
    temp = temp.sum() / coicop1[year]['population'].sum()
    coicop_summary[year] = temp
    
coicop_summary.T.plot()


coicop_summary_q07 = {}
for year in years:
    temp = cp.copy(income[year])
    temp.index = temp.iloc[:,0]
    temp = temp[['income_pc']].join(coicop1[year])
    
    q = mapclassify.Quantiles(temp['income_pc'], k=10)
    temp['q_income'] = temp['income_pc'].map(q); temp['q_income'] = [x[0] for x in temp['q_income']]
    
    temp.iloc[:,:-2] = temp.iloc[:,:-2].apply(lambda x: x*temp['population'])
    temp = temp.groupby('q_income').sum()
    temp.iloc[:,:-1] = temp.iloc[:,:-1].apply(lambda x: x/temp['population'])
    
    coicop_summary_q07[year] = temp

for i in range(1, 13):
    coicop_summary_q07[str(i)] = pd.DataFrame(columns=years, index=coicop_summary_q07[2017].index)
    for year in years:
        coicop_summary_q07[str(i)][year] = coicop_summary_q07[year][str(i)]

for i in range(1, 13):
    coicop_summary_q07[str(i)].drop(2013, axis=1).T.plot()
    plt.title(str(i))
 
    

corr_7 = transport.corr()

transport = transport.dropna(how='all').dropna(how='any')
q07 = mapclassify.Quantiles(transport[2007], k=10)
transport['q07'] = transport[2007].map(q07); transport['q07'] = [x[0] for x in transport['q07']]

transport2 = cp.copy(transport)
for year in years:
    transport2[year] = transport2[year] * transport2['pop_' +str(year)]
transport2 = transport2.groupby('q07').sum()
for year in years:
    transport2[year] = transport2[year] / transport2['pop_' +str(year)]

transport2[list(range(2007, 2018))].drop(2013, axis=1).T.plot(legend=True) #

 
check = check.join(pop.set_index(['MSOA11CD']))
q07 = mapclassify.Quantiles(check[2007], k=10)
check['q07'] = check[2007].map(q07); check['q07'] = [x[0] for x in check['q07']]

#check.plot(column='q07', legend=True)

data = check[list(range(2007, 2018))].drop(2013, axis=1).iloc[:500,:]
data.T.plot(legend=False)

data = check[list(range(2007, 2018))].stack().reset_index().groupby('MSOA11CD').corr()
data.columns = ['corr', 'temp']
data = data.reset_index()
data = data.loc[data['level_1']==0]
q_corr = mapclassify.Quantiles(data['corr'], k=3)
data['q_corr'] = data['corr'].map(q_corr); data['q_corr'] = [x[0] for x in data['q_corr']]
check[['geometry']].join(data.set_index('MSOA11CD')).plot(column='q_corr', legend=True, cmap='Greens')

check['diff_0717'] = check[2007] - check[2017]
q_diff = mapclassify.Quantiles(check['diff_0717'], k=5)
check['q_diff'] = check['diff_0717'].map(q_diff); check['q_diff'] = [x[0] for x in check['q_diff']]
check.plot(column = 'q_diff', legend=True)


# VISUALISE AT LAD LEVEL
la = check.join(lookup[['MSOA11CD', 'LAD17NM']].drop_duplicates().set_index('MSOA11CD'), how='left')
to_keep = []
for year in years:
    la[year] = la[year] * la['pop_' + str(year)]
    to_keep.append(year); to_keep.append('pop_' + str(year))
la = la[to_keep + ['LAD17NM']].groupby('LAD17NM').sum()
for year in years:
    la['pc_' + str(year)] = la[year] / la['pop_' + str(year)]

la_shp = gpd.read_file('Geography/Shapefiles/EnglandWalesLAD_2017_EW.shp').set_index('LAD17NM')

la = la_shp.join(la)

for year in years:
    la.plot(column='pc_' + str(year))
    plt.title(str(year))

la[['pc_' + str(year) for year in years]].drop('pc_2013', axis=1).T.plot(legend=False)
q07 = mapclassify.Quantiles(la['pc_2007'], k=10)
la['q07'] = la['pc_2007'].map(q07); la['q07'] = [x[0] for x in la['q07']]

    

check2 = cp.copy(check)
for year in years:
    check2[year] = check2[year] * check2['pop_' + str(year)]
    check2['income_pc_' + str(year)] = check2['income_pc_' + str(year)] * check2['pop_' + str(year)]

check2 = check2.groupby('q07').mean()
for year in years:
    check2[year] = check2[year] / check2['pop_' + str(year)]
    check2['income_pc_' + str(year)] = check2['income_pc_' + str(year)] / check2['pop_' + str(year)]

check2[list(range(2007, 2018))].drop(2013, axis=1).T.plot()

check2[['income_pc_' + str(year) for year in list(range(2007, 2018))]].drop('income_pc_2013', axis=1).T.plot()

for year in years:
    check2['ghg_per_inc_' + str(year)] = check2[year] / check2['income_pc_' + str(year)]
    
check2[['ghg_per_inc_' + str(year) for year in list(range(2007, 2018))]].drop('ghg_per_inc_2013', axis=1).T.plot()   


for year in years:
    check2[year] = check2[year] * check2['pop_' + str(year)]
    #check2[year] = check2[year]/ check2[year].sum() *100

for year in years:
    check2['pop_pct_' + str(year)] = check2['pop_' + str(year)] / check2['pop_' + str(year)].sum() *100


import matplotlib.pyplot as plt
import numpy as np

data = check2[list(range(2007, 2018))]

c = ['r', 'b', 'g', 'y', 'k', 'r', 'b', 'g', 'y', 'k']
fig, ax = plt.subplots()
old_y = [0 for i in range(len(years))]
new_y = [0 for i in range(len(years))]
for i in range(10):
    new_y += data.loc[i]
    ax.fill_between(years, old_y, new_y, color=c[i], alpha=0.5)
    old_y += data.loc[i]
plt.show()


"""data = check2[list(range(2007, 2018)) + ['pop_2007']]
fig, ax = plt.subplots(figsize=(10,5))
group = 0

b=[0 for x in range(len(data))]
col = sns.color_palette("colorblind", len(data.columns))
for i in range(12):
    sns.barplot(ax=ax, x=[names[x] for x in data.index.tolist()], 
                y=data[str(group)], bottom=b, color=col[i])
    b += data[str(group)]
    group += 1
ax.set_ylabel('tCO2 per capita')
plt.savefig('Graphs/datatypes_compared.png', dpi=200)"""


f = libpysal.io.open('Estimating_Emissions/Outputs/MSOA_EW.csv')

print(f.header[0:10])

name = f.by_col('MSOA11CD')
print(name[:10])

y2007 = f.by_col('2007')
print(y2007[:10])

y2017 = f.by_col('2017')
print(y2017[:10])
y2017 = np.array(y2017)

# turn income values into array
Y = np.array([f.by_col(str(year)) for year in range(2007,2018)]) 
Y = Y.transpose() # transpose to have years in columns

plt.plot(years,Y[0])

for msoa in random.sample(name, 10):
    plt.plot(years, Y[name.index(msoa)], label=msoa)
plt.legend()

for row in Y:
    plt.plot(years, row)

RY = Y / Y.mean(axis=0)
plt.plot(years, RY[0])

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
W = libpysal.weights.Queen.from_dataframe(check)
W.transform = 'r'

pci = np.array([f.by_col[str(y)] for y in range(2007, 2018)])
pci.shape
pci = pci.T
pci.shape

cnames = f.by_col('MSOA11CD')
cnames[:10]


# 2007
pci07 = mapclassify.Quantiles(pci[:,years.index(2007)], k=10)

f, ax = plt.subplots(1, figsize=(10, 5))
check.assign(cl=pci07.yb + 1).plot(column='cl', categorical=True, k=10, cmap='Greens', linewidth=0.1, 
                                    ax=ax, edgecolor='grey', legend=True)
ax.set_axis_off()
plt.title('Per Capita Emissions 2007 Deciles')
plt.show()

# 2017
pci17 = mapclassify.Quantiles(pci[:,years.index(2017)], k=10)

f, ax = plt.subplots(1, figsize=(10, 5))
check.assign(cl=pci17.yb + 1).plot(column='cl', categorical=True, k=10, cmap='Greens', linewidth=0.1, 
                                    ax=ax, edgecolor='grey', legend=True)
ax.set_axis_off()
plt.title('Per Capita Emissions 2017 Deciles')
plt.show()


# convert to a code cell to generate a time series of the maps
q10 = np.array([mapclassify.Quantiles(y, k=10).yb for y in pci.T]).transpose()
q10.shape
q10[:,0]

pci.shape
pci[0]

m10 = giddy.markov.Markov(q10)
m10.classes

m10.transitions

np.set_printoptions(3, suppress=True)
m10.p
# The 5 diagonals are between 0.440-0.685 shows medium stability over time

m10.steady_state #steady state distribution

# Get first mean passage time: the average number of steps to go from a state/class to another state for the first time
fmpt = giddy.ergodic.fmpt(m10.p) #first mean passage time
fmpt

# For a state with income in the first quintile, it takes on average 11.5 years for it to first enter the 
# second quintile, 29.6 to get to the third quintile, 53.4 years to enter the fourth, and 103.6 years to reach 
# the richest quintile.
# But, this approach assumes the movement of a state in the income distribution is independent of the movement 
# of its neighbors or the position of the neighbors in the distribution. Does spatial context matter?

# Dynamics of Spatial Dependence

w = libpysal.weights.Queen.from_dataframe(check)
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
sm = giddy.markov.Spatial_Markov(rpci, W, fixed=True, k=10)
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


