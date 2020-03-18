# -*- coding: utf-8 -*-
"""
This script is used to format the raw csv data provided by EnergyScope
All time series are gathered for a specific year and saved in new csv files with varying timesteps

@author: Matija Pavičević 
         Sylvain Quoilin
"""
from __future__ import division
import pandas as pd
import numpy as np
import os
from dispaset_sidetools.common import mapping,outliers,fix_na,make_dir
from search import *
#import matplotlib.pyplot as plt

from search import get_TDFile

input_folder = '../../Inputs/'  # Standard input folder
output_folder = '../../Outputs/'# Standard output folder



#Enter countries studied
countries = list(['BE'])

#Enter number of TD
n_TD = 12
get_TDFile(12)

#Enter technology names which elec consumption is to add to EUD
tech = ['TRAMWAY_TROLLEY','TRAIN_PUB','TRAIN_CapitalfREIGHT'] #change list of tech to investigate - TO DO

######################################################################################################
#Enter the starting date
date_str = '1/1/2015'
start = pd.to_datetime(date_str)
hourly_periods = 8760
drange = pd.date_range(start, periods=hourly_periods, freq='H')

#input file
TotalLoadValue = pd.read_csv(input_folder + 'EUD_ELEC.txt',delimiter = '\t' ,index_col = 0) #EUD Load
TotalLoadValue.set_index(drange, inplace=True)
TotalLoadValue.columns = countries


tech_country = list()
for Country in countries:
    for y in tech:
        elec = search_YearBalance(y, 'ELECTRICITY') #TO CHECK
        if elec!=0 :
            tech_country.append(Country + '_' + y)




TotalLoadValue_ESinput = pd.DataFrame(index=range(0,8760), columns=tech_country)

ElecLayers = pd.read_csv(input_folder + 'ElecLayers.txt',delimiter='\t')
TD_DF = pd.read_csv(input_folder + 'TD_file.csv')

for x in range(0,len(countries)):
    for day in range(1,366):
        print(day)
        for h in range(1,25):
            thistd = get_TD(TD_DF,(day-1)*24+h,n_TD)
            for y in tech:
                name = countries[x] + '_' + y
                TotalLoadValue_ESinput.at[(day-1)*24+h-1, name] = search_ElecLayers(ElecLayers,thistd,h,y) * 1000 #TO CHECK


TotalLoadValue_ESinput['Sum'] = -TotalLoadValue_ESinput.sum(axis=1)
TotalLoadValue_ESinput = TotalLoadValue_ESinput.set_index(drange)
for x in countries:
    TotalLoadValue[x] = TotalLoadValue[x] + TotalLoadValue_ESinput['Sum'] # TO BE MODIFIED FOR SEVERAL COUNTRIES !!!!!!!!!!!


######################################################################################################

def write_csv_files(file_name,demand,write_csv=None):

    filename = file_name + '.csv'
    if write_csv == True:
        for c in demand:
            make_dir(output_folder + 'Database')
            folder = output_folder + 'Database/TotalLoadValue/'
            make_dir(folder)
            make_dir(folder + c)
            demand[c].to_csv(folder + c + '/' + filename, header=False)
    else:
        print('[WARNING ]: '+'WRITE_CSV_FILES = False, unable to write .csv files')

write_csv_files('2015',TotalLoadValue,True)
#TotalLoadValue.to_csv(output_folder + 'TotalLoadValue.csv', index=True)
