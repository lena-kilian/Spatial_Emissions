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

dict_cat = 'category_8'
cat_dict = pd.read_excel(wd + '/data/processed/LCFS/Meta/lcfs_desc_anne&john.xlsx')
ghg_list = cat_dict[[dict_cat]].drop_duplicates()[dict_cat].tolist()
ghg_list.remove('other')
ghg_list.remove('Other transport')
ghg_list = [x[:10].replace('/', '').replace(' ', '') for x in ghg_list]

var_list = ['AI2015ln', 'lim', 'pop65', 'pop14', 'bame', 'totalwork', 'totalinc']

var_list2 = ['AI2015_ln', 'lim', 'pop_65.', 'pop_14.', 'bame', 'total_work', 'total_inc']

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
            temp = pd.read_csv(wd + 'Spatial_Emissions/outputs/GWR/global_coeffs/global_coef_london_' + 
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

# Make tidy table
check = all_results.loc[['Max.', 'Min.', 'Median', 'Global Estimate', 'Global pval', 'Global tval']].swaplevel(axis=0).loc['predictor']
        
check = all_results.loc[['Max.', 'Min.', 'Median', 'Global Estimate', 'Global pval', 'Global tval', 'Model fit']].T    
     

for item in check['Global pval'].columns.tolist():
    check[('Global pval str', item)] = ' '
    check.loc[check[('Global pval', item)] < 0.05, ('Global pval str', item)] = '*'
    check.loc[check[('Global pval', item)] < 0.01, ('Global pval str', item)] = '**'
    

keep = [# Model fit
        ('Model fit', 'AIC'), ('Model fit', 'gwR2.adj'),
        # Global coefficients w7 pvalues
        ('Global Estimate', 'predictor'), ('Global pval str', 'predictor'),
        ('Global Estimate', 'Intercept'), ('Global pval str', 'Intercept'),
        ('Global Estimate', 'population'), ('Global pval str', 'population'),
        ('Global Estimate', 'total_inc'), ('Global pval str', 'total_inc'),
        # Local coefficient summary (predictor only)
        ('Min.', 'predictor'), ('Median', 'predictor'), ('Max.', 'predictor')
        ]

check = check[keep]

check[('Desc.', 'DV')] = [x[0].split('_')[0] for x in check.index.tolist()]
check[('Desc.', 'Pred.')] = [x[0].split('_')[1] for x in check.index.tolist()]
check[('Desc.', 'Income controlled')] = [x[1] for x in check.index.tolist()]

check = check.set_index([('Desc.', 'DV'), ('Desc.', 'Pred.'), ('Desc.', 'Income controlled')]).reset_index()

order = dict(zip(var_list, [1, 2, 3, 4, 5, 6, 0]))
order2 = dict(zip([0, 1, 2, 3, 4, 5, 6], ['Income', 'Public Transport Density', 'Pop. limited in day-to-day activities', 
                                          'Pop. aged 65 or older', 'Pop. aged 14 or younger', 'Pop. identifying as BAME', 
                                          'Distance to workplace']))
             
check[('index', 'Pred.')] = check[('Desc.', 'Pred.')].map(order)
check[('Desc.', 'Pred.')] = check[('index', 'Pred.')].map(order2)

check[('index', 'DV')] = check[('Desc.', 'DV')].map(dict(zip(ghg_list, [0, 2, 3, 4, 1])))

check = check.sort_values([('index', 'DV'), ('index', 'Pred.'), ('Desc.', 'Income controlled')])

check.loc[check[('Desc.', 'Income controlled')] == True, ('Desc.', 'Income controlled')] = 'Yes'
check.loc[check[('Desc.', 'Income controlled')] == False, ('Desc.', 'Income controlled')] = 'No'
check.loc[check[('Desc.', 'Pred.')] == 'Income', ('Desc.', 'Income controlled')] = 'Yes'

check.to_csv(wd + 'Spatial_Emissions/outputs/GWR/summary_table.csv')
                 







    
    