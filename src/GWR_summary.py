#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar  5 10:15:25 2021

@author: lenakilian
"""

import pandas as pd
import copy as cp
import geopandas as gpd


wd = r'/Users/lenakilian/Documents/Ausbildung/UoLeeds/PhD/Analysis/'
years = list(range(2007, 2018, 2))
geog = 'MSOA'

yr = 2015

ghg_list = ['Carvanpu', 'Railandb', 'Flights']
var_list = ['AI2015ln', 'notlim', 'pop65', 'pop14', 'totalwork', 'totalinc']

var_list2 = ['AI2015_ln', 'not_lim', 'pop_65.', 'pop_14.', 'total_work', 'total_inc']

model_fit = ['RSS.gw', 'AIC', 'AICc', 'enp', 'edf', 'gw.R2', 'gwR2.adj', 'BIC']
global_results = {}
for ghg in ghg_list:
    for var in var_list:
        global_results[ghg + '_' + var] = pd.read_csv(wd + 'Spatial_Emissions/outputs/GWR/global_coeffs/global_coef_london_' + 
                                                      ghg + '_' + var + '_' + str(yr) + '.csv')
        fit = global_results[ghg + '_' + var][model_fit].drop_duplicates().T.reset_index()
        fit['Summary'] = 'Model fit'
        fit.columns = ['Measure', 'Value', 'Summary']
        global_results[ghg + '_' + var] = global_results[ghg + '_' + var].set_index(['Unnamed: 0']).drop(model_fit, axis=1).\
            stack().reset_index().drop_duplicates()
        global_results[ghg + '_' + var].columns = ['Summary', 'Measure', 'Value']
        
        global_results[ghg + '_' + var] = global_results[ghg + '_' + var].append(fit)
            
        global_results[ghg + '_' + var]['income_control'] = False
        
        if var != 'totalinc':
            temp = pd.read_csv(wd + 'Spatial_Emissions/outputs/GWR/global_coef_london_' + 
                                                      ghg + '_' + var + '_' + str(yr) + '_w-inc.csv')
            
            fit = temp[model_fit].drop_duplicates().T.reset_index()
            fit['Summary'] = 'Model fit'
            fit.columns = ['Measure', 'Value', 'Summary']
            temp = temp.set_index(['Unnamed: 0']).drop(model_fit, axis=1).\
                stack().reset_index().drop_duplicates()
            temp.columns = ['Summary', 'Measure', 'Value']
            temp = temp.append(fit)
            temp['income_control'] = True
        
            global_results[ghg + '_' + var] = global_results[ghg + '_' + var].append(temp)
            
        global_results[ghg + '_' + var] = global_results[ghg + '_' + var].set_index(['Summary', 'Measure', 'income_control'])
        global_results[ghg + '_' + var] = global_results[ghg + '_' + var].unstack(level='income_control')
        
all_results = pd.DataFrame(index = global_results[ghg_list[0] + '_' + var_list[0]].rename(index={var_list2[0]:'predictor'}).index)
for ghg in ghg_list:
    for i in range(len(var_list)):
        var = var_list[i]
        
        temp = cp.copy(global_results[ghg + '_' + var]).rename(index={var_list2[i]:'predictor'})
        temp.columns = pd.MultiIndex.from_arrays([[ghg + '_' + var] * len(temp.columns), temp.columns.levels[1].tolist()])
        
        all_results = all_results.join(temp, how='left')
all_results = all_results.dropna(how='all')


check = all_results.loc[['Max.', 'Min.', 'Median', 'Global Estimate', 'Global pval', 'Global tval']].swaplevel(axis=0).loc['predictor']
        
check = all_results.loc[['Max.', 'Min.', 'Median', 'Global Estimate', 'Global pval', 'Global tval', 'Model fit']].T       
     
