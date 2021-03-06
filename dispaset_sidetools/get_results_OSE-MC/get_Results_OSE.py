# -*- coding: utf-8 -*-
"""
Created on Wed Sep  4 11:14:36 2019

@author: matij
"""


# System imports
from __future__ import division
import matplotlib.pyplot as plt
import pandas as pd
pd.options.mode.chained_assignment = None
import numpy as np
import dispaset as ds
import os
import sys
import pickle
# Third-party imports
# Local source tree imports
from dispaset_sidetools.common import mapping,outliers_vre,fix_na,make_dir,entsoe_types,commons

#%% Adjustable inputs that should be modified
YEAR = 2030                     # considered year
WRITE_CSV_FILES = True         # Write csv database
TECHNOLOGY_THRESHOLD = 0   # threshold (%) below which a technology is considered negligible and no unit is created
TES_CAPACITY = 0               # No of storage hours in TES
CHP_TYPE = None         # Define CHP type: None, back-pressure or Extraction

input_folder = '../../Inputs/OSE_MC_Results/'  # Standard input folder
output_folder = '../../Outputs/'# Standard output folder

# model = 'CALLIOPE'                    # Chose one of 6 models
# model = 'DIETER'
# model = 'dynELMOD'
# model = 'EMMA'
model = 'URBS'
# model = 'PLEXOS'
# model = 'MIN'

# scenario = 'Baseline battery costs'     # Chose one of 3 scenarios
# scenario = '50percent battery costs'
scenario = '25percent battery costs'

# coverage = 'Full geographic coverage'   # Chose germany only or full geographic coverage
coverage = 'Germany only'

model_db = ['CALLIOPE','DIETER','dynELMOD','EMMA','URBS','PLEXOS','MIN','MEAN','MEDIAN','MAX']
scenario_db = ['Baseline battery costs','50percent battery costs','25percent battery costs']
coverage_db = ['Full geographic coverage','Germany only']

# data = pd.read_excel('../../Inputs/' + 'results_190701.xlsx','raw_all')
# variables = list(data['Variable'].unique())

def get_OSE_MC(model,scenario,coverage):
    
    if scenario == 'Baseline battery costs':
        scenario_folder = '_Baseline battery costs'
    elif scenario == '50percent battery costs':
        scenario_folder = '_50percent battery costs'
    elif scenario == '25percent battery costs':
        scenario_folder = '_25percent battery costs'
    
    if coverage == 'Full geographic coverage':
        coverage_folder = '_Full_geographic_coverage'
    elif coverage == 'Germany only':
        coverage_folder = '_Germany_only'
    
    path = input_folder + 'simulation_OSE_' + model + scenario_folder + coverage_folder
    if os.path.isdir(path) == False:
        print('Path: ' + path + ' does not exist')
    else:
        inputs,results = ds.get_sim_results(path=path,cache=False)
        ppt = ds.get_indicators_powerplant(inputs,results)
        ppt.reset_index(inplace=True)

        ## Get caoacities
        def capacity_df(df):
            df.loc[(df['Fuel'] == 'HRD') & (df['Technology'] == 'STUR'),'Variable'] = 'Capacity|Electricity|Hard coal'
            df.loc[(df['Fuel'] == 'NUC') & (df['Technology'] == 'STUR'),'Variable'] = 'Capacity|Electricity|Nuclear'
            df.loc[(df['Fuel'] == 'LIG') & (df['Technology'] == 'STUR'),'Variable'] = 'Capacity|Electricity|Lignite'
            df.loc[(df['Fuel'] == 'OIL') & (df['Technology'] == 'STUR'),'Variable'] = 'Capacity|Electricity|Oil'
            df.loc[(df['Fuel'] == 'BIO') & (df['Technology'] == 'STUR'),'Variable'] = 'Capacity|Electricity|Bioenergy'
            df.loc[(df['Fuel'] == 'OTH') & (df['Technology'] == 'STUR'),'Variable'] = 'Capacity|Electricity|Other nonrenewable'
            df.loc[(df['Fuel'] == 'GAS') & (df['Technology'] == 'GTUR'),'Variable'] = 'Capacity|Electricity|Gas OCGT'
            df.loc[(df['Fuel'] == 'GAS') & (df['Technology'] == 'COMC'),'Variable'] = 'Capacity|Electricity|Gas CCGT'
            df.loc[(df['Fuel'] == 'WST') & (df['Technology'] == 'STUR'),'Variable'] = 'Capacity|Electricity|Other renewable'
            df.loc[(df['Fuel'] == 'WIN') & (df['Technology'] == 'WTON'),'Variable'] = 'Capacity|Electricity|Wind Onshore'
            df.loc[(df['Fuel'] == 'WIN') & (df['Technology'] == 'WTOF'),'Variable'] = 'Capacity|Electricity|Wind Offshore'
            df.loc[(df['Fuel'] == 'SUN') & (df['Technology'] == 'PHOT'),'Variable'] = 'Capacity|Electricity|Solar PV'
            df.loc[(df['Fuel'] == 'WAT') & (df['Technology'] == 'HROR'),'Variable'] = 'Capacity|Electricity|Hydro ROR'
            df.loc[(df['Fuel'] == 'WAT') & (df['Technology'] == 'HPHS'),'Variable'] = 'Capacity|Electricity|Storage|Pumped hydro|Power'
            df.loc[(df['Fuel'] == 'WAT') & (df['Technology'] == 'HDAM'),'Variable'] = 'Capacity|Electricity|Hydro Reservoir'
            df.loc[(df['Fuel'] == 'OTH') & (df['Technology'] == 'BATS'),'Variable'] = 'Capacity|Electricity|Storage|Liion|Power'
            df['Value'] = df['Nunits'] * df['PowerCapacity'] / 1e3
            # Total capacity
            df_total = df.groupby(['Variable'])['Value'].sum().reset_index()
            df_total.reset_index(inplace=True)
            df_total.rename(columns={'index': 'Zone'}, inplace=True)
            df_total['Zone'] = 'Whole Region'
            df = df.append(df_total, ignore_index=True, sort=True)
            df['Unit'] = 'GW'
            df = df[['Zone','Variable','Unit','Value']]
            return df
        df_capacity = capacity_df(ppt)
        
        ## Get generation, shedding,emmisions and curtailment
        def generation_df(df,results,inputs):
            df.set_index('index', inplace=True)
            df['CO2'] = df['Generation'] / inputs['units']['Efficiency'] * inputs['units']['EmissionRate']
            co2_zone = df.groupby(['Zone'])['CO2'].sum().reset_index()
            co2_zone.reset_index(inplace=True)
            co2_zone['Variable'] = 'Carbon emissions'
            co2_zone['Unit'] = 't_CO2'
            co2_zone.rename(columns={'CO2': 'Value'}, inplace=True)
            # df.groupby(['Fruit', 'Name'])['Number'].sum().reset_index()
        # CO2 Emissions
            co2 = {'Value': [df['CO2'].sum()]}
            co2 = pd.DataFrame(co2)
            co2.reset_index(inplace=True)
            co2['Variable'] = 'Carbon emissions'
            co2['Unit'] = 't_CO2'
            co2['Zone'] = 'Whole Region'


            df.loc[(df['Fuel'] == 'HRD') & (df['Technology'] == 'STUR'),'Variable'] = 'Energy|Electricity|Hard coal'
            df.loc[(df['Fuel'] == 'NUC') & (df['Technology'] == 'STUR'),'Variable'] = 'Energy|Electricity|Nuclear'
            df.loc[(df['Fuel'] == 'LIG') & (df['Technology'] == 'STUR'),'Variable'] = 'Energy|Electricity|Lignite'
            df.loc[(df['Fuel'] == 'OIL') & (df['Technology'] == 'STUR'),'Variable'] = 'Energy|Electricity|Oil'
            df.loc[(df['Fuel'] == 'BIO') & (df['Technology'] == 'STUR'),'Variable'] = 'Energy|Electricity|Bioenergy'
            df.loc[(df['Fuel'] == 'OTH') & (df['Technology'] == 'STUR'),'Variable'] = 'Energy|Electricity|Other nonrenewable'
            df.loc[(df['Fuel'] == 'GAS') & (df['Technology'] == 'GTUR'),'Variable'] = 'Energy|Electricity|Gas OCGT'
            df.loc[(df['Fuel'] == 'GAS') & (df['Technology'] == 'COMC'),'Variable'] = 'Energy|Electricity|Gas CCGT'
            df.loc[(df['Fuel'] == 'WST') & (df['Technology'] == 'STUR'),'Variable'] = 'Energy|Electricity|Other renewable'
            df.loc[(df['Fuel'] == 'WIN') & (df['Technology'] == 'WTON'),'Variable'] = 'Energy|Electricity|Wind Onshore'
            df.loc[(df['Fuel'] == 'WIN') & (df['Technology'] == 'WTOF'),'Variable'] = 'Energy|Electricity|Wind Offshore'
            df.loc[(df['Fuel'] == 'SUN') & (df['Technology'] == 'PHOT'),'Variable'] = 'Energy|Electricity|Solar PV'
            df.loc[(df['Fuel'] == 'WAT') & (df['Technology'] == 'HROR'),'Variable'] = 'Energy|Electricity|Hydro ROR'
            df.loc[(df['Fuel'] == 'WAT') & (df['Technology'] == 'HPHS'),'Variable'] = 'Energy|Electricity|Storage|Pumped hydro|Power'
            df.loc[(df['Fuel'] == 'WAT') & (df['Technology'] == 'HDAM'),'Variable'] = 'Energy|Electricity|Hydro Reservoir'
            df.loc[(df['Fuel'] == 'OTH') & (df['Technology'] == 'BATS'),'Variable'] = 'Energy|Electricity|Storage|Liion|Power'
            df['Value'] = df['Generation'] / 1e6
        # Curtailment
            tmp_df = pd.DataFrame(results['OutputCurtailedPower'].sum() / 1e6)
            tmp_df.reset_index(inplace=True)
            tmp_df.rename(columns={'index':'Zone', 0:'Value'}, inplace=True)
            tmp_df['Variable'] = 'Energy|Electricity|Renewable curtailment|Absolute'
            df = df.append(tmp_df, ignore_index=True, sort = True)
        # Total generation
            df_total = df.groupby(['Variable'])['Value'].sum().reset_index()
            df_total.reset_index(inplace=True)
            df_total.rename(columns={'index': 'Zone'}, inplace=True)
            df_total['Zone'] = 'Whole Region'
            df = df.append(df_total, ignore_index=True, sort = True)
        # Shedding
            tmp_df = pd.DataFrame(results['OutputShedLoad'].sum() / 1e6)
            tmp_df.reset_index(inplace=True)
            tmp_df.rename(columns={'index':'Zone', 0:'Value'}, inplace=True)
            tmp_df['Variable'] = 'Energy|Electricity|Load Shedding'
            df = df.append(tmp_df, ignore_index=True, sort = True)
            df['Unit'] = 'TWh'
            df = df[['Zone','Variable','Unit','Value']]
        # Reserves
            # LL_2D
            lost_load_2D = pd.DataFrame(results['LostLoad_2D'].sum() / 1e6)
            lost_load_2D.reset_index(inplace=True)
            lost_load_2D.rename(columns={'index':'Zone', 0:'Value'}, inplace=True)
            lost_load_2D['Variable'] = 'Energy|Electricity|Lost Load 2D'
            lost_load_2D['Unit'] = 'TWh'
            df = df.append(lost_load_2D, ignore_index=True, sort = True)
            df = df[['Zone','Variable','Unit','Value']]
            # LL_2U
            lost_load_2U = pd.DataFrame(results['LostLoad_2U'].sum() / 1e6)
            lost_load_2U.reset_index(inplace=True)
            lost_load_2U.rename(columns={'index':'Zone', 0:'Value'}, inplace=True)
            lost_load_2U['Variable'] = 'Energy|Electricity|Lost Load 2U'
            lost_load_2U['Unit'] = 'TWh'
            df = df.append(lost_load_2U, ignore_index=True, sort = True)
            df = df[['Zone','Variable','Unit','Value']]
            # LL_3U
            lost_load_3U = pd.DataFrame(results['LostLoad_3U'].sum() / 1e6)
            lost_load_3U.reset_index(inplace=True)
            lost_load_3U.rename(columns={'index':'Zone', 0:'Value'}, inplace=True)
            lost_load_3U['Variable'] = 'Energy|Electricity|Lost Load 3U'
            lost_load_3U['Unit'] = 'TWh'
            df = df.append(lost_load_3U, ignore_index=True, sort = True)
            df = df[['Zone','Variable','Unit','Value']]
            # LL_Max_Power
            lost_load_max_power = pd.DataFrame(results['LostLoad_MaxPower'].sum() / 1e6)
            lost_load_max_power.reset_index(inplace=True)
            lost_load_max_power.rename(columns={'index':'Zone', 0:'Value'}, inplace=True)
            lost_load_max_power['Variable'] = 'Energy|Electricity|Lost Load Max Power'
            lost_load_max_power['Unit'] = 'TWh'
            df = df.append(lost_load_max_power, ignore_index=True, sort = True)
            df = df[['Zone','Variable','Unit','Value']]
            # LL_Min_Power
            lost_load_min_power = pd.DataFrame(results['LostLoad_MinPower'].sum() / 1e6)
            lost_load_min_power.reset_index(inplace=True)
            lost_load_min_power.rename(columns={'index':'Zone', 0:'Value'}, inplace=True)
            lost_load_min_power['Variable'] = 'Energy|Electricity|Lost Load Min Power'
            lost_load_min_power['Unit'] = 'TWh'
            df = df.append(lost_load_min_power, ignore_index=True, sort = True)
            df = df[['Zone','Variable','Unit','Value']]
            # LL_Ramp_Down
            lost_load_ramp_down = pd.DataFrame(results['LostLoad_RampDown'].sum() / 1e6)
            lost_load_ramp_down.reset_index(inplace=True)
            lost_load_ramp_down.rename(columns={'index':'Zone', 0:'Value'}, inplace=True)
            lost_load_ramp_down['Variable'] = 'Energy|Electricity|Lost Load Ramp Down'
            lost_load_ramp_down['Unit'] = 'TWh'
            df = df.append(lost_load_ramp_down, ignore_index=True, sort = True)
            df = df[['Zone','Variable','Unit','Value']]
            # LL_Ramp_Up
            lost_load_ramp_up = pd.DataFrame(results['LostLoad_RampUp'].sum() / 1e6)
            lost_load_ramp_up.reset_index(inplace=True)
            lost_load_ramp_up.rename(columns={'index':'Zone', 0:'Value'}, inplace=True)
            lost_load_ramp_up['Variable'] = 'Energy|Electricity|Lost Load Ramp Up'
            lost_load_ramp_up['Unit'] = 'TWh'
            df = df.append(lost_load_ramp_up, ignore_index=True, sort = True)
            df = df[['Zone','Variable','Unit','Value']]
            # LL_Total
            lost_load = pd.DataFrame([results['LostLoad_2D'].sum(),results['LostLoad_2U'].sum(),
                                    results['LostLoad_3U'].sum(),results['LostLoad_MaxPower'].sum(),
                                    results['LostLoad_MinPower'].sum(), results['LostLoad_RampDown'].sum(),
                                    results['LostLoad_RampUp'].sum()])
            lost_load = lost_load / 1e6
            lost_load = lost_load.sum(skipna=True)
            lost_load.reset_index(inplace=True)
            lost_load.rename(columns={'index':'Zone', 0:'Value'}, inplace=True)
            lost_load['Variable'] = 'Energy|Electricity|Lost Load Total'
            lost_load['Unit'] = 'TWh'
            df = df.append(lost_load, ignore_index=True, sort = True)
            df = df[['Zone','Variable','Unit','Value']]
        # CO2
            df = df.append(co2_zone, ignore_index=True, sort = True)
            df = df[['Zone','Variable','Unit','Value']]
            df = df.append(co2, ignore_index=True, sort = True)
            df = df[['Zone','Variable','Unit','Value']]
            return df
        df_generation = generation_df(ppt,results,inputs)
        tmp_df = df_capacity.append(df_generation, ignore_index=True)
        
        # Get startups & costs
        def startups_df(df,results):
            df.loc[(df['Fuel'] == 'HRD') & (df['Technology'] == 'STUR'),'Variable'] = 'Startups|Electricity|Hard coal'
            df.loc[(df['Fuel'] == 'NUC') & (df['Technology'] == 'STUR'),'Variable'] = 'Startups|Electricity|Nuclear'
            df.loc[(df['Fuel'] == 'LIG') & (df['Technology'] == 'STUR'),'Variable'] = 'Startups|Electricity|Lignite'
            df.loc[(df['Fuel'] == 'OIL') & (df['Technology'] == 'STUR'),'Variable'] = 'Startups|Electricity|Oil'
            df.loc[(df['Fuel'] == 'BIO') & (df['Technology'] == 'STUR'),'Variable'] = 'Startups|Electricity|Bioenergy'
            df.loc[(df['Fuel'] == 'OTH') & (df['Technology'] == 'STUR'),'Variable'] = 'Startups|Electricity|Other nonrenewable'
            df.loc[(df['Fuel'] == 'GAS') & (df['Technology'] == 'GTUR'),'Variable'] = 'Startups|Electricity|Gas OCGT'
            df.loc[(df['Fuel'] == 'GAS') & (df['Technology'] == 'COMC'),'Variable'] = 'Startups|Electricity|Gas CCGT'
            df.loc[(df['Fuel'] == 'WST') & (df['Technology'] == 'STUR'),'Variable'] = 'Startups|Electricity|Other renewable'
            df.loc[(df['Fuel'] == 'WIN') & (df['Technology'] == 'WTON'),'Variable'] = 'Startups|Electricity|Wind Onshore'
            df.loc[(df['Fuel'] == 'WIN') & (df['Technology'] == 'WTOF'),'Variable'] = 'Startups|Electricity|Wind Offshore'
            df.loc[(df['Fuel'] == 'SUN') & (df['Technology'] == 'PHOT'),'Variable'] = 'Startups|Electricity|Solar PV'
            df.loc[(df['Fuel'] == 'WAT') & (df['Technology'] == 'HROR'),'Variable'] = 'Startups|Electricity|Hydro ROR'
            df.loc[(df['Fuel'] == 'WAT') & (df['Technology'] == 'HPHS'),'Variable'] = 'Startups|Electricity|Storage|Pumped hydro|Power'
            df.loc[(df['Fuel'] == 'WAT') & (df['Technology'] == 'HDAM'),'Variable'] = 'Startups|Electricity|Hydro Reservoir'
            df.loc[(df['Fuel'] == 'OTH') & (df['Technology'] == 'BATS'),'Variable'] = 'Startups|Electricity|Storage|Liion|Power'
            df['Value'] = df['startups']
            df['Unit'] = '##'
            tmp_df = results['OutputSystemCost'].sum()
            tmp_df = {'Value': [results['OutputSystemCost'].sum()]}
            tmp_df = pd.DataFrame(tmp_df)
            tmp_df.reset_index(inplace=True)
            tmp_df['Variable'] = 'Cost|Total system'
            tmp_df['Zone'] = 'Whole Region'
            tmp_df['Unit'] = 'EUR'
            df = df.append(tmp_df, ignore_index=True, sort = True)
            df = df[['Zone','Variable','Unit','Value']]
            return df
        df_startups = startups_df(ppt,results)
        tmp_df = tmp_df.append(df_startups, ignore_index=True)
        
        # Get capacity factors and storage cycles
        def cap_factor_df(df,results):
            df.loc[(df['Fuel'] == 'HRD') & (df['Technology'] == 'STUR'),'Variable'] = 'Full load hours|Electricity|Hard coal'
            df.loc[(df['Fuel'] == 'NUC') & (df['Technology'] == 'STUR'),'Variable'] = 'Full load hours|Electricity|Nuclear'
            df.loc[(df['Fuel'] == 'LIG') & (df['Technology'] == 'STUR'),'Variable'] = 'Full load hours|Electricity|Lignite'
            df.loc[(df['Fuel'] == 'OIL') & (df['Technology'] == 'STUR'),'Variable'] = 'Full load hours|Electricity|Oil'
            df.loc[(df['Fuel'] == 'BIO') & (df['Technology'] == 'STUR'),'Variable'] = 'Full load hours|Electricity|Bioenergy'
            df.loc[(df['Fuel'] == 'OTH') & (df['Technology'] == 'STUR'),'Variable'] = 'Full load hours|Electricity|Other nonrenewable'
            df.loc[(df['Fuel'] == 'GAS') & (df['Technology'] == 'GTUR'),'Variable'] = 'Full load hours|Electricity|Gas OCGT'
            df.loc[(df['Fuel'] == 'GAS') & (df['Technology'] == 'COMC'),'Variable'] = 'Full load hours|Electricity|Gas CCGT'
            df.loc[(df['Fuel'] == 'WST') & (df['Technology'] == 'STUR'),'Variable'] = 'Full load hours|Electricity|Other renewable'
            df.loc[(df['Fuel'] == 'WIN') & (df['Technology'] == 'WTON'),'Variable'] = 'Full load hours|Electricity|Wind Onshore'
            df.loc[(df['Fuel'] == 'WIN') & (df['Technology'] == 'WTOF'),'Variable'] = 'Full load hours|Electricity|Wind Offshore'
            df.loc[(df['Fuel'] == 'SUN') & (df['Technology'] == 'PHOT'),'Variable'] = 'Full load hours|Electricity|Solar PV'
            df.loc[(df['Fuel'] == 'WAT') & (df['Technology'] == 'HROR'),'Variable'] = 'Full load hours|Electricity|Hydro ROR'
            df.loc[(df['Fuel'] == 'WAT') & (df['Technology'] == 'HPHS'),'Variable'] = 'Full load hours|Electricity|Storage|Pumped hydro|Power'
            df.loc[(df['Fuel'] == 'WAT') & (df['Technology'] == 'HDAM'),'Variable'] = 'Full load hours|Electricity|Hydro Reservoir'
            df.loc[(df['Fuel'] == 'OTH') & (df['Technology'] == 'BATS'),'Variable'] = 'Full load hours|Electricity|Storage|Liion|Power'
            df['Value'] = df['Generation']/df['Nunits']/df['PowerCapacity']
            df['Unit'] = 'hours'
            tmp_stor_input = pd.DataFrame(results['OutputStorageInput'].sum())
            isstorage = pd.Series(index=inputs['units'].index)
            for u in isstorage.index:
                isstorage[u] = inputs['units'].Technology[u] in commons['tech_storage']
            sto_units = inputs['units'][isstorage]
            sto_units['Value'] = pd.DataFrame(tmp_stor_input[0]/sto_units['StorageCapacity'])
            sto_units.reset_index(inplace=True)
            sto_units.loc[(sto_units['Fuel'] == 'OTH') & (sto_units['Technology'] == 'BATS'),'Variable'] = \
                            'Cycles|Electricity|Storage|Liion'
            sto_units.loc[(sto_units['Fuel'] == 'WAT') & (sto_units['Technology'] == 'HPHS'),'Variable'] = \
                            'Cycles|Electricity|Storage|Pumped hydro'
            sto_units = sto_units.drop(sto_units.loc[(sto_units['Fuel'] == 'WAT') & (sto_units['Technology'] == 'HDAM')].index)
            sto_units['Unit'] = '##'
            df = df.append(sto_units, ignore_index=True, sort = True)
            sto_capacity = inputs['units']
            sto_capacity.rename(columns={'StorageCapacity':'Value'}, inplace=True)
            sto_capacity.loc[(sto_capacity['Fuel'] == 'OTH') & (sto_capacity['Technology'] == 'BATS'),'Variable'] = \
                            'Capacity|Electricity|Storage|Liion|Energy'
            sto_capacity.loc[(sto_capacity['Fuel'] == 'WAT') & (sto_capacity['Technology'] == 'HPHS'),'Variable'] = \
                            'Capacity|Electricity|Storage|Pumped hydro|Energy'
            sto_capacity['Value'] = sto_capacity['Value'] / 1e3
            sto_capacity['Unit'] = 'GWh'
            df1 = sto_capacity.loc[(sto_capacity['Fuel'] == 'OTH') & (sto_capacity['Technology'] == 'BATS')]
            df2 = sto_capacity.loc[(sto_capacity['Fuel'] == 'WAT') & (sto_capacity['Technology'] == 'HPHS')]
            sto_capacity = df1.append(df2, ignore_index=True, sort = True)
            df = df.append(sto_capacity, ignore_index=True, sort = True)
            # Reserves
            lost_load_2D = {'Value': [results['LostLoad_2D'].sum().sum() / 1e6]}
            lost_load_2D = pd.DataFrame(lost_load_2D)
            lost_load_2D.reset_index(inplace=True)
            lost_load_2D['Variable'] = 'Energy|Electricity|Lost Load 2D'
            lost_load_2D['Unit'] = 'TWh'
            lost_load_2D['Zone'] = 'Whole Region'
            df = df.append(lost_load_2D, ignore_index=True, sort = True)
            df = df[['Zone','Variable','Unit','Value']]
            lost_load_2U = {'Value': [results['LostLoad_2U'].sum().sum() / 1e6]}
            lost_load_2U = pd.DataFrame(lost_load_2U)
            lost_load_2U.reset_index(inplace=True)
            lost_load_2U['Variable'] = 'Energy|Electricity|Lost Load 2U'
            lost_load_2U['Unit'] = 'TWh'
            lost_load_2U['Zone'] = 'Whole Region'
            df = df.append(lost_load_2U, ignore_index=True, sort = True)
            df = df[['Zone','Variable','Unit','Value']]
            lost_load_3U = {'Value': [results['LostLoad_3U'].sum().sum() / 1e6]}
            lost_load_3U = pd.DataFrame(lost_load_3U)
            lost_load_3U.reset_index(inplace=True)
            lost_load_3U['Variable'] = 'Energy|Electricity|Lost Load 3U'
            lost_load_3U['Unit'] = 'TWh'
            lost_load_3U['Zone'] = 'Whole Region'
            df = df.append(lost_load_3U, ignore_index=True, sort = True)
            df = df[['Zone','Variable','Unit','Value']]
            lost_load_max_power = {'Value': [results['LostLoad_MaxPower'].sum().sum() / 1e6]}
            lost_load_max_power = pd.DataFrame(lost_load_max_power)
            lost_load_max_power.reset_index(inplace=True)
            lost_load_max_power['Variable'] = 'Energy|Electricity|Lost Load Max Power'
            lost_load_max_power['Unit'] = 'TWh'
            lost_load_max_power['Zone'] = 'Whole Region'
            df = df.append(lost_load_max_power, ignore_index=True, sort = True)
            df = df[['Zone','Variable','Unit','Value']]
            lost_load_min_power = {'Value': [results['LostLoad_MinPower'].sum().sum() / 1e6]}
            lost_load_min_power = pd.DataFrame(lost_load_min_power)
            lost_load_min_power.reset_index(inplace=True)
            lost_load_min_power['Variable'] = 'Energy|Electricity|Lost Load Min Power'
            lost_load_min_power['Unit'] = 'TWh'
            lost_load_min_power['Zone'] = 'Whole Region'
            df = df.append(lost_load_min_power, ignore_index=True, sort = True)
            df = df[['Zone','Variable','Unit','Value']]
            lost_load_ramp_down = {'Value': [results['LostLoad_RampDown'].sum().sum() / 1e6]}
            lost_load_ramp_down = pd.DataFrame(lost_load_ramp_down)
            lost_load_ramp_down.reset_index(inplace=True)
            lost_load_ramp_down['Variable'] = 'Energy|Electricity|Lost Load Ramp Down'
            lost_load_ramp_down['Unit'] = 'TWh'
            lost_load_ramp_down['Zone'] = 'Whole Region'
            df = df.append(lost_load_ramp_down, ignore_index=True, sort = True)
            df = df[['Zone','Variable','Unit','Value']]
            lost_load_ramp_up = {'Value': [results['LostLoad_RampUp'].sum().sum() / 1e6]}
            lost_load_ramp_up = pd.DataFrame(lost_load_ramp_up)
            lost_load_ramp_up.reset_index(inplace=True)
            lost_load_ramp_up['Variable'] = 'Energy|Electricity|Lost Load Ramp Up'
            lost_load_ramp_up['Unit'] = 'TWh'
            lost_load_ramp_up['Zone'] = 'Whole Region'
            df = df.append(lost_load_ramp_up, ignore_index=True, sort = True)
            df = df[['Zone','Variable','Unit','Value']]
            lost_load = {'Value': [(results['LostLoad_2D'].sum().sum() + results['LostLoad_2U'].sum().sum() +
                                    results['LostLoad_3U'].sum().sum() + results['LostLoad_MaxPower'].sum().sum() +
                                    results['LostLoad_MinPower'].sum().sum() + results['LostLoad_RampDown'].sum().sum() +
                                    results['LostLoad_RampUp'].sum().sum()) / 1e6]}
            lost_load = pd.DataFrame(lost_load)
            lost_load.reset_index(inplace=True)
            lost_load['Variable'] = 'Energy|Electricity|Lost Load Total'
            lost_load['Unit'] = 'TWh'
            lost_load['Zone'] = 'Whole Region'
            df = df.append(lost_load, ignore_index=True, sort = True)
            df = df[['Zone','Variable','Unit','Value']]
            shed_load = {'Value': [results['OutputShedLoad'].sum().sum() / 1e6]}
            shed_load = pd.DataFrame(shed_load)
            shed_load.reset_index(inplace=True)
            shed_load['Variable'] = 'Energy|Electricity|Load Shedding'
            shed_load['Unit'] = 'TWh'
            shed_load['Zone'] = 'Whole Region'
            df = df.append(shed_load, ignore_index=True, sort = True)
            df = df[['Zone','Variable','Unit','Value']]
            return df
        df_cap_factor = cap_factor_df(ppt,results)
        OSE_report = tmp_df.append(df_cap_factor, ignore_index=True)
        
        # Get additional info for each scenario 
        OSE_report['Model'] = 'Dispa-SET (' + model + ')'
        OSE_report['Scenario'] = scenario + '|' + coverage
        OSE_report.rename(columns={'Zone':'Region'}, inplace=True)
        OSE_report['Unnamed: 6'] = np.nan
        OSE_report['1'] = scenario
        OSE_report['2'] = coverage
        OSE_report['3'] = np.nan
        
        OSE_report = OSE_report[['Model','Scenario','Region','Variable','Unit','Value','Unnamed: 6','1','2','3']]
        
        return OSE_report

tmp_data = get_OSE_MC(model,scenario,coverage)

# OSE_report = pd.DataFrame()
# for m in model_db:
#     for c in coverage_db:
#         for s in scenario_db:
#             tmp_data = get_OSE_MC(m,s,c)
#             OSE_report = OSE_report.append(tmp_data, ignore_index=True)
#
# OSE_report.to_excel(output_folder + 'Dispa-SET_preliminary_results.xlsx')
