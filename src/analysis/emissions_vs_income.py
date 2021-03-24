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


covid_data = pd.read_csv('CovidData/tab/cb_indresp_w.tab', sep='\t')
to_keep = ['cb_hhincome_amount', 'cb_hhincome_period', 'cb_wah', 'cb_gor_dv', 'i_hidp', 'cb_ff_intd', 'cb_ff_intm', 'cb_ff_inty']


data2 = covid_data[to_keep]
data2 = data2.loc[(data2['cb_ff_intm'] > 0) & (data2['cb_ff_intd'] > 0)]
data2['date_str'] = data2['cb_ff_intd'].astype(str) + ' ' + data2['cb_ff_intm'].astype(str) + ' ' + data2['cb_ff_inty'].astype(str)
temp = []
for item in data2['date_str']:
    temp.append(datetime.strptime(item, '%d %m %Y'))
data2['date'] = temp

data3 = data2.groupby(['date', 'cb_gor_dv']).mean().reset_index()
sns.lineplot(data=data3, x='date', y='cb_hhincome_amount', hue='cb_gor_dv')



#covid_data = {}
#for name_extension in []:
#    covid_data[] = pd.read_csv('CovidData/tab/cb_indresp_w.tab', sep='\t')




emissions = pd.read_csv('Estimating_Emissions/Outputs/MSOA/ghg_detailed_2016.csv')
total_emissions = pd.DataFrame(emissions.set_index('MSOA11CD').drop('population', axis=1).sum(1)); total_emissions.columns = ['ghg']
income = pd.read_csv('Income_Data/totalannualincome2016.csv', encoding = 'ISO-8859-1', header=2).set_index('MSOA code')[['Total annual income (£)', 'MSOA name', 'Local authority name', 'Region name']]
income.columns = ['total_income', 'MSOA name', 'Local authority name', 'Region name']; income['total_income'] = income['total_income'].str.replace(',', '').astype(float).dropna()

data = income.join(total_emissions, how='left')

data['co2/gbp'] = data['ghg'] / data['total_income']

shp = gpd.read_file('Geography/Shapefiles/EnglandWales/msoa_2011_ew.shp')
shp = shp.set_index('msoa11cd').join(data)
shp.plot(column='co2/gbp')


q1 = 0.1
q = data.quantile(q=[q1, 1-q1], axis=0, numeric_only=True)

fig, ax = plt.subplots(figsize=(10, 10))
sns.scatterplot(ax=ax, data=data, x='total_income', y='ghg')
ax.axvline(q.loc[q1, 'total_income'], color='r'); ax.axvline(q.loc[1-q1, 'total_income'], color='r')
ax.axhline(q.loc[q1, 'ghg'], color='r'); ax.axhline(q.loc[1-q1, 'ghg'], color='r')
plt.savefig('Graphs/income_vs_emissions.png', dpi=150, bbox_inch='tight')

ghg_cases = data.loc[(data['ghg'] > 7.8) & (data['ghg'] < 8)] # Salford, Manchester, Sheffield

lads = data[['Local authority name']].drop_duplicates().dropna()['Local authority name']
#['Manchester', 'Sheffield', 'Hackney', 'Leeds', 'Southwark', 'Salford']
for lad in lads:
    fig, ax = plt.subplots(figsize=(7.5, 7.5))
    sns.scatterplot(ax=ax, data=data, x='total_income', y='ghg', color='grey')
    sns.scatterplot(ax=ax, data=data.loc[(data['Local authority name'] == lad)], 
                x='total_income', y='ghg', color='b')
    ax.axvline(q.loc[q1, 'total_income'], color='k'); ax.axvline(q.loc[1-q1, 'total_income'], color='k')
    ax.axhline(q.loc[q1, 'ghg'], color='k'); ax.axhline(q.loc[1-q1, 'ghg'], color='k')
    ax.set_title(lad)
    plt.savefig('Graphs/' + lad + '_income_vs_emissions.png', dpi=100, bbox_inch='tight')



income_cases = data.loc[(data['total_income'] > 39000) & (data['total_income'] < 43000)] # Salford, Manchester, Sheffield

ghg_q1 = data.loc[(data['ghg'] < 8) & (data['ghg'] > 7.75)]

leeds = data.loc[(data['Local authority name'] == 'Leeds')]
for var in ['ghg', 'total_income']:
    leeds['pct_' + var] = leeds[var]/leeds[var].sum() * 100
leeds = leeds[['pct_ghg', 'pct_total_income']].stack().reset_index(); leeds.columns = ['MSOA', 'Var', 'Value']

sns.boxplot(data=leeds, x='Var', y='Value')


data2 = cp.copy(data)
for var in ['ghg', 'total_income']:
    data2['pct_' + var] = data2[var]/data2[var].sum() * 100
order = data2.groupby('Region name').mean().sort_values('pct_ghg', ascending=False).index.tolist()
data2 = data2.set_index('Region name')[['pct_ghg', 'pct_total_income']].stack().reset_index(); data2.columns = ['Region', 'Var', 'Value']
sns.boxplot(data=data2, x='Region', y='Value', hue='Var', order=order)
plt.xticks(rotation=45, ha='right')

fig, ax = plt.subplots(figsize=(10, 10))
sns.scatterplot(ax=ax, data=data.groupby(['Region name', 'Local authority name']).mean().reset_index(), x='total_income', y='ghg', hue='Region name')


for region in data[['Region name']].dropna().drop_duplicates()['Region name'].tolist():
    fig, ax = plt.subplots(figsize=(10, 10))
    sns.scatterplot(ax=ax, data=data.loc[data['Region name'] == region], x='total_income', y='ghg')
    ax.set_xlim(19000, 106000); ax.set_ylim(5, 18)
    ax.set_title(region)

#data2 = data.loc[(data['total_income'] < q.loc[0.25, 'total_income']) | (data['total_income'] > q.loc[0.75, 'total_income']) &
#                 (data['ghg'] < q.loc[0.25, 'ghg']) | (data['ghg'] > q.loc[0.75, 'ghg'])]
for region in data[['Region name']].dropna().drop_duplicates()['Region name'].tolist():
    fig, ax = plt.subplots(figsize=(10, 10))
    sns.scatterplot(ax=ax, data=data.loc[data['Region name'] == region], x='total_income', y='ghg')
    ax.axvline(q.loc[q1, 'total_income'], color='r'); ax.axvline(q.loc[1-q1, 'total_income'], color='r')
    ax.axhline(q.loc[q1, 'ghg'], color='r'); ax.axhline(q.loc[1-q1, 'ghg'], color='r')
    ax.set_xlim(19000, 106000); ax.set_ylim(5, 18)
    ax.set_title(region)


LA = 'Leeds'
sns.scatterplot(data=data.loc[data['Local authority name']==LA], x='total_income', y='ghg', size=0.5, color='k')


data3 = data[['total_income', 'ghg']].astype(float)
# plot a kde plot
sns.jointplot(data=data, x='total_income', y='ghg', kind ='hex');

# Setting up the samples 

# Plotting the KDE Plot 
sns.kdeplot(data['ghg'], 
            data['total_income'], 
            color='r', shade=True, Label='Iris_Setosa', 
            cmap="Reds", shade_lowest=False) 
  
sns.kdeplot(data['ghg'], 
            data['total_income'], color='b', 
            shade=True, Label='Iris_Virginica', 
            cmap="Blues", shade_lowest=False) 


lim = {}; lim['ghg'] = 5, 18; lim['total_income'] = 19000, 106000
for var in ['ghg', 'total_income']:
    fig, ax = plt.subplots(figsize=(15*9/3*2, 7.5/3*2))
    order = data.groupby('Local authority name').mean().sort_values(var, ascending=False).index.tolist()
    sns.boxplot(ax=ax, data=data, x='Local authority name', y=var, order=order, hue='Region name')
    ax.set_title(var)
    ax.set_ylim(lim[var])
    plt.xticks(rotation=45, ha='right')
    plt.savefig('Graphs/boxplot_' + var + '.png', dpi=500, bbox_inch='tight')
    

for var in ['ghg', 'total_income']:
    for region in data[['Region name']].dropna().drop_duplicates()['Region name'].tolist():
        fig, ax = plt.subplots(figsize=(15, 7.5))
        data2 = data.loc[data['Region name'] == region]
        order = data2.groupby('Local authority name').mean().sort_values(var, ascending=False).index.tolist()
        sns.boxplot(ax=ax, data=data2, x='Local authority name', y=var, order=order)
        ax.set_title(region)
        ax.set_ylim(lim[var])
        plt.xticks(rotation=45, ha='right')
        plt.savefig('Graphs/boxplot_' + var + '_' + region + '.png', dpi=500, bbox_inch='tight')