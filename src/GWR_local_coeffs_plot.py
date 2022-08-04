#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar  5 10:15:25 2021

@author: lenakilian
"""

import pandas as pd
import copy as cp
import geopandas as gpd
import seaborn as sns
import matplotlib.pyplot as plt


wd = r'/Users/lenakilian/Documents/Ausbildung/UoLeeds/PhD/Analysis/'
years = list(range(2007, 2018, 2))
geog = 'MSOA'

yr = 2015

dict_cat = 'category_8'

cat_dict = pd.read_excel(wd + '/data/processed/LCFS/Meta/lcfs_desc_anne&john.xlsx')
ghg_list = cat_dict[[dict_cat]].drop_duplicates()[dict_cat].tolist()
ghg_list.remove('other')
ghg_list.remove('Other transport')
ghg_list = [x[:10].replace('/', '').replace(' ', '') for x in ghg_list]

#ghg_list = ['Carvanpu', 'Railandb', 'Flights']
var_list = ['AI2015ln', 'lim', 'pop65', 'pop14', 'bame', 'totalwork', 'totalinc']

var_list2 = ['AI2015_ln', 'lim', 'pop_65.', 'pop_14.', 'bame', 'total_work', 'total_inc']

global_results = pd.DataFrame()
for ghg in ghg_list:
    for i in range(len(var_list)):
        var = var_list[i]
        temp = pd.read_csv(wd + 'Spatial_Emissions/outputs/GWR/global_coeffs/global_coef_london_' + 
                           ghg + '_' + var + '_' + str(yr) + '.csv', index_col = 0)\
            .loc['Global Estimate':'Global Estimate', var_list2[i]:var_list2[i]].T
        temp['transport'] = ghg
        temp['pred'] = var
        temp['income_controlled'] = False
        global_results = global_results.append(temp)
        
        if var != 'totalinc':
            temp = pd.read_csv(wd + 'Spatial_Emissions/outputs/GWR/global_coeffs/global_coef_london_' + 
                               ghg + '_' + var + '_' + str(yr) + '_w-inc.csv', index_col = 0)\
                .loc['Global Estimate':'Global Estimate', var_list2[i]:var_list2[i]].T
            temp['transport'] = ghg
            temp['pred'] = var
            temp['income_controlled'] = True
            global_results = global_results.append(temp)
        

local_results = pd.DataFrame()
for ghg in ghg_list:
    for i in range(len(var_list)):
        var = var_list[i]
        temp = pd.read_csv(wd + 'Spatial_Emissions/outputs/GWR/local_coeffs/local_coef_london_' + 
                           ghg + '_' + var + '_' + str(yr) + '.csv', index_col = 0)
        temp.columns = ['MSOA11CD', 'local_coeffs']
        temp['transport'] = ghg
        temp['pred'] = var
        temp['income_controlled'] = False
        local_results = local_results.append(temp)
        
        if var != 'totalinc':
            temp = pd.read_csv(wd + 'Spatial_Emissions/outputs/GWR/local_coeffs/local_coef_london_' + 
                               ghg + '_' + var + '_' + str(yr) + '_w-inc.csv', index_col = 0)
            temp.columns = ['MSOA11CD', 'local_coeffs']
            temp['transport'] = ghg
            temp['pred'] = var
            temp['income_controlled'] = True
            local_results = local_results.append(temp)
            

for ghg in ghg_list:
    for var in var_list:
        for option in [True, False]:
            if var == 'totalinc' and option == True:
                pass
            else:
                data = local_results.loc[(local_results['transport'] == ghg) & 
                                         (local_results['pred'] == var) &
                                         (local_results['income_controlled'] == option)]
                global_val = global_results.loc[(global_results['transport'] == ghg) & 
                                                (global_results['pred'] == var) &
                                                (global_results['income_controlled'] == option)]
            sns.distplot(data['local_coeffs'])
            plt.title(ghg + '_' + var + '_inccont:_' + str(option));
            plt.axvline(x=global_val['Global Estimate'][0])
            plt.show()
            
local_results.merge(global_results, on=['transport', 'pred', 'income_controlled'])\
    .to_csv(wd + 'Spatial_Emissions/outputs/GWR/local_coeffs/all_for_plot.csv')
    
    
check = cp.copy(local_results)
check['>0'] = False; check.loc[check['local_coeffs'] >0, '>0'] = True
check = check.groupby(['transport', 'pred', 'income_controlled', '>0']).describe().droplevel(axis=1, level=0)[['count']].unstack(level='>0')

check = local_results.groupby(['transport', 'pred', 'income_controlled']).describe().join(check)


