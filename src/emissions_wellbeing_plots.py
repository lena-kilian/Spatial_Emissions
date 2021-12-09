#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Dec  3 14:08:41 2021

@author: lenakilian
"""
import pandas as pd
import geopandas as gpd
import libpysal
import pysal
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.lines import Line2D
import seaborn as sns
import copy as cp
from scipy.stats import pearsonr

wd = r'/Users/lenakilian/Documents/Ausbildung/UoLeeds/PhD/Analysis/'

# create lookup for emisisons
ward_shp = gpd.read_file(wd + 'data/processed/Wellbeing/wwellbeing_london_geography.shp')
ward_shp = ward_shp.to_crs(epsg=27700)
ward_shp['area_ward'] = ward_shp.area

# import emissions and wellbeing data
keep = ['index', 'RGN11NM', 'population', 'income', 'Car/van pu', 'Other tran', 'Rail', 'Bus', 'Combined f', 'Flights', 'geometry']
variables = ['income', 'Car/van pu', 'Other tran', 'Rail', 'Bus', 'Combined f', 'Flights']

# new with wide format
emissions = gpd.read_file(wd + 'data/processed/GWR_data/gwr_data_london_2015.shp')[keep].set_index('index')
emissions = emissions.to_crs(epsg=27700)
# Find centroid to match with ward_shp
# Find interesections and add by ward ID
intersection = gpd.overlay(emissions, ward_shp, how='intersection')
# weigh by area
intersection['area'] = intersection.area
intersection['proportion'] = intersection['area'] / intersection['area_ward']
intersection[variables + ['population']] = intersection[variables + ['population']].apply(lambda x: x * intersection['proportion'])
# add by ward ID
emissions = intersection.groupby('ID').sum()
emissions[variables] = emissions[variables].apply(lambda x: x / emissions['population'])
emissions = ward_shp.set_index('ID').join(emissions[variables + ['population']])
# Add total transport
emissions['Total_transport'] = emissions[['Car/van pu', 'Other tran', 'Rail', 'Bus', 'Combined f', 'Flights']].sum(1)
emissions['land_transport'] = emissions[['Car/van pu', 'Other tran', 'Rail', 'Bus', 'Combined f']].sum(1)

# import wellbeing
wellbeing = pd.read_excel(wd + 'data/raw/Wellbeing/london-ward-well-being-probability-scores.xlsx', 
                          sheet_name='Data').dropna(how='all').set_index('New ward code')
wellbeing = ward_shp.set_index('Ward Code')[['ID', 'Borough na', 'Ward name', 'geometry']].join(wellbeing, how='left')

temp = pd.read_excel(wd + 'data/raw/Wellbeing/london-ward-well-being-probability-scores.xlsx', 
                          sheet_name='Ranked', header = 3).loc[:, :'Borough'].dropna(how='all')

# COMBINE AND FIX
wellbeing_keep = ['London Rank 2013 (out of 625)', 'Index Score 2013', 
        'Life Expectancy 2009-13',
       'Childhood Obesity 2013', 
       'Incapacity Benefit rate - 2013',
       'Unemployment rate 2013', 
       'Crime rate - 2013',
       'Deliberate Fires - 2013', 'GCSE point scores - 2013',
       'Unauthorised Absence in All Schools (%) - 2013',
       '% dependent children in out-of-work households - 2013',
       'Public Transport Accessibility - 2013',
       'Homes with access to open space & nature, and % greenspace - 2013',
       'Subjective well-being average score, 2013']

wellbeing = wellbeing.merge(temp, on=['Ward', 'Borough'], how='left')[wellbeing_keep + ['geometry', 'ID']]

# Merge datasets
all_data = emissions.join(wellbeing.set_index('ID')[wellbeing_keep].dropna(how='all'), how='inner').drop('index', axis=1).drop_duplicates()

# reverse = ['London Rank 2013 (out of 625)',
#            'Childhood Obesity 2013', 
#            'Incapacity Benefit rate - 2013', 
#            'Unemployment rate 2013', 
#            'Crime rate - 2013',
#            'Deliberate Fires - 2013', 
#            'Unauthorised Absence in All Schools (%) - 2013',
#            '% dependent children in out-of-work households - 2013']

# for item in reverse:
#     if item in wellbeing.columns.tolist():
#         print(item)
#         wellbeing[item] = -1 * wellbeing[item]


# correlation
corr_vars_em = ['Car/van pu', 'Flights', 'Rail', 'Bus', 'Combined f', 'Total_transport', 'land_transport']
corr_vars_wb = ['Index Score 2013', 'Life Expectancy 2009-13', 'Subjective well-being average score, 2013']

corr_vars = corr_vars_em + corr_vars_wb

corr_vars_dict = dict(zip(corr_vars, ['Car/van purchases \n and motoing oils', 'Flights', 'Rail', 'Bus', 
                                      'Combined fares', 'Total transport', 'Land transport', 
                                      'Index Score 2013', 'Life Expectancy \n 2009-13', 
                                      'Subjective well-being \n average score, 2013']))


corr = all_data[corr_vars].corr(method='pearson').loc[:'land_transport', 'Index Score 2013':]

# P-values
def pearsonr_pval(x,y):
    return pearsonr(x,y)[1]
    
corr_p = all_data[corr_vars].corr(method=pearsonr_pval).loc[:'land_transport', 'Index Score 2013':]
    
for item in corr_p.columns:
    corr_p.loc[corr_p[item] >= 0.05, item] = 1
    corr_p.loc[(corr_p[item] < 0.05) & (corr_p[item] >= 0.01), item] = 0.05
    corr_p.loc[corr_p[item] < 0.01, item] = 0.01


# plot

# for x in ['Total_transport', 'Car/van pu', 'Other tran', 'Rail', 'Bus', 'Combined f', 'Flights']:
#     for y in wellbeing_keep[:2]:
#         plt.scatter(all_data[x], all_data[y])
#         plt.xlabel(x), plt.ylabel(y)
#         plt.axvline(all_data[x].median(), c='r'); plt.axhline(all_data[y].median(), c='r')
#         plt.show()


# Categorise
cats = all_data.drop(['Borough na', 'Ward Code', 'Ward name', 'geometry'], axis=1).T
cats['Median'] = cats.median(1)
cats = cats.iloc[:, :-1].apply(lambda x: x > cats['Median']).T
for item in cats.columns:
    cats.loc[cats[item] == True, item] = 'High'
    cats.loc[cats[item] == False, item] = 'Low'
    

ward = ward_shp.set_index('ID')[['geometry']].drop_duplicates().join(cats.dropna(how='all'), how='inner').dropna(how='any')


colours = ['#CD7D7B', '#76A7CB', 'lightgrey']
my_cols = ListedColormap(['#CD7D7B', '#76A7CB', 'lightgrey'])

# for x in ['Total_transport', 'land_transport', 'Car/van pu', 'Flights']: #, 'Car/van pu', 'Other tran', 'Rail', 'Bus', 'Combined f', 'Flights']:
#     for y in ['Index Score 2013', 'Life Expectancy 2009-13', 'Subjective well-being average score, 2013']: #wellbeing_keep[:2] + 
#         ward['temp'] = ward[x] + ' emissions - ' + ward[y] + ' wellbeing' 
#         ward.loc[ward[x] == ward[y], 'temp'] = 'Other'
#         ward.plot(column='temp', legend=True, cmap=my_cols)
#         plt.title(x + ' - ' + y)
#         plt.show()


plot_data = cats[corr_vars_em].stack().reset_index(level=1).rename(columns={'level_1':'Emissions', 0:'Emissions_Score'})
plot_data = plot_data.join(cats[corr_vars_wb].stack().reset_index(level=1).rename(columns={'level_1':'Wellbeing', 0:'Wellbeing_Score'}))
plot_data['Category'] = plot_data['Emissions_Score'] + ' emissions - ' + plot_data['Wellbeing_Score'] + ' wellbeing' 
plot_data.loc[plot_data['Emissions_Score'] == plot_data['Wellbeing_Score'], 'Category'] = 'Other'
plot_data = ward_shp.set_index('ID')[['geometry']].drop_duplicates().join(plot_data).sort_values('Category')


#cols = 'wb'; rows = 'em'
cols = 'em'; rows = 'wb'; size = 5; font_size = 6.8
c = eval('len(corr_vars_' + cols + ')'); r = eval('len(corr_vars_' + rows + ')')

# set plots in script to TNR font
plt.rcParams.update({'font.family':'Times New Roman', 'font.size':size*font_size, 
                     'axes.labelsize':size*font_size, 'axes.titlesize':size*font_size})

fig, axs = plt.subplots(ncols=c, nrows=r, figsize=(1.25 * size *c, size*r))
for i in range(r):
    for j in range(c):
        if rows == 'em':
            wb = corr_vars_wb[j]
            em = corr_vars_em[i]
            title = corr_vars_dict[wb]; yax = corr_vars_dict[em]
        else:
            wb = corr_vars_wb[i]
            em = corr_vars_em[j]
            title = corr_vars_dict[em]; yax = corr_vars_dict[wb]
        temp = plot_data.loc[(plot_data['Emissions'] == em) & (plot_data['Wellbeing'] == wb)]
        temp.plot(ax=axs[i, j], column='Category', cmap=my_cols)
        axs[i, j].get_xaxis().set_visible(False); axs[i, j].set_yticks([]) 
        axs[i, j].spines['top'].set_visible(False); axs[i, j].spines['bottom'].set_visible(False)
        axs[i, j].spines['right'].set_visible(False); axs[i, j].spines['left'].set_visible(False)
        if i == 0:
            axs[i, j].set_title(title)
        if j == 0:
            axs[i, j].set_ylabel(yax)
# make custom legend
for k in range(3):
    legend_elements = [Line2D([k], [k], label=plot_data[['Category']].drop_duplicates()['Category'].tolist()[k], 
                                   markerfacecolor=colours[k], marker='o', color='w',  markersize=4*font_size)]
    axs[r-1, int((c+1)/2)+k-2].legend(handles=legend_elements, loc='lower left', frameon=False,
                                      bbox_to_anchor=((k-1)*(font_size*0.1), -size*0.1))

plt.savefig(wd + 'Spatial_Emissions/outputs/Graphs/Wellbeing_Emission_Maps.png', bbox_inches='tight', dpi=200)


