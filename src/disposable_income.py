#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar  5 10:15:25 2021

@author: lenakilian
"""

import pandas as pd
import seaborn as sns
import copy as cp
import matplotlib.pyplot as plt

data_directory = "/Users/lenakilian/Documents/Ausbildung/UoLeeds/PhD/Analysis"
output_directory = "/Users/lenakilian/Documents/Ausbildung/UoLeeds/PhD/Analysis/Spatial_Emissions"

data = {}; income = {}; income_compare = {}
for year in range(2011, 2017, 2):
    data[year] = pd.read_csv(eval("r'" + data_directory + "/data/processed/GHG_Estimates/MSOA_mean_" + str(year) + '-' + str(year+1) + ".csv'"))
    income[year] = pd.read_csv(eval("r'" + data_directory + "/data/raw/Income_Data/equivalised_income_" + str(year) + '-' + str(year+1)[2:] + ".csv'"), skiprows=5, header=None)
    income[year].columns = ['MSOA11CD', 'MSO11NM', 'LAD17CD', 'LAD17NM', 'RGN11CD' ,'RGN11NM', 'income_disp', 'Upper confidence limit', 'Lower confidence limit', 'Confidence interval']
    income[year] = income[year].dropna()
    for item in ['income_disp', 'Upper confidence limit', 'Lower confidence limit', 'Confidence interval']:
        income[year][item] = income[year][item].astype(str).str.replace(',', '').astype(float)
        
    income_compare[year] =  income[year].set_index('MSOA11CD')[['income_disp', 'RGN11NM', 'LAD17NM']].join(data[year].set_index('MSOA')[['Income anonymised', 'population']])
        
income_compare[2015]['income_disp'] = income_compare[2015]['income_disp'] / (365/7)

for year in range(2011, 2017, 2):
    sns.scatterplot(data=income_compare[year], y='income_disp', x='Income anonymised', hue='RGN11NM', legend=False); plt.show()


lad_inc = {}; lad_inc_all = pd.DataFrame()
for year in range(2011, 2017, 2):
    temp = cp.copy(income_compare[year])
    temp[['income_disp', 'Income anonymised']] = temp[['income_disp', 'Income anonymised']].apply(lambda x: x*temp['population'])
    temp = temp.groupby(['LAD17NM', 'RGN11NM']).sum()
    temp[['income_disp', 'Income anonymised']] = temp[['income_disp', 'Income anonymised']].apply(lambda x: x/temp['population'])
    lad_inc[year] = temp.reset_index()
    lad_inc[year]['year'] = year
    lad_inc_all = lad_inc_all.append(lad_inc[year])
    
lad_inc_all.to_csv(eval("r'" + data_directory + "/data/processed/GHG_Estimates/LAD_incomes.csv'"))

corr = lad_inc_all.drop('population', axis=1).groupby(['RGN11NM', 'year']).corr()[['income_disp']].unstack(level=1).reset_index()
corr = corr.loc[corr['level_1'] == 'Income anonymised']


for year in range(2011, 2017, 2):
    sns.scatterplot(data=lad_inc[year], y='income_disp', x='Income anonymised', hue='RGN11NM', legend=False); plt.show()

