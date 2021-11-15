#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 18 2021

Aggregating expenditure groups for LCFS by OAC x Region Profiles & UK Supergroups

@author: lenakilian
"""

import pandas as pd
import copy as cp
import pickle
import numpy as np


def import_lcfs(year, dvhh_file, dvper_file):
    
    idx = {}; idx['person'] = {}; idx['hhld'] = {}

    idx['person']['to_keep'] = ['person', 'a012p', 'a013p']
    idx['person']['new_name'] = ['person_no', 'ethnicity_hrp', 'ethnicity partner hrp', 'income tax']
    idx['person']['dict'] = dict(zip(idx['person']['to_keep'], idx['person']['new_name']))

    idx['hhld']['to_keep'] = ['weighta', 'p396p', 'sexhrp']
    idx['hhld']['new_name'] = ['weight', 'age HRP', 'sex HRP']
    idx['hhld']['dict'] = dict(zip(idx['hhld']['to_keep'], idx['hhld']['new_name']))
    
    dvhh = pd.read_csv(eval(dvhh_file), sep='\t', index_col=0)
    dvper = pd.read_csv(eval(dvper_file), sep='\t', index_col=0)
    
    dvhh.columns = dvhh.columns.str.lower()
    dvper.columns = dvper.columns.str.lower()
     
    person_data = dvper[idx['person']['to_keep']].rename(columns=idx['person']['dict'])
    person_data['income tax'] = np.zeros(shape=np.size(dvper,0))
    
    useful_data = dvhh[idx['hhld']['to_keep']].rename(columns=idx['hhld']['dict'])
    
    temp = useful_data.join(person_data, how = 'inner')
    temp = temp.apply(lambda x: pd.to_numeric(x, errors='coerce')).fillna(0)
    
    useful_data['owned_prop'] = dvhh['a121']
    useful_data.loc[(useful_data['owned_prop'] == 5) | (useful_data['owned_prop'] == 6) | 
                    (useful_data['owned_prop'] == 7), 'owned_prop'] = True
    useful_data.loc[(useful_data['owned_prop'] != True), 'owned_prop'] = False
    useful_data['ethnicity HRP'] = temp.groupby(level=0)['ethnicity_hrp'].sum()
    useful_data['no people'] = dvhh['a049']
    useful_data['type of hhold'] = dvhh['a062']
    useful_data['category of dwelling'] = dvhh['a116']
    useful_data['tenure type'] = dvhh['a122']
    useful_data['GOR modified'] = dvhh['gorx']
    useful_data['OA class 1D'] =  np.zeros(shape=len(dvhh))
    # OAC data only available from 2007
    if year > 2006: 
        useful_data['OAC_Supergroup'] = dvhh['oac1d']
        useful_data['OAC_Group'] = dvhh['oac2d']
        useful_data['OAC_Subgroup'] = dvhh['oac3d']
    useful_data['Income anonymised'] = dvhh['incanon']
    useful_data['Income tax'] = temp.groupby(level=0)['income tax'].sum()
    useful_data['Socio-ec HRP'] = dvhh['a091']
    
    if year < 2005:
        useful_data['rooms in accommodation'] = dvhh['a114']
    else:
        useful_data['rooms in accommodation'] = dvhh['a114p']
    
    return(useful_data)



# import LCFS data and adjust flights and rent
def import_income(first_year, last_year, combined_years, working_directory):
    
    if (first_year < 2007) | (last_year > 2018):
        print('Error: Please select year values between 2007-2018 (incl.)')
    elif first_year > last_year:
        print('Error: first_year > last_year')
    else:    
        pass
    if combined_years < 1:
        print('Error: Please choose a value of 1 or greater for combined_years')
    else:    
        pass
        
    all_years = list(range(2007, 2019))
    lcf_years = dict(zip(all_years, ['2007', '2008', '2009', '2010', '2011', '2012', '2013', '2014', '2015-2016', '2016-2017', '2017-2018', '2018-2019']))
    
    years = list(range(first_year, last_year + 1))
    
    # create data directory from working directory
    data_directory = working_directory + "/data/"
    
    # load LFC data
    hhdspend_lcfs = {}
        
    for year in years:
        file_dvhh = "r'" + data_directory + "raw/LCFS/" + lcf_years[year] + '/tab/' + lcf_years[year] + "_dvhh_ukanon.tab'"
        file_dvper = "r'" + data_directory + "raw/LCFS/" + str(lcf_years[year]) + '/tab/' + str(lcf_years[year]) + "_dvper_ukanon.tab'"
        hhdspend_lcfs[year] = import_lcfs(year, file_dvhh, file_dvper).drop_duplicates()
        for col in ['GOR modified', 'OAC_Supergroup', 'OAC_Group', 'OAC_Subgroup']:
            hhdspend_lcfs[year][col] = hhdspend_lcfs[year][col].astype(str).str.upper().str.replace(' ', '')
            hhdspend_lcfs[year].loc[hhdspend_lcfs[year][col].str.len() < 1, col] = '0'
            hhdspend_lcfs[year]['GOR modified'] = hhdspend_lcfs[year]['GOR modified'].astype(int)
            
    # merge years
    hhdspend_lcfs_combined = {}
    if (last_year - first_year) % combined_years == 0:
        end = last_year + 1
    else:
        end = last_year
    years_combined = list(range(first_year, end, combined_years))
    for year in years_combined:
        hhdspend_lcfs_combined[year] = cp.copy(hhdspend_lcfs[year])
        hhdspend_lcfs_combined[year].index = [str(year) + '-' + str(x) for x in hhdspend_lcfs_combined[year].index]
        if combined_years > 1:
            year_list = [] # check if boundary between 2013 and 2014 boundary is kept
            for i in range(1, combined_years):
                # check 2013 & 2014 boudary
                year_list.append(year + i)
                if (2013 in year_list) & (2014 in year_list):
                    print('Error: Please separate 2013 and 2014')
                else:
                    pass
                # continue appending years
                temp = cp.copy(hhdspend_lcfs[year + i])
                temp.index = [str(year + i) + '-' + str(x) for x in temp.index]
                hhdspend_lcfs_combined[year] = hhdspend_lcfs_combined[year].append(temp)
        hhdspend_lcfs_combined[year].index = hhdspend_lcfs_combined[year].index.rename('case')
        
    return(hhdspend_lcfs_combined)


def get_year_combinations(first_year, last_year, combine_years):
    year_combinations = {}
    
    check_years = []
    for item in list(range(first_year, last_year, combine_years)):
        if item <= 2013:
            check_years.append(item)
    start_year_2013 = min(check_years, key=lambda x:abs(x-2013))
    end_year_2013 = start_year_2013 + combine_years - 1
        
    year_combinations['2013_boundary'] = [start_year_2013, end_year_2013]
    
    if last_year > end_year_2013:
        year_combinations['higher'] = [first_year, start_year_2013 - 1]

    if first_year < start_year_2013:
        year_combinations['lower'] = [end_year_2013 + 1, last_year]
            
    return(year_combinations)


def mean_inc_2013_bounday(exp_by_year, wd):
    
    lookup = pd.read_csv(eval("r'" + wd + "/data/raw/Geography/Conversion_Lookups/UK_full_lookup_2001_to_2011.csv'"))
    lookup_msoa = lookup[['MSOA01CD', 'MSOA11CD']].drop_duplicates()
            
    new_exp_2013 = pd.DataFrame()
    for year in list(exp_by_year.keys()):
        # import ghg and income
        if year > 2013:
            exp_by_year[year] = exp_by_year[year].join(lookup_msoa.set_index('MSOA11CD')).set_index('MSOA01CD').mean(axis=0, level='MSOA01CD')
        exp_by_year[year]['year'] = year
        new_exp_2013 = new_exp_2013.append(exp_by_year[year])
            
    new_exp_2013 = new_exp_2013.mean(axis=0, level='MSOA01CD').drop('year', axis=1)
            
    return(new_exp_2013)



def winsorise(hhdspend_lcfs_combined, sd_limit):
    new_hhspend_all = {}
    
    for year in list(hhdspend_lcfs_combined.keys()):
        keep = ['Income anonymised', 'Income tax']
        means = pd.DataFrame(hhdspend_lcfs_combined[year][keep].mean())
        sd = pd.DataFrame(hhdspend_lcfs_combined[year][keep].std())

        new_hhspend = hhdspend_lcfs_combined[year][keep].T
        new_hhspend['sd'] = sd; new_hhspend['mean'] = means

        new_hhspend.columns = pd.MultiIndex.from_arrays([['og' for x in new_hhspend.columns[:-2]] + ['summary', 'summary'], new_hhspend.columns.tolist()])
        new_hhspend = new_hhspend.droplevel(axis=1, level=0)

        for item in new_hhspend.columns[:-2]:
            new_hhspend.loc[new_hhspend[item] > new_hhspend['mean'] + (sd_limit * new_hhspend['sd']), item] = new_hhspend['mean'] + (sd_limit * new_hhspend['sd'])
            new_hhspend.loc[new_hhspend[item] < new_hhspend['mean'] - (sd_limit * new_hhspend['sd']), item] = new_hhspend['mean'] - (sd_limit * new_hhspend['sd'])
    
        new_hhspend_all[year] = hhdspend_lcfs_combined[year].drop(keep, axis=1).join(new_hhspend.T, how='left')
        new_hhspend_all[year] = new_hhspend_all[year][hhdspend_lcfs_combined[year].columns.tolist()]
    
    return(new_hhspend_all)


def check_missing_oac(hhdspend_lcfs, years):
    hhdspend_missingoac = {}; hhdspend_product = {}
    for year in years:
        temp = hhdspend_lcfs[year].loc[:,'1.1.1.1':'12.5.3.5'].apply(lambda x: x / hhdspend_lcfs[year]['no people'])
        temp.columns = pd.MultiIndex.from_arrays([[str(x).split('.')[0] for x in temp.columns.tolist()], [x for x in temp.columns.tolist()]])
        temp = temp.sum(level=0, axis=1)
        temp['Total Expenditure'] = temp.sum(1)
        temp = temp.join(hhdspend_lcfs[year][['weight', 'no people', 'OAC_Supergroup', 'GOR modified']])
        temp['OAC_Supergroup'] = pd.to_numeric(temp['OAC_Supergroup'], errors='coerce')
        temp.loc[temp['OAC_Supergroup'].isna() == True, 'OAC_Supergroup'] = 0
        temp['Missing OAC'] = False; temp.loc[temp['OAC_Supergroup'] == 0, 'Missing OAC'] = True
        hhdspend_missingoac[year] = temp
    
        hhdspend_product[year] = pd.DataFrame(columns=['Missing OAC', 'GOR modified', 'Expenditure', 'Product Type'])
        idx = [str(x) for x in range(1, 13)] + ['weight', 'no people']
        for j in idx:
            temp = hhdspend_missingoac[year][[j, 'Missing OAC', 'GOR modified']].rename(columns={j:'Expenditure'})
            temp['Product Type'] = j
            hhdspend_product[year] = hhdspend_product[year].merge(temp, on=['Missing OAC', 'GOR modified', 'Expenditure', 'Product Type'], how='outer')
    return(hhdspend_missingoac, hhdspend_product)

#count OAC Subgroups in LCFS
def count_oac(hhdspend_lcfs, all_oac, years):
    full_index_lookup = {}; full_index = {}
    for year in years:
        subgroup_totals = hhdspend_lcfs[year][['GOR modified', 'OAC_Subgroup']]
        subgroup_totals.columns = ['GOR', 'Subgroup']
        subgroup_totals['count'] = 1
        subgroup_totals = subgroup_totals.groupby(['GOR', 'Subgroup']).sum()
        # merge the two, use UK OA index, fill with LCFS count
        if year < 2014:
            oac_year = '2001'
        else:
            oac_year = '2011'
        count_oac = all_oac[oac_year][['GOR', 'Subgroup']]
        count_oac = count_oac.drop_duplicates().set_index(['GOR', 'Subgroup']).join(subgroup_totals).fillna(0).reset_index()
        count_oac['Supergroup'] = [x[0] for x in count_oac['Subgroup']]; count_oac['Group'] = [x[:-1] for x in count_oac['Subgroup']]
        count_oac = count_oac.set_index(['GOR', 'Supergroup', 'Group', 'Subgroup'])

        full_index_lookup[year] = {}
        temp = count_oac; temp['OAC'] = [str(x[0]) + '_' + x[3] for x in count_oac.index.tolist()]
        full_index_lookup[year]['Subgroup_pass'] = temp.loc[temp['count'] >= 10]
    
        temp = temp.loc[temp['count'] < 10].drop_duplicates()
        OACs = temp.reset_index().groupby(['GOR', 'Supergroup', 'Group'])['OAC'].apply(', '.join); OACs.columns = ['OAC']
        temp = temp.sum(level=['GOR', 'Supergroup', 'Group']).join(OACs).drop_duplicates()
        full_index_lookup[year]['Group_pass'] = temp.loc[temp['count'] >= 10]
        full_index_lookup[year]['Group_pass'] = full_index_lookup[year]['Group_pass'].join(full_index_lookup[year]['Group_pass']['OAC'].str.split(', ', expand = True))
    
        temp = temp.loc[temp['count'] < 10].drop_duplicates()
        OACs = temp.reset_index().groupby(['GOR', 'Supergroup'])['OAC'].apply(', '.join); OACs.columns = ['OAC']
        temp = temp.sum(level=['GOR', 'Supergroup']).join(OACs).drop_duplicates()
        full_index_lookup[year]['Supergroup_pass'] = temp.loc[temp['count'] >= 10]
        full_index_lookup[year]['Supergroup_pass'] = full_index_lookup[year]['Supergroup_pass'].join(full_index_lookup[year]['Supergroup_pass']['OAC'].str.split(', ', expand = True))
        
        temp = temp.loc[temp['count'] < 10]
        OACs = temp.reset_index().groupby(['Supergroup'])['OAC'].apply(', '.join); OACs.columns = ['OAC']
        temp = temp.sum(level=['Supergroup']).join(OACs).drop_duplicates()
        full_index_lookup[year]['Supergroup_UK_pass'] = temp.loc[temp['count'] >= 10].drop_duplicates()
        full_index_lookup[year]['Supergroup_UK_pass'] = full_index_lookup[year]['Supergroup_UK_pass']
        
        full_index_lookup[year]['Supergroup_UK_fail'] = temp.loc[temp['count'] < 10].drop_duplicates()
        full_index_lookup[year]['Supergroup_UK_fail'] = full_index_lookup[year]['Supergroup_UK_fail'].drop_duplicates()
        
        # extract those with enough data for full_index
        check = full_index_lookup[year]['Subgroup_pass'].reset_index().drop(['Supergroup', 'Group'], axis=1).rename(columns={'Subgroup':'OAC_label'})[['GOR', 'OAC_label', 'count', 'OAC']]
        if len(full_index_lookup[year]['Group_pass']) > 0:
            temp = full_index_lookup[year]['Group_pass'].reset_index().drop(['Supergroup'], axis=1).rename(columns={'Group':'OAC_label'})
            check = check.append(temp[['GOR', 'OAC_label', 'count', 'OAC']])
        if len(full_index_lookup[year]['Supergroup_pass']) > 0:
            temp = full_index_lookup[year]['Supergroup_pass'].reset_index().rename(columns={'Supergroup':'OAC_label'})
            check = check.append(temp[['GOR', 'OAC_label', 'count', 'OAC']])
        if len(full_index_lookup[year]['Supergroup_UK_pass']) > 0:
            temp = full_index_lookup[year]['Supergroup_UK_pass'].reset_index().rename(columns={'Supergroup':'OAC_label'}); temp['GOR'] = 0
            check = check.append(temp[['GOR', 'OAC_label', 'count', 'OAC']])
        if len(full_index_lookup[year]['Supergroup_UK_fail']) > 0:
            temp = full_index_lookup[year]['Supergroup_UK_fail'].reset_index().drop('Supergroup', axis=1); temp['GOR'] = 0; temp['OAC_label'] = '0' 
            check = check.append(temp[['GOR', 'OAC_label', 'count', 'OAC']])
            
        check.index = list(range(len(check)))

        idx = pd.DataFrame(check['OAC'].str.split(',', expand=True).stack()).dropna(how='all').droplevel(level=1).join(check)
        idx['GOR modified'] = [x.split('_')[0].replace(' ', '') for x in idx[0]]
        idx['OAC_Subgroup'] = [x.split('_')[1].replace(' ', '') for x in idx[0]]
        idx = idx.drop('OAC', axis=1).rename(columns={'OAC_label':'OAC'})
        
        full_index[year] = idx.rename(columns={0:'GOR_OAC'}).set_index(['GOR modified', 'OAC_Subgroup'])
    
    return(full_index_lookup, full_index)

# attach expenditures to OAC classifications made
def attach_exp(hhdspend_lcfs, full_index, years):
    full_exp = {}
    for year in years:
        # calculate per capita expenditure
        check = hhdspend_lcfs[year].reset_index()
        check['GOR modified'] = check['GOR modified'].astype(str)
        check = check.set_index(['GOR modified', 'OAC_Subgroup'])[['case', 'no people', 'weight']].join(full_index[year]).reset_index().set_index('case')
        check['pop'] = check['weight'] * check['no people']

        inc = hhdspend_lcfs[year][['Income anonymised', 'Income tax']]

        check = check[['GOR modified', 'OAC', 'GOR', 'pop', 'weight', 'no people']].join(inc)
        
        full_exp[year] = check.reset_index().drop_duplicates().set_index('case')
    return(full_exp)

def agg_groups(hhdspend_lcfs, full_exp, years):
    hhdspend_full_index = {}; hhdspend_oac = {}
    for year in years:
        # save all OAC levels
        hhdspend_oac[year] = {}
        spend = hhdspend_lcfs[year]  
        spend['pop'] = spend['no people'] * spend['weight']
        spend[['Income anonymised', 'Income tax']] = spend[['Income anonymised', 'Income tax']].apply(lambda x: x * spend['weight'])
        for region in ['GOR', 'no_GOR']:
            hhdspend_oac[year][region] = {}
            for level in ['Supergroup', 'Group', 'Subgroup']:
                if region == 'GOR':
                    group = ['GOR modified', 'OAC_' + level]
                else:
                    group = ['OAC_' + level]
                spend.loc[spend['OAC_' + level].isna() == True, 'OAC_' + level] = '0'
                spend['OAC_' + level] = spend['OAC_' + level].astype(str)
                temp = spend.groupby(group).sum()
                temp[['Income anonymised', 'Income tax']] = temp[['Income anonymised', 'Income tax']].apply(lambda x: x/temp['pop'])
                hhdspend_oac[year][region][level] = temp
        # for detailed OACxLCFS
        spend = full_exp[year]
        spend[['Income anonymised', 'Income tax']] = spend[['Income anonymised', 'Income tax']].apply(lambda x: x*spend['weight'])
        spend['count'] = 1
        spend = spend.fillna(0).drop('GOR modified', axis=1).rename(columns={'GOR':'GOR modified'}).groupby(['GOR modified', 'OAC']).sum()
        spend[['Income anonymised', 'Income tax']] = spend[['Income anonymised', 'Income tax']].apply(lambda x: x/spend['pop'])
        hhdspend_full_index[year] = spend.drop(['weight', 'no people'], axis=1)
    return(hhdspend_full_index, hhdspend_oac)


def detailed_oac_aggregation(hhdspend_full_index, oac_all, hhdspend_oac):
    OA_exp_detailed = {}
    for year in list(hhdspend_full_index.keys()): 
        OAC_detailed = hhdspend_full_index[year].loc[hhdspend_full_index[year]['count'] >= 10].reset_index()
        OAC_detailed['OAC'] = OAC_detailed['OAC'].str.upper()
        #OAC_detailed = OAC_detailed.set_index(['GOR modified', 'OAC'])
    
        oac_temp = oac_all[year].drop_duplicates().rename(columns={'OA01CD':'OA_Code', 'OA11CD':'OA_Code'})[
            ['OA_Code', 'GOR modified', 'OAC_Supergroup', 'OAC_Group', 'OAC_Subgroup', 'population']]
        #pop = oac_temp[['OA_Code', 'population']]
    
        temp = {}; OA_list = oac_temp['OA_Code'].to_list()
        for var in ['OAC_Subgroup', 'OAC_Group', 'OAC_Supergroup']:
            oac_var = oac_temp.loc[oac_temp['OA_Code'].isin(OA_list) == True]
            oac_var['OAC'] = oac_var[var].str.upper()
            
            temp[var] = oac_var[['OA_Code', 'GOR modified', 'OAC', 'population']]\
                .merge(OAC_detailed.drop('pop', axis=1), on=['GOR modified', 'OAC'], how='left')\
                    .set_index(['OA_Code', 'GOR modified', 'OAC'])
                
            OA_list = temp[var].loc[temp[var]['Income anonymised'].isna() == True].reset_index()['OA_Code'].to_list()
            temp[var] = temp[var].loc[temp[var]['Income anonymised'].isna() == False]
  
        if len(OA_list) > 0:    
            oac_var = oac_temp.loc[oac_temp['OA_Code'].isin(OA_list) == True]
            oac_var['OAC'] = oac_var['OAC_Supergroup'].str.upper()
            
            temp_exp = hhdspend_oac[year]['no_GOR']['Supergroup'][['Income anonymised', 'Income tax']].reset_index()\
                .rename(columns={'OAC_Supergroup':'OAC'})
                
            temp['UK_all'] = oac_var[['OA_Code', 'GOR modified', 'OAC', 'population']]\
                .merge(temp_exp, on=['OAC'], how='left')\
                    .set_index(['OA_Code', 'GOR modified', 'OAC'])

        OA_exp_detailed[year] = temp['OAC_Subgroup'].append(temp['OAC_Group']).append(temp['OAC_Supergroup'])\
            .append(temp['UK_all'])
    return(OA_exp_detailed)


def geog_aggregation(OA_exp_detailed, oac_all, years, geog_level):
    new_ghg_detailed= {}
    for year in list(OA_exp_detailed.keys()):
        if year > 2013:
            oac_year = 2011
        else:
            oac_year = 2001

        geog_var = geog_level + str(oac_year)[2:] + 'CD'
        
        geog_lookup = oac_all['oa_' + str(oac_year)].rename(columns={'OA_SA':'OA_Code'})[['OA_Code', geog_var]]\
            .drop_duplicates().set_index('OA_Code')

        temp = OA_exp_detailed[year].droplevel(['GOR modified', 'OAC'])
        temp = temp.join(geog_lookup)
        temp = temp.set_index([geog_var], append=True)
        
        temp[['Income anonymised', 'Income tax']] = temp[['Income anonymised', 'Income tax']].apply(lambda x: x * temp['population'])
    
        new_ghg_detailed[year] = temp.groupby(geog_var).sum()
        new_ghg_detailed[year][['Income anonymised', 'Income tax']] = new_ghg_detailed[year][['Income anonymised', 'Income tax']]\
            .apply(lambda x: x / new_ghg_detailed[year]['population'])
    return(new_ghg_detailed)


# Assign expenditure to OAs
def attach_oac_grouping(hhdspend_lcfs_combined, wd):

    years_combined = list(hhdspend_lcfs_combined.keys())
    data_directory = wd + "/data/"
    
    # check totals per group
    # these are all OAs in the UK
    all_oac = pd.read_excel(eval("r'" + data_directory + "raw/Geography/Output_Area_Classification/OACxRegion.xlsx'"), sheet_name=None)
    for year in ['2001', '2011']:
        all_oac[year]['GOR'] = all_oac[year]['GOR modified']
        all_oac[year]['Supergroup'] = all_oac[year]['Supergroup'].astype(str)
    
    # count OAC Subgroups in LCFS
    full_index_lookup, full_index = count_oac(hhdspend_lcfs_combined, all_oac, years_combined)
        
    # Attach OAC expenditure to index
    full_exp = attach_exp(hhdspend_lcfs_combined, full_index, years_combined)
    
    # Aggregate expenditure
    hhdspend_full_index, hhdspend_oac = agg_groups(hhdspend_lcfs_combined, full_exp, years_combined)
        
    return(hhdspend_full_index, hhdspend_oac) 


def get_oac_census(years_combined, working_directory):

    data_directory = working_directory + "/data/"   
    
    # Get OA data to create profile by OA
    # combine with OAs (2007-2013, and 2014-2016)
    # Region (GOR) lookup
    fname = "r'" + data_directory + "raw/LCFS/2016-2017/mrdoc/excel/8351_volume_f_derived_variables_201617_final.xls'"
    gor_lookup = pd.read_excel(eval(fname), sheet_name='Part 4').iloc[920:932, 1:3]
    gor_lookup.columns=['GOR_name', 'GOR modified']
    gor_lookup['GOR_code'] = gor_lookup['GOR_name'].str.lower().str.replace(' ', '').str[:7]
    
    oac_all = {}
    # 2001 OAC
    oac_2001 = pd.read_csv(eval("r'" + data_directory + "raw/Geography/Conversion_Lookups/UK_full_lookup_2001.csv'")).drop_duplicates()
    oac_2001.loc[oac_2001['RGN01NM'] == 'East', 'RGN01NM'] = 'Eastern'
    oac_2001['GOR_code'] = oac_2001['RGN01NM'].str.lower().str.replace(' ', '').str[:7]
    oac_2001 = oac_2001.merge(gor_lookup, on='GOR_code')
    oac_all['oa_2001'] = oac_2001.drop_duplicates()

    # 2011 OAC
    full_lookup = pd.read_csv(eval("r'" + data_directory + "raw/Geography/Conversion_Lookups/UK_full_lookup_2001_to_2011.csv'"))
    oac_2011 = full_lookup[['OAC11CD', 'OA11CD', 'LSOA11CD', 'MSOA11CD', 'LAD17NM', 'RGN11NM']].drop_duplicates()
    oac_2011.loc[oac_2011['RGN11NM'] == 'East of England', 'RGN11NM'] = 'Eastern'
    oac_2011['GOR_code'] = oac_2011['RGN11NM'].str.lower().str.replace(' ', '').str[:7]
    oac_2011 = oac_2011.merge(gor_lookup, on='GOR_code')
    oac_all['oa_2011'] = oac_2011


    # clean OAC and import OA populations
    oa_populations = {}
    for year_code in ['oa_2001', 'oa_2011']:
        year_end = year_code[-2:]
        
        # tidy OAC
        oac_all[year_code]['OAC_Supergroup'] = oac_all[year_code]['OAC' + year_end + 'CD'].str[0]
        oac_all[year_code]['OAC_Group'] = oac_all[year_code]['OAC' + year_end + 'CD'].str[:2]
        oac_all[year_code]['OAC_Subgroup'] = oac_all[year_code]['OAC' + year_end + 'CD']
        oac_all[year_code]['OA_SA'] = oac_all[year_code]['OA' + year_end + 'CD']
    
        # import populations
        oa_populations[year_code] = pd.read_csv(eval("r'" + data_directory + "raw/Geography/Census_Populations/census20" + year_end + "_pop_uk_oa.csv'"))[
                ['OA' + year_end + 'CD', 'population']]
        oa_populations[year_code]['population'] = oa_populations[year_code]['population'].astype(float)   

    ni_pop_01 = pd.read_csv(eval("r'" + data_directory + "raw/Geography/Census_Populations/census2001_pop_northern_ireland_oa.csv'"), header=5)[['Unnamed: 0', 'All persons']]
    ni_pop_01['Unnamed: 0'] = ni_pop_01['Unnamed: 0'].str.replace(' ', '')
    ni_pop_01 = ni_pop_01.loc[(ni_pop_01['Unnamed: 0'].str.len() == len('95ZZ160009')) & 
                              (ni_pop_01['Unnamed: 0'].str[-1].str.isnumeric() == True)]
    ni_pop_01.columns = ['OA01CD', 'population']

    oa_populations['oa_2001'] = oa_populations['oa_2001'].append(ni_pop_01)


    # import mid year populations
    mid_year_pop = pd.read_csv(eval("r'" + data_directory + "raw/Geography/Census_Populations/mid_year_pop.csv'"), header=7); mid_year_pop.columns = ['year', 'population']
    mid_year_pop = mid_year_pop.set_index('year')

    mid_year_pop_combined = mid_year_pop.loc[years_combined]
    
    if len(years_combined) > 1:
        difference = years_combined[1] - years_combined[0]
        for year in years_combined:
            year_list = [year + i for i in range(difference)]
            temp =  mid_year_pop.loc[year, 'population']
            for i in range(1, difference):
                temp += mid_year_pop.loc[year_list[i], 'population']
            mid_year_pop_combined.loc[year, 'population'] = temp / difference
    else:
        for year in years_combined:
             mid_year_pop_combined.loc[year, 'population'] = mid_year_pop.loc[year, 'population']

    for year in years_combined:
        if year < 2014:
            year_code = 'oa_2001'
        else:
            year_code = 'oa_2011'
        year_end = year_code[-2:] 

        # adjust OA populations to mid-year populations
        oa_populations[year_code]['OA_SA'] = oa_populations[year_code]['OA' + year_end + 'CD']
        oac_all[year] = oac_all[year_code].merge(oa_populations[year_code][['OA_SA', 'population']], on='OA_SA', how='left')
        oac_all[year] = oac_all[year][['MSOA' + year_end + 'CD', 'LSOA' + year_end + 'CD', 'OA' + year_end + 'CD',
                                   'GOR_code', 'GOR_name', 'GOR modified', 'OAC_Supergroup', 'OAC_Group', 'OAC_Subgroup', 'OA_SA', 'population']].drop_duplicates()
        oac_all[year]['population'] = ((oac_all[year]['population']/oac_all[year]['population'].sum()) * mid_year_pop_combined.loc[year, 'population'])

    return(oac_all)


# main function to run all above
def estimate_income(geog, first_year, last_year, combine_years, wd, sd_limit):
    hhdspend_lcfs_combined = import_income(first_year, last_year, combine_years, wd)
    hhdspend_lcfs_combined = winsorise(hhdspend_lcfs_combined, sd_limit)
    
    hhdspend_full_index, hhdspend_oac = attach_oac_grouping(hhdspend_lcfs_combined, wd)
    # import OAC data adjusted to mid-year populations
    oac_all = get_oac_census(list(hhdspend_lcfs_combined.keys()), wd)
    OA_exp_detailed = detailed_oac_aggregation(hhdspend_full_index, oac_all, hhdspend_oac)
    # Aggregate to LSOA and MSOA level
    geog_exp_detailed = geog_aggregation(OA_exp_detailed, oac_all, list(OA_exp_detailed.keys()), geog)
    
    return(geog_exp_detailed)


def mean_spend_2013_bounday(exp_by_year, wd):
    
    lookup = pd.read_csv(eval("r'" + wd + "/data/raw/Geography/Conversion_Lookups/UK_full_lookup_2001_to_2011.csv'"))
    lookup_msoa = lookup[['MSOA01CD', 'MSOA11CD']].drop_duplicates()
            
    new_exp_2013 = pd.DataFrame()
    for year in list(exp_by_year.keys()):
        # import ghg and income
        if year > 2013:
            exp_by_year[year] = exp_by_year[year].join(lookup_msoa.set_index('MSOA11CD')).set_index('MSOA01CD').mean(axis=0, level='MSOA01CD')
        exp_by_year[year]['year'] = year
        new_exp_2013 = new_exp_2013.append(exp_by_year[year])
            
    new_exp_2013 = new_exp_2013.mean(axis=0, level='MSOA01CD').drop('year', axis=1)
            
    return(new_exp_2013)

# save expenditure
def save_geog_income(geog, geog_exp_detailed, working_directory):  
    data_directory = working_directory + "/data/"        
    # save expenditure profiles
    pickle.dump(geog_exp_detailed, open(eval("r'" + data_directory + "/processed/LCFS/Income/" + geog + "_income.p'"), 'wb'))
    
    #for year in list(geog_exp_detailed.keys()):
    #    geog_exp_detailed[year].to_csv(eval("r'" + data_directory + "processed/LCFS/lcfsXoac/" + geog + "_expenditure_" + str(year) + '-' + str(year+1) + ".csv'"))