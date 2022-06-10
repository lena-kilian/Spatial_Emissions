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
import mapclassify
import random
import math
import statsmodels.api as sm

data_directory = "/Users/lenakilian/Documents/Ausbildung/UoLeeds/PhD/Analysis"
output_directory = "/Users/lenakilian/Documents/Ausbildung/UoLeeds/PhD/Analysis/Spatial_Emissions"

# import mean income data to adjust incomes for inflation (using 2019 for adjustment)
#income_equivalised = pd.read_excel(eval("r'" + data_directory + "/data/raw/Mean_Income_Equivalised.xls'"), header=6).dropna(how='any')
#income_equivalised.loc[income_equivalised['year'].str.contains('/'), 'year'] = income_equivalised['year'].str.split('/').str[0]
#income_equivalised = income_equivalised.astype(int).set_index('year')


income_2020 = {}
for item in ['b', 'c', 'd', 'e', 'f', 'g']:
    income_2020[item] = pd.read_csv(eval("r'" + data_directory + "/data/raw/Income_Data/Income_2020/UKDA-8644-tab/tab/c" + item + "_indresp_w.tab'"), sep='\t', header=0)
    if item not in ['b', 'c', 'd']:
        keep = ['pidp', 'c' + item + '_hhnum',  'c' + item + '_hhincome_amount', 'c' + item + '_hhincome_period',
                'c' + item + '_ghhincome_amount', 'c' + item + '_ghhincome_period'] 
    else:
        keep = ['pidp', 'c' + item + '_hhnum',  'c' + item + '_hhincome_amount', 'c' + item + '_hhincome_period']
    income_2020[item] = income_2020[item][keep]
    
month_dict = {'b':'may', 'c':'june', 'd':'july', 'e':'sep.', 'f':'nov.', 'g':'jan.'}
month_dict2 = {'b':'2020-05', 'c':'2020-06', 'd':'2020-07', 'e':'2020-09', 'f':'2020-11', 'g':'2021-01'}
income_2020_all = pd.DataFrame(columns = [x[3:] for x in income_2020['g'].columns] + ['month', 'date'])
for item in ['b', 'c', 'd', 'e', 'f', 'g']:
    temp = cp.copy(income_2020[item]); temp.columns = [x[3:] for x in temp.columns]
    temp['month'] = month_dict[item]; temp['date'] = month_dict2[item]
    income_2020_all = income_2020_all.append(temp)

income_2020_all = income_2020_all.loc[(income_2020_all['hhincome_period'] <= 4) & (income_2020_all['hhincome_period'] >= 1)] 
    
# adjust for inflation
income_2020_all['hhincome_amount'] = income_2020_all['hhincome_amount'] * (1/1.08)
income_2020_all['ghhincome_amount'] = income_2020_all['hhincome_amount'] * (1/1.08)

period_dict = {1:1, 2:2, 3:(30.5/7), 4:(365.25/7)}  
income_2020_all['hhincome_dict'] = income_2020_all['hhincome_period'].map(period_dict)
income_2020_all['hhincome_week']= income_2020_all['hhincome_amount'] / income_2020_all['hhincome_dict']
income_2020_all['pcincome_week'] = income_2020_all['hhincome_week'] / income_2020_all['hhnum']

income_2020_all['ghhincome_dict'] = income_2020_all['ghhincome_period'].map(period_dict)
income_2020_all['ghhincome_week']= income_2020_all['ghhincome_amount'] / income_2020_all['ghhincome_dict']
income_2020_all['gpcincome_week'] = income_2020_all['ghhincome_week'] / income_2020_all['hhnum']

sns.boxplot(data=income_2020_all, x='month', y='pcincome_week')
sns.boxplot(data=income_2020_all, x='month', y='hhincome_week')

print(income_2020_all.set_index('month')[['hhincome_week', 'pcincome_week', 'ghhincome_week', 'gpcincome_week']].astype(float).mean(level=0))    
#HERE

inflation = [1.32, 1.27, 1.28, 1.22, 1.16, 1.12, 1.09, 1.06, 1.05, 1.04, 1.0]    
    
ghg = {}; income = {}; data = {}
for year in range(2007, 2018):
    # import ghg and income
    ghg[year] = pd.read_csv(eval("r'" + data_directory + "/data/processed/GHG_Estimates/MSOA_" + str(year) + ".csv'"))
    income[year] = pd.read_csv(eval("r'" + data_directory + "/data/processed/Income/UK_Income_MSOA_" + str(year) + ".csv'"))
    # adjust for equivalised incomes (account for inflation)
    #income[year]['Income anonymised'] = income[year]['Income anonymised'] * income[year]['population']
    #total_income = income_equivalised.loc[year, 'Mean equivalised disposable income'] * income[year]['population'].sum()
    
    income[year]['Income anonymised'] = income[year]['Income anonymised'] *  inflation[year-2007]
    
    #income[year]['Income anonymised'] = ((income[year]['Income anonymised'] / income[year]['Income anonymised'].sum()) * total_income) / income[year]['population']
    # add income and ghg to one dataset
    data[year] = ghg[year].join(income[year][['Income anonymised']])
    data[year]['total_ghg'] = data[year].loc[:,'1.1.1.1':'12.5.3.5'].sum(1)

msoa_2011 = gpd.read_file(eval("r'" + data_directory + "/data/raw/Geography/Shapefiles/UK/msoa_2011_uk_all.shp'")).set_index('MSOA11CD')[['geometry']]
lookup = pd.read_csv(eval("r'" + data_directory + "/data/raw/Geography/Conversion_Lookups/UK_full_lookup_2001_to_2011.csv'"))
msoa_2011 = msoa_2011.join(lookup[['MSOA01CD', 'MSOA11CD', 'RGN11NM']].drop_duplicates().set_index('MSOA11CD')).reset_index().to_crs(epsg=3035)

for year in range(2007, 2018):
    if year < 2014:
        data[year] = msoa_2011.set_index('MSOA01CD')[['geometry', 'RGN11NM']].join(data[year].set_index('MSOA'), how='right')
    else:
        data[year] = msoa_2011.set_index('MSOA11CD')[['geometry', 'RGN11NM']].join(data[year].set_index('MSOA'), how='left')
    data[year] = data[year].loc[(data[year]['RGN11NM'] != 'Scotland') & (data[year]['RGN11NM'] != 'Northern Ireland') & (data[year]['RGN11NM'] != 'Wales')] 

# try different product categories
new_cat = {}
cat_dict = pd.read_excel(eval("r'" + data_directory + "/data/processed/LCFS/Meta/lcfs_desc_anne&john.xlsx'"))
cats = cat_dict[['category_2']].drop_duplicates()['category_2']
cat_dict['ccp_code'] = [x.split(' ')[0] for x in cat_dict['ccp']]
cat_dict = dict(zip(cat_dict['ccp_code'], cat_dict['category_2']))
for year in range(2007, 2018):
    new_cat[year] = data[year].rename(columns=cat_dict).sum(axis=1, level=0)
    new_cat[year] = gpd.GeoDataFrame(new_cat[year], geometry='geometry')
    

new_cat_all = pd.DataFrame(columns=new_cat[2017].columns)
for year in range(2007, 2018):
    temp = cp.copy(new_cat[year]); temp['year'] = year
    new_cat_all = new_cat_all.append(temp)

new_cat_all = gpd.GeoDataFrame(new_cat_all, geometry='geometry')

new_cat_all.to_file(eval("r'" + data_directory + "/data/processed/new_cat_for_gwr.shp'"), driver = 'ESRI Shapefile')


# use other cats
new_cat = {}
cat_dict = pd.read_excel(eval("r'" + data_directory + "/data/processed/LCFS/Meta/lcfs_desc_anne&john.xlsx'"))
cats = cat_dict[['category']].drop_duplicates()['category']
cat_dict['ccp_code'] = [x.split(' ')[0] for x in cat_dict['ccp']]
cat_dict = dict(zip(cat_dict['ccp_code'], cat_dict['category']))
for year in range(2007, 2018):
    new_cat[year] = data[year].rename(columns=cat_dict).sum(axis=1, level=0)
    new_cat[year] = gpd.GeoDataFrame(new_cat[year], geometry='geometry')
    
new_cat_all = pd.DataFrame(columns=new_cat[2017].columns)
for year in range(2007, 2018):
    temp = cp.copy(new_cat[year]); temp['year'] = year
    new_cat_all = new_cat_all.append(temp)

keep = ['grains', 'other food', 'meat', 'dairy and eggs',
       'fruit and veg', 'drinks', 'miscellaneous', 'clothing', 'other home',
       'home energy', 'private transport (land)',
       'public transport (land and water)', 'air transport', 
       'Income anonymised', 'total_ghg']

uk_avg = cp.copy(new_cat_all)
uk_avg[keep] = uk_avg[keep].apply(lambda x: x*uk_avg['population'])
uk_avg = uk_avg.groupby('year').sum()
uk_avg[keep] = uk_avg[keep].apply(lambda x: x/uk_avg['population'])

uk_avg[['grains', 'other food', 'meat', 'dairy and eggs', 'fruit and veg', 'drinks']].plot()

uk_avg[['private transport (land)', 'public transport (land and water)', 'air transport']].plot()


for item in ['other food', 'meat', 'dairy and eggs', 'clothing', 'home energy', 'private transport (land)', 'public transport (land and water)', 'air transport', 'total_ghg']:
    g=sns.FacetGrid(new_cat_all, row='year', col='RGN11NM')
    g.map(sns.scatterplot, 'Income anonymised', item)
    plt.savefig(eval("r'" + data_directory + "/Spatial_Emissions/outputs/facets/UK_regions_scatter_" + item + ".png'"))


# by income decile
new_cat_all = pd.DataFrame(columns=new_cat[2017].columns)
for year in range(2007, 2018):
    temp = cp.copy(new_cat[year]); temp['year'] = year
    temp['q10'] = temp['Income anonymised'].map(mapclassify.Quantiles(temp['Income anonymised'], k=10))
    temp['q10'] = [x[0] for x in temp['q10']]
    new_cat_all = new_cat_all.append(temp)

uk_avg = cp.copy(new_cat_all)
uk_avg[keep] = uk_avg[keep].apply(lambda x: x*uk_avg['population'])
uk_avg = uk_avg.groupby(['year', 'q10']).sum()
uk_avg[keep] = uk_avg[keep].apply(lambda x: x/uk_avg['population'])


categories = ['grains', 'other food', 'meat', 'dairy and eggs', 'fruit and veg', 'drinks']
data = uk_avg[categories].stack().reset_index(); data.columns = ['year', 'q10', 'category', 'ghg']; data['col'] = 'col'

g = sns.FacetGrid(data, row='col', col='q10', hue='category')
g.map(sns.lineplot, 'year', 'ghg')

g = sns.FacetGrid(data, row='col', col='category', hue='q10')
g.map(sns.lineplot, 'year', 'ghg')


uk_avg[['grains', 'other food', 'meat', 'dairy and eggs', 'fruit and veg', 'drinks']].plot()

uk_avg[['private transport (land)', 'public transport (land and water)', 'air transport']].plot()


# by region

uk_avg = cp.copy(new_cat_all)
uk_avg[keep] = uk_avg[keep].apply(lambda x: x*uk_avg['population'])
uk_avg = uk_avg.groupby(['year', 'RGN11NM']).sum()
uk_avg[keep] = uk_avg[keep].apply(lambda x: x/uk_avg['population'])


categories = ['grains', 'other food', 'meat', 'dairy and eggs', 'fruit and veg', 'drinks']
data = uk_avg[categories].stack().reset_index(); data.columns = ['year', 'q10', 'category', 'ghg']; data['col'] = 'col'

g = sns.FacetGrid(data, row='col', col='q10', hue='category')
g.map(sns.lineplot, 'year', 'ghg')

g = sns.FacetGrid(data, col='col', row='category', hue='q10')
g.map(sns.lineplot, 'year', 'ghg')


uk_avg[['grains', 'other food', 'meat', 'dairy and eggs', 'fruit and veg', 'drinks']].plot()

uk_avg[['private transport (land)', 'public transport (land and water)', 'air transport']].plot()




"""
data_2y = {}
for year in range(2007, 2017, 2):
    temp = lookup[['MSOA11CD', 'MSOA01CD']].drop_duplicates()
    temp = temp.loc[temp['MSOA11CD'].isin(new_cat[2017].index) == True]
    if (year != 2013):
        if year < 2014:
            oac_year = 'MSOA01CD'
        else: 
            oac_year = 'MSOA11CD'
        data_2y[year] = temp.set_index(oac_year)
        for cat in cats.tolist() + ['total_ghg', 'Income anonymised']:
            temp2 = new_cat[year][[cat, 'population']].join(new_cat[year + 1][[cat, 'population']], rsuffix='_+1')
            temp2 = (((temp2[cat] * temp2['population']) + (temp2[cat + '_+1'] * temp2['population_+1'])) / (temp2['population'] + temp2['population_+1']))
            data_2y[year] = data_2y[year].join(pd.DataFrame(temp2)).rename(columns={0:cat})

        data_2y[year]['population'] = data_2y[year][['population']].join(new_cat[year + 1][['population']], rsuffix='_+1').mean(1)
        
        if year < 2014:
            data_2y[year] = data_2y[year].set_index('MSOA11CD')
        else: 
            data_2y[year] = data_2y[year].drop('MSOA01CD', axis=1)
    else:
        data_2y[year] = temp.set_index('MSOA01CD').join(new_cat[year]).set_index('MSOA11CD')
        for cat in cats.tolist() + ['total_ghg', 'Income anonymised', 'population']:
            data_2y[year][cat] = (((data_2y[year][cat] * data_2y[year]['population']) + (new_cat[year + 1][cat] * new_cat[year + 1]['population'])) / 
                                  (data_2y[year]['population'] + new_cat[year + 1]['population']))
    print(year)
 """   
 
 
nw = {}
for cat in cats:
    nw[cat] = lookup[['MSOA11CD', 'MSOA01CD', 'LAD17NM', 'RGN11NM']].drop_duplicates()
    nw[cat] = nw[cat].loc[(nw[cat]['MSOA11CD'].isin(new_cat[2017].index) == True) & (nw[cat]['RGN11NM'] == 'North West')]
    for year in range(2007, 2018):
        temp = new_cat[year].loc[new_cat[year]['RGN11NM'] == 'North West'][[cat, 'Income anonymised']].rename(columns={cat:'ghg_' + str(year), 'Income anonymised':'income_' + str(year)})
        if year < 2014:
            nw[cat] = nw[cat].set_index('MSOA01CD').join(temp).reset_index()
        else:
            nw[cat] = nw[cat].set_index('MSOA11CD').join(temp).reset_index()
    nw[cat] = nw[cat].set_index(['MSOA11CD', 'MSOA01CD', 'LAD17NM', 'RGN11NM'])
    nw[cat].columns = pd.MultiIndex.from_arrays([[int(x.split('_')[1]) for x in nw[cat].columns], [x.split('_')[0] for x in nw[cat].columns]])
    nw[cat] = nw[cat].stack(level=0).reset_index().rename(columns={'level_4':'year'})
    
nw_all = pd.DataFrame(columns = nw[cat].columns.tolist() + ['category'])
for cat in cats:
    temp = cp.copy(nw[cat])
    temp['category'] = cat
    nw_all = nw_all.append(temp)
    
"""
g = sns.FacetGrid(nw_all, col='category',  row="LAD17NM")
g.map(sns.boxplot, "year", "ghg")
plt.savefig(eval("r'" + data_directory + "/Spatial_Emissions/outputs/facets/north_west_boxplot.png'"))
"""

g = sns.FacetGrid(nw_all, col='category',  row="LAD17NM")
g.map(sns.scatterplot, "income", "ghg")
plt.savefig(eval("r'" + data_directory + "/Spatial_Emissions/outputs/facets/north_west_scatter.png'"))

manchester = nw_all.loc[nw_all['LAD17NM'] == 'Manchester']
liverpool = nw_all.loc[nw_all['LAD17NM'] == 'Liverpool']

for cat in cats:
    fig, ax = plt.subplots()
    sns.scatterplot(ax=ax, data=nw_all, x='Income anonymised', y='ghg')
    sns.scatterplot(ax=ax, data=manchester, x='Income anonymised', y='ghg', c='red')
    plt.show()
    
nw_all['manchester'] = False; nw_all.loc[nw_all['LAD17NM'] == 'Manchester', 'manchester'] = True
g = sns.FacetGrid(nw_all, col='category',  row="year", hue="manchester")
g.map(sns.scatterplot, "income", "ghg")
plt.savefig(eval("r'" + data_directory + "/Spatial_Emissions/outputs/facets/manchester_scatter.png'"))


nw_all['liverpool'] = False; nw_all.loc[nw_all['LAD17NM'] == 'Liverpool', 'liverpool'] = True
g = sns.FacetGrid(nw_all, col='category',  row="year", hue="liverpool")
g.map(sns.scatterplot, "income", "ghg")
plt.savefig(eval("r'" + data_directory + "/Spatial_Emissions/outputs/facets/liverpool_scatter.png'"))


    
    
    

# check petrol emissions
keep = ['7.2.2.1', '7.2.2.2', '7.2.2.3']
for year in range(2007, 2018):
    temp = data[year][keep + ['geometry']]
    fig, axs = plt.subplots(ncols=3)
    for i in range(3):
        temp.plot(ax=axs[i], column=keep[i], legend=True)
        axs[i].set_title(str(year))
        
for year in range(2007, 2018):
    temp = pd.DataFrame(data[year][keep].stack()).reset_index()
    temp.columns = [temp.columns.tolist()[0], 'ccp', 'ghg']
    temp = temp.set_index(temp.columns.tolist()[0])
    temp = temp.join(data[year][['Income anonymised']])
    sns.scatterplot(data=temp, x='Income anonymised', y='ghg', hue='ccp'); plt.title(str(year)); plt.show()


# add income deciles from 2007
q_07 = mapclassify.Quantiles(data[2007]['Income anonymised'], k=10)
q_07_msoas = cp.copy(data[2007])
q_07_msoas['q_07'] = q_07_msoas['Income anonymised'].map(q_07); q_07_msoas['q_07'] = ['Q' + str(x[0] + 1) for x in q_07_msoas['q_07']]
q_07_dict = dict(zip(q_07_msoas.index, q_07_msoas['q_07']))


all_data = pd.DataFrame(columns= data[2007].columns.to_list() + ['year', 'q_07'])
for year in range(2007, 2018):
    temp = cp.copy(data[year])
    temp['year'] = year
    temp['q_07'] = temp.index.map(q_07_dict)
    all_data = all_data.append(temp)
    
# facetgrid
temp = all_data[['RGN11NM', 'year', 'Income anonymised']]
temp['petrol'] = all_data[['7.2.2.1', '7.2.2.2', '7.2.2.3']].sum(1)
g = sns.FacetGrid(temp, col='RGN11NM',  row="year")
g.map(sns.scatterplot, "Income anonymised", "petrol")


facet_data = all_data.set_index(['year', 'RGN11NM'], append=True).loc[:, '1.1.1.1':'12.5.3.5']
facet_data.columns = [x.split('.')[0] for x in facet_data.columns]
facet_data = facet_data.sum(axis=1, level=0).reset_index(level=[1, 2]).join(all_data['Income anonymised'])
for item in range(1, 13):
    g = sns.FacetGrid(facet_data, col='RGN11NM',  row='year')
    g.map(sns.scatterplot, 'Income anonymised', str(item))
    plt.savefig(eval("r'" + data_directory + "/Spatial_Emissions/outputs/facets/" + str(item) + ".png'"))



    
all_data_corr = all_data[['Income anonymised', 'total_ghg', 'year']].groupby('year').corr()[['Income anonymised']].reset_index()
all_data_corr = all_data_corr.loc[all_data_corr['level_1'] == 'total_ghg']


# plot product emissions over time
temp = all_data.loc[:,'1.1.1.1':'year']
temp.columns = [x.split('.')[0] for x in temp.loc[:,'1.1.1.1':'12.5.3.5'].columns] + ['population', 'Income anonymised', 'total_ghg', 'year']
temp = temp.sum(axis=1, level=0)
save  = temp.drop('population', axis=1)
keep = temp.loc[:,'1':'12'].columns.tolist() + ['Income anonymised']
temp.loc[:,keep] = temp.loc[:,keep].apply(lambda x: x*temp['population'])
temp = temp.groupby('year').sum()
temp = temp.apply(lambda x: x/temp['population']).loc[:,keep]
temp.plot(); plt.show();
plot_data = temp

ccp_labels = ['Food & Drinks', 'Alcohol & Tobacco', 'Clothing & Footwear', 'Housing', 'Furnishings', 'Health', 'Transport', 'Communication', 'Recreation & Culture', 
              'Education', 'Restaurants & Hotels', 'Miscellaneous']
ccp1_dict = dict(zip([str(x) for x in range(1,13)], ccp_labels))
product_year = temp.stack().reset_index(); product_year.columns = ['Year', 'Product/Service (COICOP 1)', 'tCO$_{2}$e per capita']
product_year['Year'] = product_year['Year'].astype(int)
income_year = product_year.loc[product_year['Product/Service (COICOP 1)'] == 'Income anonymised']; income_year.columns = ['Year', 'Income', 'Mean income']
product_year = product_year.loc[product_year['Product/Service (COICOP 1)'] != 'Income anonymised']
product_year['Product/Service (COICOP 1)'] = product_year['Product/Service (COICOP 1)'].map(ccp1_dict)


# Look at correlations
ccp1_corr = pd.DataFrame(save.groupby('year').corr()[['Income anonymised']]).join(pd.DataFrame(plot_data.stack())).reset_index()\
    .rename(columns={0:'ghg', 'Income anonymised':'pearson_r', 'level_1':'ccp1'})
ccp1_corr = ccp1_corr.loc[(ccp1_corr['ccp1'] != 'Income anonymised') & (ccp1_corr['ccp1'] != 'total ghg')]
ccp1_corr['Product'] = ccp1_corr['ccp1'].map(ccp1_dict)
fig, ax = plt.subplots(figsize=(15, 10)); sns.scatterplot(data=ccp1_corr, x='ghg', y='pearson_r', hue='Product', size='year', palette='colorblind');
ax.set_xlabel('tCO$_{2}$e per capita (UK mean)'); ax.set_ylabel('Correlation Coefficient'); ax.set_xlim(0, 5)
plt.savefig(eval("r'" + output_directory + "/outputs/Graphs/ghg_pearson_scatter.png'"), bbox_inch='tight', dpi=150)


transport_lookup = pd.read_csv(eval("r'" + data_directory + "/data/processed/transport_ccp4_lookup.csv'"))
transport_lookup['Kind']= 'Land_Public'
transport_lookup.loc[transport_lookup['kind'] == 'Air', 'Kind'] = 'Air'
transport_lookup.loc[transport_lookup['owned'] == 'Private', 'Kind'] = 'Land_Private'
transport_dict = dict(zip(transport_lookup['ccp4'], transport_lookup['Kind']))
ccp4_corr = all_data[all_data.loc[:,'7.1.1.1':'7.3.4.8'].columns.tolist() + ['year', 'Income anonymised']]\
    .rename(columns=transport_dict).sum(axis=1, level=0).groupby('year').corr()[['Income anonymised']]
ccp4_ghg = all_data[all_data.loc[:,'7.1.1.1':'7.3.4.8'].columns.tolist() + ['year', 'Income anonymised', 'population']].rename(columns=transport_dict).sum(axis=1, level=0)

plot_data = pd.DataFrame(ccp4_ghg.set_index(['Income anonymised', 'year'], append=True).drop('population', axis=1).stack()).reset_index()\
    .rename(columns={0:'ghg', 'level_3':'Kind', 'level_0':'MSOA'})
fig, ax = plt.subplots(figsize=(8, 8)); sns.scatterplot(data=plot_data.loc[plot_data['Kind']=='Air'], y='ghg', x='Income anonymised', hue='Kind');

ccp4_ghg.iloc[:,:-3] = ccp4_ghg.iloc[:,:-3].apply(lambda x: x*ccp4_ghg['population'])
ccp4_ghg = ccp4_ghg.groupby('year').sum()
ccp4_ghg = ccp4_ghg.iloc[:,:-1].apply(lambda x: x/ccp4_ghg['population'])
ccp4_corr = ccp4_corr.join(pd.DataFrame(ccp4_ghg.stack())).reset_index().rename(columns={0:'ghg', 'Income anonymised':'pearson_r', 'level_1':'Kind'})
ccp4_corr = ccp4_corr.loc[(ccp4_corr['Kind'] != 'Income anonymised')]
fig, ax = plt.subplots(figsize=(8, 8)); sns.scatterplot(data=ccp4_corr, x='ghg', y='pearson_r', hue='Kind', size='year');

ccp4_ghg.columns = [x.split('.')[0] for x in temp.loc[:,'1.1.1.1':'12.5.3.5'].columns] + ['population', 'Income anonymised', 'total_ghg', 'year']
temp = temp.sum(axis=1, level=0)
save  = temp.drop('population', axis=1)
keep = temp.loc[:,'1':'12'].columns.tolist() + ['Income anonymised']
temp.loc[:,keep] = temp.loc[:,keep].apply(lambda x: x*temp['population'])
temp = temp.groupby('year').sum()
temp = temp.apply(lambda x: x/temp['population']).loc[:,keep]
temp.plot(); plt.show();
plot_data = temp





product_year = product_year.loc[product_year['Product/Service (COICOP 1)'] != 'Income anonymised']

sns.lineplot(data=product_year, x='Year', y='tCO$_{2}$e per capita', hue='Product/Service (COICOP 1)', palette='colorblind'); plt.show();

# Creating plot with dataset_1
fig, ax1 = plt.subplots(figsize=(12,8)) 
# ghg
sns.lineplot(data=product_year, x='Year', y='tCO$_{2}$e per capita', hue='Product/Service (COICOP 1)', palette="Paired", ax=ax1, legend=False);
ax1.set_xlabel('Year') 
ax1.set_ylabel('tCO$_{2}$e per capita', color = 'k') 
ax1.set_ylim(0, 6)
#plt.savefig(eval("r'" + output_directory + "/outputs/GISRUK_legend.png'"), bbox_inch='tight', dpi=150)
# Adding Twin Axes to plot using dataset_2
ax2 = ax1.twinx() 
sns.lineplot(data=income_year, x='Year', y='Mean income', ax=ax2, color='k', legend=False);
ax2.lines[0].set_linestyle(":")
ax2.set_ylabel('Income per capita', color = 'k')
ax2.set_ylim(0, 400)
# Show plot
plt.savefig(eval("r'" + output_directory + "/outputs/GISRUK_plot.png'"), bbox_inch='tight', dpi=150)
plt.show();

#stacked plot

# set seaborn style
fig, ax1 = plt.subplots(figsize=(12,8)) 
# ghg
sns.lineplot(data=product_year, x='Year', y='tCO$_{2}$e per capita', hue='Product/Service (COICOP 1)', palette="Paired", ax=ax1, legend=False);
for item in ['Housing', 'Transport', 'Food & Drinks', 'Recreation & Culture', 'Restaurants & Hotels']:
    y = product_year.loc[(product_year['Product/Service (COICOP 1)'] == item) & (product_year['Year'] <= 2008)]['tCO$_{2}$e per capita'].tolist()
    if y[0] < y[1]:
        y = y[0] + 0.25
    else:
        y = y[0]
    ax1.text(x=2007.25, y=y, s=item)
ax1.set_xlabel('Year') 
ax1.set_ylabel('tCO$_{2}$e per capita', color = 'k') 
ax1.set_ylim(0, 6)
#plt.savefig(eval("r'" + output_directory + "/outputs/GISRUK_legend.png'"), bbox_inch='tight', dpi=150)
# Adding Twin Axes to plot using dataset_2
ax2 = ax1.twinx() 
sns.lineplot(data=income_year, x='Year', y='Mean income', ax=ax2, color='k', legend=False);
ax2.lines[0].set_linestyle(":")
ax2.set_ylabel('Income per capita', color = 'k')
ax2.set_ylim(0, 400)
ax2.text(x=2016, y=370, s='Income')
# Show plot
plt.savefig(eval("r'" + output_directory + "/outputs/GISRUK_plot.png'"), bbox_inch='tight', dpi=150)
plt.show();



# stacked plot
years = list(range(2007, 2018))
fig, ax1 = plt.subplots(figsize=(12,8)) 
# ghg
plot_data = plot_data.rename(columns=ccp1_dict) 
plot_data.iloc[:, :-1].plot.area(cmap='Paired', ax=ax1)
ax1.legend(fontsize=10, ncol=4)
ax1.text(x=2007.25, y=0.5, s='Food & Drinks')
ax1.text(x=2007.25, y=3.75, s='Housing')
ax1.text(x=2007.25, y=8, s='Transport')
ax1.set_xlabel('Year') 
ax1.set_ylabel('tCO$_{2}$e per capita', color = 'k') 
ax1.set_ylim(0, 16)
ax2.set_xlim(2007, 2017)
# Adding Twin Axes to plot using dataset_2
ax2 = ax1.twinx() 
sns.lineplot(data=income_year, x='Year', y='Mean income', ax=ax2, color='k', legend=False);
ax2.lines[0].set_linestyle(":")
ax2.set_ylabel('Income per capita', color = 'k')
ax2.set_ylim(0, 450)
ax2.set_xlim(2007, 2017)
ax2.text(x=2016, y=370, s='Income')
# Show plot
plt.savefig(eval("r'" + output_directory + "/outputs/GISRUK_plot_stacked.png'"), bbox_inch='tight', dpi=150)
plt.show();



all_data = all_data[['RGN11NM', 'population', 'Income anonymised', 'total_ghg', 'year', 'q_07']]



sns.lineplot(x='year', y='total_ghg', hue='q_07', data=all_data.dropna(how='any'))

# add income deciles from each year individually
all_data = pd.DataFrame(columns= data[2007].columns.to_list() + ['year', 'q_inc'])
for year in range(2007, 2018):
    temp = cp.copy(data[year])
    temp['year'] = year
    
    q = mapclassify.Quantiles(data[year]['Income anonymised'], k=10)
    temp['q_inc'] = temp['Income anonymised'].map(q_07); temp['q_inc'] = ['Q' + str(x[0] + 1) for x in temp['q_inc']]
    
    all_data = all_data.append(temp)

all_data.index.name = 'MSOA'
all_data = all_data[['RGN11NM', 'population', 'Income anonymised', 'total_ghg', 'year', 'q_inc']]
sns.lineplot(x='year', y='total_ghg', hue='q_inc', data=all_data.dropna(how='any'))


sns.lineplot(x='year', y='total_ghg', hue='q_inc', data=all_data.dropna(how='any'))

sns.lmplot(x='total_ghg', y='Income anonymised', hue='year', data=all_data, scatter_kws ={'s':0.1, 'alpha':0.2})
 


check3 = sm.OLS(all_data['total_ghg'], all_data[['Income anonymised', 'year']].astype(float)).fit()
check3.summary()


# Model GHG totals over time!
models = {}
models['all'] = sm.OLS(all_data['total_ghg'], all_data['Income anonymised']).fit()
for year in range(2007, 2018):
    temp = all_data.loc[all_data['year'] == year]
    models[year] = sm.OLS(temp['total_ghg'], temp['Income anonymised']).fit()
    print(models[year].summary())
  

cross_validation = {year:data[year][['total_ghg', 'Income anonymised']] for year in range(2007, 2018)}
for year in range(2007, 2018):
    random.seed(year)
    cross_validation[year] = cross_validation[year].sample(frac=1)
    cross_validation[year]['group'] = np.repeat(list(range(10)), math.ceil(len(cross_validation[year])/10), axis=0)[:len(cross_validation[year])]

results = {}; models = {}
for year in range(2007, 2018):
    results[year] = pd.DataFrame()
    models[year] = {}
    for i in range(10):
        train = cross_validation[year].loc[cross_validation[year]['group'] != i]
        test = cross_validation[year].loc[cross_validation[year]['group'] == i]
        models[year][i] = sm.OLS(train['total_ghg'], train['Income anonymised']).fit()
        test['predict'] = models[year][i].predict(test['Income anonymised'])
        results[year] = results[year].append(test)
    results[year]['difference'] = results[year]['total_ghg'] - results[year]['predict']
 
    
for year in range(2007, 2018):
    results[year]['group'] = 'G' + results[year]['group'].astype(str)
    sns.scatterplot(data=results[year], x='total_ghg', y='predict', hue='group')
    plt.show()
    print(results[year].groupby('group').mean())
    
results_rmse = pd.DataFrame(index=list(range(2007, 2018)))
import math
for year in range(2007, 2018):
    MSE = np.square(results[year]['difference']).mean()
    RMSE = math.sqrt(MSE)
    results_rmse.loc[year, 'Predict own year'] = RMSE
    
results_2017 = data[2017][['total_ghg']]
for year in range(2007, 2018):
    temp = pd.DataFrame(index= data[2017].index)
    for i in range(10):
        temp[i] = models[year][i].predict(data[2017]['Income anonymised'])
    results_2017[year] = temp.mean(1)
    
for year in range(2007, 2018):
    MSE = np.square(np.subtract(results_2017['total_ghg'], results_2017[year])).mean()
    RMSE = math.sqrt(MSE)
    results_rmse.loc[year, 'Predict 2017'] = RMSE

fig, ax = plt.subplots(figsize=(5,5))
sns.heatmap(ax=ax, data=results_rmse, cmap='Greens', annot=True)
plt.savefig(eval("r'" + output_directory + "/outputs/model_heatmap.png'"), bbox_inches='tight', dpi=150)


# Model 2020 products by 2017 data

models_2017 = {}
data_2017 = cp.copy(data[2017]).drop('geometry', axis=1)
data_2017.columns = ['RGN11NM'] + [x.split('.')[0] for x in data_2017.loc[:,'1.1.1.1':'12.5.3.5'].columns] + ['population', 'Income anonymised', 'total_ghg']
data_2017 = data_2017.sum(axis=1, level=0).set_index(['RGN11NM', 'population', 'Income anonymised', 'total_ghg'], append=True).stack().reset_index()\
    .rename(columns={'level_5':'ccp1', 0:'ghg'})


cross_validation = {x:data_2017.loc[data_2017['ccp1'] == str(x)] for x in range(1, 13)}
for x in range(1, 13):
    random.seed(x)
    cross_validation[x] = cross_validation[x].sample(frac=1)
    cross_validation[x]['group'] = np.repeat(list(range(10)), math.ceil(len(cross_validation[x])/10), axis=0)[:len(cross_validation[x])]

results = {}
for x in range(1, 13):
    results[x] = pd.DataFrame()
    models_2017[x] = {}
    for i in range(10):
        train = cross_validation[x].loc[cross_validation[x]['group'] != i]
        test = cross_validation[x].loc[cross_validation[x]['group'] == i]
        models_2017[x][i] = sm.OLS(train['ghg'], train['Income anonymised']).fit()
        test['predict'] = models_2017[x][i].predict(test['Income anonymised'])
        results[x] = results[x].append(test)
    results[x]['difference'] = results[x]['ghg'] - results[x]['predict']
        
for x in range(1, 13):
    results[x]['group'] = 'G' + results[x]['group'].astype(str)
    sns.scatterplot(data=results[x], x='ghg', y='predict', hue='group')
    plt.show()
    print(results[x].groupby('group').mean())
    

####### 2020 income data:
    
# pct_change = [4, -0.5, -2, -4, -5, -5, -6, -7, -7.5, -16]
# import income data
    
change = {}; change['may'] = {}; change['nov'] = {}
change['may']['w_policy'] = [4, -0.5, -2, -4, -5, -5, -6, -7, -7.5, -7.5]
change['may']['wo_policy'] = [-29, -29, -30, -30.5, -19.5, -30.5, -30.5, -31, -27, -27]
change['nov']['w_policy'] = [4.5, -0.5, -2, -4, -5, -5, -6, -7.5, -7.5, -7.5]
change['nov']['wo_policy'] = [-15.5, -15.5, -15.5, -17.5, -15.5, -15.5, -17.5, -17, -17.5, -17.5]
    
imd_2019 = pd.read_excel(eval("r'" + data_directory + "/data/raw/imd_2019.xlsx'"), sheet_name='IoD2019 Domains').set_index('LSOA code (2011)')
imd_2019 = imd_2019.join(lookup[['LSOA11CD', 'MSOA11CD']].drop_duplicates().set_index('LSOA11CD'))
imd_2019 = imd_2019[['MSOA11CD', 'Income Rank (where 1 is most deprived)', 'Income Decile (where 1 is most deprived 10% of LSOAs)']].groupby('MSOA11CD').median()
imd_2019['msoa_decile'] = imd_2019['Income Decile (where 1 is most deprived 10% of LSOAs)'].round(0).astype(int)

incomes_2020 = imd_2019.join(data[2017]['Income anonymised'])
for month in ['may', 'nov']:
    for policy in ['w_policy', 'wo_policy']:
        income_change = incomes_2020['msoa_decile'].map(dict(zip(list(range(1, 11)), change[month][policy])))
        incomes_2020['income_' + month + '_' + policy] = incomes_2020['Income anonymised'] * (1 + (income_change / 100))
        

cols = pd.MultiIndex.from_arrays([['may_2020' for x in range(24)] + ['nov_2020' for x in range(24)],
                                  ((['w_policy'] * 12) + (['wo_policy'] * 12)) * 2,
                                  [str(x) for x in range(1,13)] * 4])
        


total_ghg_2020 = pd.DataFrame(index = incomes_2020.index)
for month in ['may', 'nov']:
    for policy in ['w_policy', 'wo_policy']:
        temp = pd.DataFrame(index=incomes_2020.index)
        for i in list(models[2017].keys()):
            temp[i] = models[2017][i].predict(incomes_2020['income_' + month + '_' + policy])
        total_ghg_2020[(month, policy)] = temp.mean(axis=1)

check3 = total_ghg_2020.join(data[2017][['total_ghg', 'population']]).drop_duplicates()
check3.iloc[:,:-1] = check3.iloc[:,:-1].apply(lambda x: x*check3['population'])
check3 = pd.DataFrame(check3.sum()).T
check3 = check3.iloc[:,:-1].apply(lambda x: x/check3['population'])
check3.columns = ['May_policy', 'May_reg', 'Nov_policy', 'Nov_reg', 'Control_2017']; check3.index=['mean_ghg']
check3.T.to_csv(eval("r'" + data_directory + "/data/processed/pred_values_means.csv'"))

check3.plot.bar()

income_means = income_2020_all.set_index(['date', 'month'])[['pcincome_week']].astype(float).mean(level=[0,1])
uss_ghg = cp.copy(income_means)
temp = pd.DataFrame(index=income_means.index)
for i in list(models[2017].keys()):
    temp[i] = models[2017][i].predict(income_means['pcincome_week'])
uss_ghg['predict'] = temp.mean(axis=1)   

temp = data[2017][['population', 'Income anonymised', 'total_ghg']]
temp.iloc[:,1:] = temp.iloc[:,1:].apply(lambda x: x*temp['population'])
temp = temp.sum()
uss_ghg.loc[('2017-06', '2017'), 'pcincome_week'] = temp['Income anonymised'] / temp['population']
uss_ghg.loc[('2017-06', '2017'), 'predict'] = temp['total_ghg'] / temp['population']

from datetime import datetime
uss_ghg = uss_ghg.reset_index()
uss_ghg['datetime'] = pd.to_datetime(uss_ghg['date']).dt.date

sns.barplot(data=uss_ghg.sort_values('datetime'), x='month', y='predict', color='r')
# twin

fig, ax1 = plt.subplots(figsize=(5,6.5)) 
# ghg
uss_ghg.sort_values('datetime').set_index('date')[['predict']].plot.bar(cmap='Paired', ax=ax1, legend=False)
#ax1.legend(fontsize=10, ncol=4)
ax1.set_xlabel('') 
ax1.set_ylabel('tCO$_{2}$e per capita', color = '#00698b') 
ax1.set_ylim(0, 10)
# Adding Twin Axes to plot using dataset_2
ax2 = ax1.twinx() 
sns.lineplot(data=uss_ghg.sort_values('datetime'), x='date', y='pcincome_week', ax=ax2, color='#8b0000', legend=False);
#ax2.lines[0].set_linestyle(":")
ax2.set_ylabel('Income per capita', color = '#8b0000')
ax2.set_ylim(0, 500)
# Show plot
plt.savefig(eval("r'" + output_directory + "/outputs/GISRUK_plot_stacked_covidincome.png'"), bbox_inches='tight', dpi=150)
plt.show();

temp = {}; temp_msoa = {}
for year in [2007, 2008, 2009]:
    temp[year] = data[year].loc[:,'1.1.1.1':'population']
    temp[year].columns = [x.split('.')[0] for x in temp[year].loc[:,:'12.5.3.5'].columns] + ['population']
    temp[year] = temp[year].sum(axis=1, level=0)
    temp_msoa[year] = cp.copy(temp[year])
    
    temp[year].loc[:,:'12'] = temp[year].loc[:,:'12'].apply(lambda x: x* temp[year]['population'])
    temp[year] = temp[year].sum(axis=0)
    for i in range(1,13):
        temp[year][str(i)] = temp[year][str(i)] / temp[year]['population']
    
    
econ_crisis = pd.DataFrame(temp[2007]).join(pd.DataFrame(temp[2008]), lsuffix='_07', rsuffix='_08').join(pd.DataFrame(temp[2009])).T
econ_crisis.index = [2007, 2008, 2009]

econ_crisis.drop('population', axis=1).plot()

econ_crisis.drop('population', axis=1).plot.area(cmap='Paired')

econ_msoa = pd.DataFrame(index=temp_msoa[2007].index, columns=pd.MultiIndex.from_arrays([['test'], ['test']]))
for year in [2007, 2008, 2009]:
    temp = temp_msoa[year].drop('population', axis=1)
    temp.columns = pd.MultiIndex.from_arrays([[year]*len(temp.columns), temp.columns.tolist()])
    econ_msoa = econ_msoa.join(temp)
econ_msoa = econ_msoa.drop(('test', 'test'), axis=1) 


temp = econ_msoa.sum(axis=1, level=0)

temp = econ_msoa.stack(level=[0,1]).reset_index(); temp.columns=['MSOA', 'year', 'Product/Service', 'tCO$_{2}$e per capita']
temp['Product/Service'] = temp['Product/Service'].map(ccp1_dict)

fig, ax=plt.subplots(figsize=(7,4))
sns.boxplot(ax=ax, data=temp, hue='year', y='tCO$_{2}$e per capita', x='Product/Service', palette='Paired'); #ax.set_xscale('log')


sns.lmplot(data=all_data, x='Income anonymised', y='total_ghg', hue='year')

all_data.to_csv(eval("r'" + output_directory + "/outputs/all_data_for_plot_GISRUK.csv'"))




check2 = total_ghg_2020.join(data[2017][['total_ghg']])
check2.columns = ['May_policy', 'May_reg', 'Nov_policy', 'Nov_reg', 'Control_2017']
check2.to_csv(eval("r'" + data_directory + "/data/processed/pred_values_total_ghg.csv'"))

check_msoa = check2.join(imd_2019[['msoa_decile']]).join(data[2017][['population']])
check_msoa.iloc[:,:-2] = check_msoa.iloc[:,:-2].apply(lambda x: x*check_msoa['population'])
check_msoa = check_msoa.groupby('msoa_decile').sum()
check_msoa.iloc[:,:-1] = check_msoa.iloc[:,:-1].apply(lambda x: x/check_msoa['population'])

for item in check_msoa.columns[:-2]:
    check_msoa['pct_change_' + item] = (check_msoa['Control_2017'] - check_msoa[item]) / check_msoa['Control_2017'] * 100

check_msoa.to_csv(eval("r'" + data_directory + "/data/processed/pred_values_total_ghg_byIMD.csv'"))

income_2020_all.set_index('month')[['hhincome_week', 'pcincome_week', 'ghhincome_week', 'gpcincome_week']].astype(float).mean(level=0)


ghg_2020 = pd.DataFrame(columns = cols, index = incomes_2020.index)
for month in ['may', 'nov']:
    for x in range(1, 13):
        for policy in ['w_policy', 'wo_policy']:
            temp = pd.DataFrame(index=incomes_2020.index)
            for i in list(models_2017[x].keys()):
                temp[i] = models_2017[x][i].predict(incomes_2020['income_' + month + '_' + policy])
            ghg_2020[(month + '_2020', policy, str(x))] = temp.mean(axis=1)

temp = data[2017][['population']]; temp.columns = pd.MultiIndex.from_arrays([['pop'], ['pop'], ['pop']])
check = ghg_2020.join(temp)
check.iloc[:,:-1] = check.iloc[:,:-1].apply(lambda x: x*check[('pop', 'pop', 'pop')])
check = pd.DataFrame(check.sum(axis=0)).T
check.iloc[:,:-1] = check.iloc[:,:-1].apply(lambda x: x/check[('pop', 'pop', 'pop')])
check = check.drop(('pop', 'pop', 'pop'), axis=1).T.unstack(level=2).reset_index()

fig, ax = plt.subplots()
bottom = [0, 0, 0, 0]
for i in range(1, 13):
    top = check[(0, str(i))]
    ax.bar(height=top, bottom=bottom, x=check['level_0'] + '_' + check['level_1'])
    bottom += top

temp = data[2017].loc[:,'1.1.1.1':'12.5.3.5']; temp.columns = [x.split('.')[0] for x in temp.columns]
temp = temp.sum(axis=1, level=0).join(data[2017][['population']]).join(imd_2019[['msoa_decile']]); 
temp.columns = pd.MultiIndex.from_arrays([['baseline']*len(temp.columns.tolist()), ['baseline']*len(temp.columns.tolist()), temp.columns.tolist()])
by_imd = ghg_2020.join(temp)
by_imd.iloc[:,:-2] = by_imd.iloc[:,:-2].apply(lambda x: x*by_imd[('baseline', 'baseline', 'population')])
by_imd = by_imd.groupby(('baseline', 'baseline', 'msoa_decile')).sum()
by_imd.iloc[:,:-1] = by_imd.iloc[:,:-1].apply(lambda x: x/by_imd[('baseline', 'baseline', 'population')])

plot = by_imd.drop(('baseline', 'baseline', 'population'), axis=1).stack(level=2).unstack(level=0).T.reset_index()
plot2 = plot.set_index(['level_0', 'level_1', ('baseline', 'baseline', 'msoa_decile')]).unstack(level=[0,1])
plot = plot.loc[plot['level_1'] != 'w_policy']
plot = plot.loc[plot['level_0'] != 'may_2020']
fig, ax = plt.subplots(figsize=(15, 5))
bottom = [0] * len(plot)
for i in range(1, 13):
    top = plot[str(i)]
    x= plot['level_0'].str[0] + plot[('baseline', 'baseline', 'msoa_decile')].astype(str)
    ax.bar(height=top, bottom=bottom, x=x)
    bottom += top
    
plot = by_imd.drop(('baseline', 'baseline', 'population'), axis=1).stack(level=2).unstack(level=0).T.reset_index()
plot2 = plot.set_index(['level_0', 'level_1', ('baseline', 'baseline', 'msoa_decile')]).unstack(level=[0,1])
plot = plot.loc[plot['level_1'] == 'baseline']
fig, ax = plt.subplots(figsize=(7.5, 5))
bottom = [0] * len(plot)
for i in range(1, 13):
    top = plot[str(i)]
    x= plot['level_0'].str[0] + plot[('baseline', 'baseline', 'msoa_decile')].astype(str)
    ax.bar(height=top, bottom=bottom, x=x)
    bottom += top
    
plot.loc[:,'1':].rename(columns=ccp1_dict).plot(cmap='Paired')

    
plot3 = plot.set_index(('baseline', 'baseline', 'msoa_decile')).drop(['level_0', 'level_1'], axis=1).stack().reset_index()
plot3.columns = ['Income Decile', 'Product/Service', 'tCO$_{2}$e per capita']
plot3['Product / Service'] = plot3['Product/Service'].map(ccp1_dict)

sns.lineplot(data=plot3, x='Income Decile', y='tCO$_{2}$e per capita', hue='Product / Service', palette='Paired'); #plt.yscale('log')

temp = plot3.groupby('Product/Service').mean()[['tCO$_{2}$e per capita']]; temp.columns=['mean']

plot3=plot3.merge(temp.reset_index(), on='Product/Service')
fig, ax = plt.subplots(figsize=(15, 10))
sns.barplot(ax=ax, data=plot3.sort_values('mean'), x='Income Decile', y='tCO$_{2}$e per capita', hue='Product / Service', palette='Paired')
 
fig, ax = plt.subplots(figsize=(7.5, 5))
sns.barplot(ax=ax, data=plot3.sort_values('mean'), hue='Income Decile', x='tCO$_{2}$e per capita', y='Product / Service', palette='Paired_r')
  
fig, ax = plt.subplots(figsize=(15, 5))
sns.barplot(ax=ax, data=plot3.sort_values('mean'), hue='Income Decile', y='tCO$_{2}$e per capita', x='Product / Service', palette='Paired')
plt.xticks(rotation=90);
plt.savefig(eval("r'" + output_directory + "/outputs/Graphs/income_decile_2017_ghg.png'"), bbox_inches='tight', dpi=150)

  
   
for month in ['may_2020', 'nov_2020']:
    for policy in ['w_policy', 'wo_policy']:
        for i in range(1, 13):
            plot2[('pct_change_' + str(i), month, policy)] = (plot2[(str(i), 'baseline', 'baseline')] - plot2[(str(i), month, policy)]) / plot2[(str(i), 'baseline', 'baseline')] * 100
plot2.to_csv(eval("r'" + data_directory + "/data/processed/pred_values_product_ghg_byIMD.csv'"))
check_msoa.to_csv(eval("r'" + data_directory + "/data/processed/pred_values_total_ghg_byIMD.csv'"))

temp = by_imd.drop(('baseline', 'baseline', 'population'), axis=1).sum(axis=1, level=[0,1])
temp.plot.bar()

temp = by_imd.sum(axis=1, level=[0,1]).drop('pop', axis=1).unstack().reset_index(); temp.columns=['month', 'policy', 'imd', 'ghg']

sns.barplot(data=temp.loc[temp['month'] == 'may_2020'], x='imd', y='ghg', hue='policy')
sns.barplot(data=temp.loc[temp['month'] == 'nov_2020'], x='imd', y='ghg', hue='policy')

plot = by_imd.drop(('baseline', 'baseline', 'population'), axis=1).stack(level=2).unstack(level=0).T.sum(axis=1).reset_index()
plot.columns = ['year', 'policy', 'decile', 'ghg']
plot['group'] = plot['year'].str[0] + plot['policy'].str[:2]
sns.barplot(data=plot, x='decile', y='ghg', hue='group')
sns.barplot(data=temp.loc[temp['month'] == 'nov_2020'], x='imd', y='ghg', hue='policy')


stacked_2017 = data_2017[['MSOA11CD', 'ccp1', 'ghg']].rename(columns={'ghg':2017}).drop_duplicates().rename(columns={2017:'ghg'})
stacked_2017['year'] = '2017'
     

# with policy
w_policy = ghg_2020.stack(level=2).stack(level=1).stack(level=0).reset_index(); w_policy.columns = ['MSOA11CD', 'ccp1', 'policy',  'year', 'ghg']
w_policy = w_policy.loc[w_policy['policy'] == 'w_policy'].append(stacked_2017)
    
sns.boxplot(data=w_policy, x='ccp1', y='ghg', hue='year'); plt.show();

temp = w_policy.groupby(['MSOA11CD', 'year']).sum().join(imd_2019[['msoa_decile']]).reset_index()
sns.boxplot(data=temp, x='msoa_decile', y='ghg', hue='year'); plt.show();

temp2 = data[2017][['geometry']].join(temp.set_index('MSOA11CD'))

for year in ['2017', 'may_2020', 'nov_2020']:
    mean = temp2.loc[temp2['year'] == year]['ghg'].mean()
    sd = temp2.loc[temp2['year'] == year]['ghg'].std()
    temp2.loc[(temp2['year'] == year) & (temp2['ghg'] > mean + 3 * sd), 'ghg'] = mean + 3 * sd
    temp2.loc[(temp2['year'] == year) & (temp2['ghg'] < mean - 3 * sd), 'ghg'] = mean - 3 * sd
    print(year, mean, sd)

minmax = msoa_2011.loc[msoa_2011['RGN11NM'] == 'Northern Ireland'].iloc[:2, :].set_index('MSOA11CD')
minmax['ghg'] = [temp2['ghg'].min(), temp2['ghg'].max()]

fig, axs = plt.subplots(ncols=3, figsize=(20,7))
for i in range(3):
    year = ['2017', 'may_2020', 'nov_2020'][i]
    temp2.loc[temp2['year'] == year].append(minmax[['geometry', 'ghg']]).plot(column='ghg', legend=True, cmap='Greens', ax=axs[i]); #scheme='quantiles',
    axs[i].set_title(year)
    axs[i].set_xlim(3000000, 3820000);
    axs[i].set_ylim(3000000, 3720000);


# no policy
wo_policy = ghg_2020.stack(level=2).stack(level=1).stack(level=0).reset_index(); wo_policy.columns = ['MSOA11CD', 'ccp1', 'policy',  'year', 'ghg']
wo_policy = wo_policy.loc[wo_policy['policy'] == 'wo_policy'].append(stacked_2017)

sns.boxplot(data=wo_policy, x='ccp1', y='ghg', hue='year'); plt.show();

temp = wo_policy.groupby(['MSOA11CD', 'year']).sum().join(imd_2019[['msoa_decile']]).reset_index()
sns.boxplot(data=temp, x='msoa_decile', y='ghg', hue='year'); plt.show();

    
temp2 = data[2017][['geometry']].join(temp.set_index('MSOA11CD'))

for year in ['2017', 'may_2020', 'nov_2020']:
    mean = temp2.loc[temp2['year'] == year]['ghg'].mean()
    sd = temp2.loc[temp2['year'] == year]['ghg'].std()
    temp2.loc[(temp2['year'] == year) & (temp2['ghg'] > mean + 3 * sd), 'ghg'] = mean + 3 * sd
    temp2.loc[(temp2['year'] == year) & (temp2['ghg'] < mean - 3 * sd), 'ghg'] = mean - 3 * sd
    print(year, mean, sd)

minmax = msoa_2011.loc[msoa_2011['RGN11NM'] == 'Northern Ireland'].iloc[:2, :].set_index('MSOA11CD')
minmax['ghg'] = [temp2['ghg'].min(), temp2['ghg'].max()]

fig, axs = plt.subplots(ncols=3, figsize=(20,7))
for i in range(3):
    year = ['2017', 'may_2020', 'nov_2020'][i]
    temp2.loc[temp2['year'] == year].append(minmax[['geometry', 'ghg']]).plot(column='ghg', legend=True, cmap='Greens', ax=axs[i]); #scheme='quantiles',
    axs[i].set_title(year)
    axs[i].set_xlim(3000000, 3820000);
    axs[i].set_ylim(3000000, 3720000);

# reduce by 20% income of poor households
temp = data[2017].loc[temp.loc[temp['msoa_decile'] < 3]['MSOA11CD']][['Income anonymised']]
temp['income_2020'] = temp['Income anonymised'] * 0.8
ghg_2020 = pd.DataFrame(columns = pd.MultiIndex.from_arrays([[2020 for x in range(12)], [str(x) for x in range(1,13)]]), index = temp.index)
for x in range(1, 13):
    ghg_2020[(2020, str(x))] = models_2017[x][0].predict(temp['income_2020'])
    
ghg_2020 = ghg_2020.join(data_2017[['MSOA11CD', 'ccp1', 'ghg']].rename(columns={'ghg':2017}).drop_duplicates().set_index(['MSOA11CD', 'ccp1']).unstack(level='ccp1'))

ghg_2020.sum(axis=1,level=0).boxplot()

"""   
for year in range(2007, 2018):
    fig, axs = plt.subplots(ncols=2, nrows=1)
    data[year].plot(column='total_ghg', ax=axs[0], legend=True)
    axs[0].set_title(str(year) +' GHG')
    data[year].plot(column='Income anonymised', ax=axs[1], legend=True)
    axs[1].set_title(str(year) +' Income')
"""

all_data['year_str'] = 'Y' + all_data['year'].astype(str)
sns.scatterplot(data=all_data, x='total_ghg', y='Income anonymised', hue='year_str', size=0.5)

fname = "r'" + data_directory + "/data/processed/modelling_data.csv'"
all_data[['RGN11NM', 'population', 'Income anonymised', 'total_ghg', 'year', 'year_str']].rename(columns={'Income anonymised':'income'}).reset_index()\
    .drop_duplicates().to_csv(eval(fname))

temp = all_data.set_index(['RGN11NM', 'year_str'], append=True)[['Income anonymised', 'total_ghg']]
for var in ['Income anonymised', 'total_ghg']:
    temp[var] = temp[var] / temp[var].sum()
temp = temp.stack().reset_index()
temp.columns = ['MSOA', 'RGN11NM', 'year_str', 'var', 'value']

sns.boxplot(data=temp, x='year_str', y='value', hue='var')

for reg in temp[['RGN11NM']].drop_duplicates()['RGN11NM']:
    sns.boxplot(data=temp.loc[temp['RGN11NM'] == reg], x='year_str', y='value', hue='var')
    plt.title(reg); plt.ylim(0, temp['value'].max()); plt.show()

sns.boxplot(data=all_data, x='year_str', y='Income anonymised')
sns.boxplot(data=all_data, x='year_str', y='total_ghg')


for year in range(2007, 2018):
    print(data[year][['total_ghg', 'Income anonymised']].corr())
    plt.scatter(data[year]['total_ghg'], data[year]['Income anonymised'], s=0.5)
plt.show()


for year in range(2007, 2018):
    sns.scatterplot(data=data[year], x='total_ghg', y='Income anonymised', hue='RGN11NM', size=0.1, legend=False)
    plt.show()


coicop1 = {year : data[year].loc[:,'1.1.1.1':'Income anonymised'] for year in range(2007, 2018)}
for year in range(2007, 2018):
    coicop1[year].columns = [x.split('.')[0] for x in coicop1[year].columns[:-2]] + ['population', 'income']
    coicop1[year] = coicop1[year].sum(axis=1, level=0)

for i in range(12):
    for year in range(2007, 2018):
        plt.scatter(coicop1[year][str(i+1)], coicop1[year]['income'], s=0.5)
    plt.title('COICOP ' + str(i+1)); plt.xlim(0, 8)
    plt.show()
    
for year in range(2007, 2018):
    print(coicop1[year].loc[:,'1':'12'].max().max())
    
    