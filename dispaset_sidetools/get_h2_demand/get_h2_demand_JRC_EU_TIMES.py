# -*- coding: utf-8 -*-
"""
This script generates the demand for H2 as an hourly time-series

@author: Eva Joskin
"""

import pandas as pd
import sys,os
sys.path.append(os.path.abspath(r'../..')) 
from dispaset_sidetools.common import make_dir

# %% Adjustable inputs that should be modified
# Scenario definition
WRITE_CSV_FILES = True  # Write csv database
SCENARIO = 'ProRes1'  # Scenario name, used for naming csv files
CASE = 'ALLFLEX'  # Case name, used for naming csv files
SOURCE = 'JRC_EU_TIMES_'  # Source name, used for naming csv files
EFF_DIESEL = 0.78 # Efficiency of hydrogenation to diesel
EFF_METHANOL = 0.82 # Efficiency of hydrogenation to methanol

# %% Inputs
# Folder destinations
input_folder = '../../Inputs/'  # Standard input folder
source_folder = 'JRC_EU_TIMES/'
output_folder = '../../Outputs/'  # Standard output folder
scenario = SCENARIO + '/'

# %% Load data
h2_normal_demand = pd.read_excel(
    input_folder + source_folder + scenario + 'TIMES_H2_Demand_2050.xlsx', 
    header=None, index_col = 0, skiprows = 2)
h2_demand_PtL = pd.read_excel(
    input_folder + source_folder + scenario + 'TIMES_H2_Demand_PtL_2050.xlsx', 
    index_col = 0, skiprows = 1)

# %% Correct H2 demand for PtL (what we have is demand for diesel and methanol, not for H2)
for h in h2_demand_PtL.columns:
    if "Diesel" in h:
        h2_demand_PtL.loc[:,h] = h2_demand_PtL.loc[:,h]/EFF_DIESEL
    elif "Methanol" in h:
        h2_demand_PtL.loc[:,h] = h2_demand_PtL.loc[:,h]/EFF_METHANOL

h2_demand_PtL_final=h2_normal_demand.copy()
for c in h2_demand_PtL.index:
    h2_demand_PtL_final.loc[c]=h2_demand_PtL.loc[c,:].sum() 
    
# %% Total demand for H2
h2_total_demand = h2_normal_demand.copy()
h2_total_demand[:] = h2_normal_demand[:] +  h2_demand_PtL_final[:] 

# %% First solution: create a flat demand over the year
dates = pd.date_range(start='1/1/2050', end='31/12/2050 23:00:00', freq='H')

h2_demand_time_series = pd.DataFrame(0,index=dates, columns = h2_total_demand.index)

for c in h2_total_demand.index:
    h2_demand_time_series.loc[:,c] = h2_total_demand.loc[c].item()/(len(dates)*3.6e-6) # flat demand [MWh]
    
# %% Write csv file:
def write_csv_files(h2_TimeSeries, write_csv=None):
    """
    Function that generates .csv files in the Output/Database/h2_demand/ folder
    :h2_TimeSeries:  DataFrame with H2 demand at each hour for each zone
    """
    if write_csv is True:
        for c in h2_TimeSeries.columns:
            filename = 'H2_Demand'  +'_' + c + '_' + '2050' + '.csv'
            make_dir((output_folder))
            make_dir(output_folder + source_folder + 'Database')
            folder = output_folder + source_folder + 'Database/' + scenario + 'H2_demand/'
            make_dir(folder)
            make_dir(folder + c)
            h2_TimeSeries[c].to_csv(folder + c + '/' + filename)
    else:
        print('[WARNING ]: ' + 'WRITE_CSV_FILES = False, unable to write .csv files')


write_csv_files(h2_demand_time_series, WRITE_CSV_FILES) 
