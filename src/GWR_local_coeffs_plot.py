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

ghg_list = ['Carvanpu', 'Railandb', 'Flights']
var_list = ['AI2015ln', 'notlim', 'pop65', 'pop14', 'totalwork', 'totalinc']

var_list2 = ['AI2015_ln', 'not_lim', 'pop_65.', 'pop_14.', 'total_work', 'total_inc']

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