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
import numpy as np
from matplotlib.patches import Rectangle
import scipy.stats as stats

wd = r'/Users/lenakilian/Documents/Ausbildung/UoLeeds/PhD/Analysis/'

# create lookup for emisisons
ward_shp = gpd.read_file(wd + 'data/processed/Wellbeing/wwellbeing_london_geography.shp')
ward_shp = ward_shp.to_crs(epsg=27700)
ward_shp = ward_shp.dissolve(['ID', 'Ward Code']).drop_duplicates().reset_index()

# import emissions and wellbeing data
keep = ['index', 'RGN11NM', 'population', 'income', 'Car/van pu', 'Other tran', 'Rail', 'Bus', 'Combined f', 'Flights', 'geometry']
variables = ['income', 'Car/van pu', 'Other tran', 'Rail', 'Bus', 'Combined f', 'Flights']

# new with wide format
emissions = gpd.read_file(wd + 'data/processed/GWR_data/gwr_data_london_2015.shp')[keep].drop_duplicates().set_index('index')
emissions = emissions.to_crs(epsg=27700)
pop = emissions['population'].sum()

# Find centroid to match with ward_shp
# Find interesections and add by ward ID
intersection = gpd.overlay(emissions.reset_index(), ward_shp, how='intersection').drop_duplicates()

# weigh by area
msoa_area = intersection.dissolve('index_1').area.reset_index().rename(columns={0:'msoa_area'})
intersection = intersection.merge(msoa_area, on='index_1')
intersection['area'] = intersection.area

intersection['proportion'] = intersection['area'] / intersection['msoa_area']

intersection[variables + ['population']] = intersection[variables + ['population']].apply(lambda x: x * intersection['proportion'])

intersection['population'] = intersection['population'] / intersection['population'].sum() * pop

#check if they match
if emissions['population'].sum() == intersection['population'].sum():
    print('TEST PASSED')
else:
    print(emissions['population'].sum() - intersection['population'].sum())

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

reverse = ['London Rank 2013 (out of 625)',
            'Childhood Obesity 2013', 
            'Incapacity Benefit rate - 2013', 
            'Unemployment rate 2013', 
            'Crime rate - 2013',
            'Deliberate Fires - 2013', 
            'Unauthorised Absence in All Schools (%) - 2013',
            '% dependent children in out-of-work households - 2013']

for item in reverse:
    if item in wellbeing.columns.tolist():
        print(item)
        all_data[item] = -1 * all_data[item]


# correlation
all_vars_em = ['Car/van pu', 'Flights', 'Rail', 'Bus', 'Combined f', 'Total_transport', 'land_transport']
all_vars_wb = cp.copy(wellbeing_keep)

all_vars = all_vars_em + all_vars_wb

corr_vars_dict = dict(zip(all_vars, [
    # transport emissions
    'Car/van purchases\nand motoing oils', 'Flights', 'Rail', 'Bus', 
    'Combined fares', 'Total transport', 'Land transport', 
    # wellbeing
    'London Rank 2013 (reversed)', 
    'Wellbeing Index\nScore 2013', 
    'Life Expectancy\n2009-13',
    'Childhood Obesity\n2013 (reversed)', 
    'Incapacity Benefit\nrate 2013 (reversed)',
    'Unemployment rate\n2013 (reversed)', 
    'Crime rate 2013\n(reversed)',
    'Deliberate Fires\n2013 (reversed)', 
    'GCSE point scores\n2013 (reversed)',
    'Unauthorised Absence\nin All Schools\n(%) 2013 (reversed)',
    'Dependent children\nin out-of-work\nhouseholds (%)\n2013 (reversed)',
    'Public Transport\nAccessibility 2013',
    'Homes with access\nto open space, nature,\nand greenspace\n(%) 2013 (reversed)',
    'Subjective well-\nbeing average\nscore, 2013']))


corr_vars_em = ['Car/van pu', 'Flights', 'Rail', 'Bus', 'Combined f', 'Total_transport', 'land_transport'] #
corr_vars_wb = ['Index Score 2013', 'Life Expectancy 2009-13', 'Unemployment rate 2013', '% dependent children in out-of-work households - 2013', 
                'Homes with access to open space & nature, and % greenspace - 2013', 'Subjective well-being average score, 2013']

corr_vars = corr_vars_em + corr_vars_wb


corr = all_data[corr_vars].corr(method='pearson')

# P-values
def pearsonr_pval(x,y):
    return pearsonr(x,y)[1]
    
corr_p = all_data[corr_vars].corr(method=pearsonr_pval)

corr_p2 = all_data[corr_vars].corr(method=pearsonr_pval)
for item in corr_p.columns:
    corr_p2.loc[corr_p[item] >= 0.05, item] = '  '
    corr_p2.loc[(corr_p[item] < 0.05) & (corr_p[item] >= 0.01), item] = '* '
    corr_p2.loc[corr_p[item] < 0.01, item] = "**"
    
for item in corr_p.columns:
    corr_p.loc[corr_p[item] >= 0.05, item] = 1
    corr_p.loc[(corr_p[item] < 0.05) & (corr_p[item] >= 0.01), item] = 0.05
    corr_p.loc[corr_p[item] < 0.01, item] = 0.01
    

corr_summary = cp.copy(corr)
for item in corr_summary.columns:
    corr_summary[item] = [str(np.round(corr_summary[item][x], 2)) + ' ' + corr_p2[item][x] for x in range(len(corr_summary[item]))]



#########
# COUNT #
#########

count = all_data[['Ward Code', 'population', 'Car/van pu', 'Bus', 'Combined f', 'land_transport', 'Index Score 2013', 'Subjective well-being average score, 2013']].reset_index()
count_w = pd.DataFrame(columns=count.columns)
for i in range(len(count)):
    for j in range(int(count['population'][i] * 1)):
        count_w = count_w.append(count.iloc[i,:])
        print(len(count_w))

q = count_w.loc[:, 'Car/van pu':'Subjective well-being average score, 2013'].stack().reset_index().groupby('level_1').quantile([0.25, 0.5, 0.75])[[0]]\
    .unstack(level=1).droplevel(axis=1, level=0)

# plot
for item in ['Car/van pu', 'Bus', 'Combined f', 'land_transport', 'Index Score 2013', 'Subjective well-being average score, 2013']:
    n = int(round(len(count_w) / 4))
    k = ['Q1'] * n + ['Q2'] * n + ['Q3'] * n + ['Q4'] * n
    if len(count_w) > len(k):
        for i in len(count_w) - len(k):
            k += ['Q4']
    else:
        k = k[:len(count_w)]
    count_w = count_w.sort_values(item, ascending=True)
    count_w[item + '_Group'] = k

temp = count_w.loc[:, 'Car/van pu_Group':]
temp['count'] = 1

count_results = pd.DataFrame()
for w in ['Index Score 2013_Group', 'Subjective well-being average score, 2013_Group']:
    temp_results = pd.DataFrame()
    for e in ['Car/van pu_Group', 'Bus_Group', 'Combined f_Group', 'land_transport_Group']:
        count_final = temp.groupby([e, w]).count()[['count']].unstack().rename(columns={'count':w})
        count_final = count_final.apply(lambda x: x/count_final.sum().sum() * 100)
        count_final.index = pd.MultiIndex.from_arrays([[e] * 4, count_final.index])
        count_final.index.names = ['Transport', 'Group']
        temp_results = temp_results.append(count_final)
    if w == 'Index Score 2013_Group':
        count_results = cp.copy(temp_results)
    else:
        count_results = count_results.join(temp_results)
      

###############
# SCATTERPLOT #
###############

wellbeing = ['Index Score 2013', 'Subjective well-being average score, 2013']
transport = ['Car/van purchases and motoring oils', 'Land Transport', 'All transport'] #'Total_transport', 'Car/van pu', 'Other tran', 'Rail', 'Bus', 'Combined f', 'Flights'

temp = all_data.rename(columns={'Car/van pu':'Car/van purchases and motoring oils',
                                'Total_transport':'All transport',
                                'land_transport':'Land Transport'})

temp_corr = temp.corr()

for j in range(len(wellbeing)):
    fig, axs = plt.subplots(ncols=len(transport), nrows=1, 
                            figsize=(10*len(transport), 10), sharey=True)  
    y = wellbeing[j]
    for i in range(len(transport)):
         x=transport[i]
         
         axs[i].add_patch(Rectangle(xy=(temp[x].min(), temp[y].median()), 
                                    height=temp[y].max() - temp[y].median(), 
                                    width=temp[x].median()-temp[x].min(),
                                    fc='none', ec='#C54A43', linewidth = 3.5))
         sns.scatterplot(ax=axs[i], data=temp, x=x, y=y, color='gray')
         axs[i].set_title(x); 
         axs[i].set_ylabel(y); axs[i].set_xlabel('tCO$_{2}$e / capita')
         
         if y == 'Index Score 2013':
             pos_y = 15
         else:
             pos_y = 8.4
             
         temp2 = temp[[x, y]].dropna(how='any')
         r = stats.spearmanr(temp2[x], temp2[y])
         sig = ''
         if r[1] < 0.05:
             sig = '*'
         if r[1] < 0.01:
             sig = '**'
         len_x = (temp[x].max() - temp[x].min()) *0.3 + temp[x].min()
         axs[i].text(len_x, temp[y].min(), "Spearman Rho = " + str(round(r[0], 2)) + sig)
         print(y, x)
    
    plt.savefig(wd + 'Spatial_Emissions/outputs/Graphs/Wellbeing/Scatter/' + y.replace('/', '') + '_spearman.png', 
                bbox_inches='tight', dpi=300)
    
temp = temp[wellbeing + transport]
for item in wellbeing + transport:
    temp[item + '_m'] = 'median or above'
    temp.loc[temp[item] < temp[item].median(), item + '_m'] = 'below_median'
    temp[item] = temp[item + '_m']
temp = temp[wellbeing + transport]

wellbeing_results = pd.DataFrame(columns=['wellbeing_type', 'transport_type'])
for w in wellbeing:
    for t in transport:
        temp2 = temp.groupby([w, t]).count().iloc[:,:1].reset_index()
        temp2.columns = ['wellbeing', 'transport', 'count']
        temp2['transport_type'] = t
        temp2['wellbeing_type'] = w
        temp2['sum_all'] = temp2['count'].sum()
        wellbeing_results = wellbeing_results.append(temp2)
  
wellbeing_results['percent'] = wellbeing_results['count'] / wellbeing_results['sum_all'] * 100
        
font_size = 18
temp = all_data.rename(columns={'Car/van pu':'Car/van purchases and motoring oils', 'Combined f':'Combined Fares', 
                                'population':'Population (1,000)'})
corr_summary = corr_summary.rename(columns={'Car/van pu':'Car/van purchases and motoring oils', 'Combined f':'Combined Fares'})
for y in ['Index Score 2013', 'Subjective well-being average score, 2013']:
    for x in ['Car/van purchases and motoring oils', 'Bus', 'Combined Fares']:
        plt.rcParams.update({'font.family':'Times New Roman', 'font.size':font_size, 
                             'axes.labelsize':font_size, 'axes.titlesize':font_size})
        fig, ax = plt.subplots(figsize=(5, 5))
        sns.scatterplot(ax=ax, data=temp, x=x, y=y, hue='Population (1,000)', palette='Blues', edgecolor='black', legend=False)
        if y == 'Index Score 2013':
            pos_y = 15
        else:
            pos_y = 8.35
        ax.text(temp[x].min(), pos_y, "Pearson's r = " + corr_summary.loc[y, x])
        ax.set_xlabel(''), ax.set_ylabel('')
        
        plt.savefig(wd + 'Spatial_Emissions/outputs/Graphs/Wellbeing/Scatter/Colplot_' + y.replace('/', '') + '_' + x.replace('/', '') + '.png', 
                dpi=300, bbox_inches='tight')
        
plt.rcParams.update({'font.family':'Times New Roman', 'font.size':font_size, 
                             'axes.labelsize':font_size, 'axes.titlesize':font_size})
fig, ax = plt.subplots(figsize=(5, 5))
sns.scatterplot(ax=ax, data=temp, x=x, y=y, hue='Population (1,000)', palette='Blues', edgecolor='black')
ax.legend(loc='center left', title='Population (1,000)', bbox_to_anchor=(1, 0.5), ncol=1)
plt.savefig(wd + 'Spatial_Emissions/outputs/Graphs/Wellbeing/Scatter/Colplot_legend.png', 
                dpi=300, bbox_inches='tight')


########
# MAPS #
########

# Categorise
cats = all_data.drop(['Borough na', 'Ward Code', 'Ward name', 'geometry'], axis=1).T
cats['Median'] = cats.median(1)
#cats.loc['Index Score 2013', 'Median'] = 0
cats = cats.iloc[:, :-1].apply(lambda x: x > cats['Median']).T
for item in cats.columns:
    cats.loc[cats[item] == True, item] = 'High'
    cats.loc[cats[item] == False, item] = 'Low'
    

ward = ward_shp.set_index('ID')[['geometry']].drop_duplicates().join(cats.dropna(how='all'), how='inner').dropna(how='any')


#colours = ['#CD7D7B', '#76A7CB', 'lightgrey']
#my_cols = ListedColormap(['#CD7D7B', '#76A7CB', 'lightgrey'])

# for x in ['Total_transport', 'land_transport', 'Car/van pu', 'Flights']: #, 'Car/van pu', 'Other tran', 'Rail', 'Bus', 'Combined f', 'Flights']:
#     for y in ['Index Score 2013', 'Life Expectancy 2009-13', 'Subjective well-being average score, 2013']: #wellbeing_keep[:2] + 
#         ward['temp'] = ward[x] + ' emissions - ' + ward[y] + ' wellbeing' 
#         ward.loc[ward[x] == ward[y], 'temp'] = 'Other'
#         ward.plot(column='temp', legend=True, cmap=my_cols)
#         plt.title(x + ' - ' + y)
#         plt.show()


colours = ['#B75248', '#E8B798', '#1C356A', '#74A3CC']
my_cols = ListedColormap(colours)

plot_data = cats[corr_vars_em].stack().reset_index(level=1).rename(columns={'level_1':'Emissions', 0:'Emissions_Score'})
plot_data = plot_data.join(cats[corr_vars_wb].stack().reset_index(level=1).rename(columns={'level_1':'Wellbeing', 0:'Wellbeing_Score'}))
plot_data['Category'] = plot_data['Emissions_Score'] + ' emissions - ' + plot_data['Wellbeing_Score'] + ' wellbeing' 
#plot_data.loc[plot_data['Emissions_Score'] == plot_data['Wellbeing_Score'], 'Category'] = 'Other'
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
for k in range(len(colours)):
    legend_elements = [Line2D([k], [k], label=plot_data[['Category']].drop_duplicates()['Category'].tolist()[k], 
                                   markerfacecolor=colours[k], marker='o', color='w',  markersize=4*font_size)]
    axs[r-1, int((c+1)/2)+k-3].legend(handles=legend_elements, loc='lower left', frameon=False,
                                      bbox_to_anchor=((k-1)*(font_size*0.1), -size*0.1))

plt.savefig(wd + 'Spatial_Emissions/outputs/Graphs/Wellbeing_Emission_Maps.png', bbox_inches='tight', dpi=300)


# individual pictures
for i in range(r):
    for j in range(c):
        fig, ax = plt.subplots(figsize=(5, 5))
        if rows == 'em':
            wb = corr_vars_wb[j].replace('/', '')
            em = corr_vars_em[i].replace('/', '')
        else:
            wb = corr_vars_wb[i].replace('/', '')
            em = corr_vars_em[j].replace('/', '')
        temp = plot_data.loc[(plot_data['Emissions'] == em) & (plot_data['Wellbeing'] == wb)]
        temp.plot(ax=ax, column='Category', cmap=my_cols)
        #hide axes
        plt.axis('off')
        plt.savefig(wd + 'Spatial_Emissions/outputs/Graphs/Wellbeing/Maps/' + em + '_' + wb + '.png', dpi=300,
                    bbox_inches='tight', pad_inches=-0.1)
        
        
 

# individual pictures
carvan_data = plot_data.loc[(plot_data['Emissions'] == 'Car/van pu')].drop_duplicates()

# individual pictures
for wb in corr_vars_wb:
    fig, ax = plt.subplots(figsize=(5, 5))
    temp = carvan_data.loc[(carvan_data['Wellbeing'] == wb)]
    temp.plot(ax=ax, column='Category', cmap=my_cols)
    #hide axes
    plt.axis('off')
    plt.savefig(wd + 'Spatial_Emissions/outputs/Graphs/Wellbeing/Maps/Carvan pu_' + wb + '.png', dpi=300,
                bbox_inches='tight', pad_inches=-0.1)
        
        

