#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 29 15:59:34 2021

@author: lenakilian
"""

import LCFS_Income_functions as lcfs


wd = '/Users/lenakilian/Documents/Ausbildung/UoLeeds/PhD/Analysis'
geogs = ['MSOA']
combine_years = 2
sd_limit = 3.5

first_year = 2007
last_year = 2018


# cannot combine 2013 and 2014 - so have to take mean here!

for geog in geogs:
#####################
# aggregate incomes #
#####################
    
    # aggregate income for years if boundary crosses 20013 and 2014 
    if first_year <= 2013 and last_year >= 2013 and 2014 not in list(range(first_year, last_year, combine_years)) and combine_years > 1:
        print('Using mean income for 2013 2014 OAC boundary crossing')
        
        geog_inc_detailed = {}; temp_inc = {}
        
        year_combinations = lcfs.get_year_combinations(first_year, last_year, combine_years)
            
        if len(list(year_combinations.keys())) > 1:
            
            items = list(year_combinations.keys())
            items.remove('2013_boundary')
            
            for item in items:
                start_year = year_combinations[item][0]
                end_year = year_combinations[item][1]
    
                temp_inc = lcfs.estimate_income(geog, start_year, end_year, combine_years, wd, sd_limit)
                
                for year in list(temp_inc.keys()):
                    geog_inc_detailed[year] = temp_inc[year]
        
        # OAC change after 2013, so need to combine datasets differently
        inc_by_year = lcfs.estimate_income(geog, year_combinations['2013_boundary'][0], year_combinations['2013_boundary'][1], 1, wd, sd_limit)
        inc_mean_2013 = lcfs.mean_spend_2013_bounday(inc_by_year, wd)
        
        geog_inc_detailed[year_combinations['2013_boundary'][0]] = inc_mean_2013
     
                 
    # aggregate income for years if boundary does NOT cross 2013 and 2014 
    else:
        print('Using aggregated income from OAC')
        geog_inc_detailed = lcfs.estimate_income(geog, first_year, last_year, combine_years, wd, sd_limit)
        
    # save expenditure
    lcfs.save_geog_income(geog, geog_inc_detailed, wd)
