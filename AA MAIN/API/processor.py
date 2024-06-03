"""

Base functions for data conversion and file manipulation

author: Samantha Rudinsky
institution: Steam Instruments, Inc.
date: 2022-08-01

edited: Khaled Madhoun 2023-05-18

"""

import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
import sys
from datetime import datetime
# Globals
projectdir = os.getcwd()
projectdir = projectdir.rsplit('code')[0]
pk_width = 1.80 # ns
trace_mean = 0.890 # mV
pk_ampl = 7.0 # mV
pk_sigma = 1.9 # mV
pk_height = pk_ampl - trace_mean
mu = 0
pk_area = pk_height * pk_sigma * np.sqrt(2*np.pi)

"""

Save instrument configuration settings from excel file

"""
def SaveSettings(xlsfilename : str, configfilename : str):
    df = pd.read_excel(xlsfilename, header=None)
    names = df[0].to_list()
    values = df[1].to_list()
    dictionary = dict(zip(names, values))

    # Check what the ending of spectrum filename is
    extension = configfilename.rsplit('.')[-1]
    outfilename = configfilename if extension == 'json' else configfilename + '.json'

    with open(outfilename, 'w') as file:
        json.dump(dictionary, file, indent=4)

    return dictionary

"""

Convert times and mV from csv file produced by picoscope to counts and m/z given current calibration

"""
def convert_to_calibrated(filename : str, config : dict, time=None, volt=None):   
    
    # load configurations
    mass_calibration = config['calibration_factor']
    mcp_voltage = config['mcp_voltage_V']
    pk_area = 9E-7 * np.exp(0.0058 * mcp_voltage)  # completely useless, we never use this
    # if units[1] == '(mV)':  # removed for now
    #     pk_area *= 1000
    pk_area*=1000
    nspectra = config['num_buffers']  # we use this tho for some reason

    # Find and remove infinity signs
    # TODO: value is just replaced by 10 V
    infty = "\u221E"
    neginfty = "-\u221E"

    # Live conversion
    if time is not None:
        times_us = np.asarray(time, dtype='float64')
        nparr = np.asarray(volt, dtype='float64')
        nparr[nparr == neginfty] = -10  # convert the infinities and neginfinities to +-10
        nparr[nparr == infty] = 10
        mVs = np.asarray(nparr, dtype='float64') * float(nspectra)  # why this????????????
        mVs = mVs * -1
    # file conversion
    else:
        # Load spectrum
        data = pd.read_csv(filename, header=0, skip_blank_lines=True)
        units = data.iloc[0].to_list()
        data = data.drop(0)
        try:
            times_us = np.asarray(data['Time'], dtype='float64')  # get the time array
        except KeyError:
            print(filename + ': No time found')
            return None

        # Get average data (may be inverted)
        try:
            nparr = np.asarray(data['Channel A'])
            nparr[nparr == neginfty] = -10  # convert the infinities and neginfinities to +-10
            nparr[nparr == infty] = 10
            mVs = np.asarray(nparr, dtype='float64') * float(nspectra)  # why this????????????
            mVs = mVs * -1
            print('Yay')
        except KeyError:
            try:
                nparr = np.asarray(data['invertedAverage(A)'])  # works much better
                nparr[nparr == neginfty] = -10
                nparr[nparr == infty] = 10
                mVs = np.asarray(nparr, dtype='float64') * float(nspectra)
            except KeyError:
                print(filename + ': No average trace found')
                return None

    # Convert the data  
    mVs = mVs[times_us >=0]  # take the positive times
    times_us = times_us[times_us >= 0]
    mzs = (times_us/mass_calibration)**2  # conversion from book
    cnts_temp = (mVs/pk_area)  # is there any need for the pk_area? I think it cancels out since pk_area is a constant
    kaju = max(cnts_temp)
    cnts = cnts_temp/kaju
    processed_data = pd.DataFrame(np.column_stack((mzs,cnts)), columns=['m/z', 'Counts'])

    mean = np.mean(mVs)
    print(mean)
    print(np.min(mVs))

    return processed_data

"""

Run calibration conversion for most recent file in specified directory
TODO: Untested
"""
def run_most_recent(directory : str, xlsfilename : str):
    # Do the most recent file in the directory
    newtime = 0
    for file in os.listdir(directory):
        fullname = os.path.join(directory, file)
        if os.path.getctime(fullname) > newtime:
            newtime = os.path.getctime(fullname)
            newfile = fullname

    # Get filename
    currentFile = newfile.rsplit('.csv')[0]

    # Get current instrument settings
    jsonfilename = currentFile + '_config.json'
    config = SaveSettings(xlsfilename, jsonfilename)

    processed_data = convert_to_calibrated(newfile, config)
    if processed_data is not None:
        processed_data.to_csv(currentFile + '_processed.csv', index=False)

"""

Convert all files in a directory

"""
def run_directory_all(directory : str, xlsfilename : str):

    # Save one configuration for the whole directory
    jsonfilename = os.path.join(directory, 'config.json')
    config = SaveSettings(xlsfilename, jsonfilename)

    for file in os.listdir(directory):
        fullname = os.path.join(directory, file)

        # Get filename
        if len(fullname.rsplit('.csv')) > 1:
            currentFile = fullname.rsplit('.csv')[0]
        else:
            continue

        # Process file
        processed_data = convert_to_calibrated(fullname, config)
        if processed_data is not None:
            processed_data.to_csv(currentFile + '_processed.csv', index=False)

    # Plot the last converted file
    if processed_data is not None:
        plt.plot(processed_data["m/z"], processed_data["Counts"])
        plt.xlabel("m/z")
        plt.ylabel("Intensity (counts)")
        plt.title(currentFile.rsplit('/', maxsplit=1)[-1])
        plt.show(block=False)

"""

Run calibration conversion for specific file

"""
def run_single_file(filename : str, xlsfilename : str):
    # Get configuration
    currentFile = filename.rsplit('.csv')[0]
    jsonfilename = currentFile + '_config.json'
    config = SaveSettings(xlsfilename, jsonfilename)

    processed_data = convert_to_calibrated(filename, config)

    # Plot calibrated data
    plt.plot(processed_data["m/z"], processed_data["Counts"])
    plt.xlabel("m/z")
    plt.ylabel("Intensity (counts)")
    plt.title(currentFile.rsplit('/', maxsplit=1)[-1])
    plt.show(block=False)
    if processed_data is not None:
        processed_data.to_csv(currentFile + '_processed.csv', index=False)

"""

Run calibration conversion for two lists containing data (for live conversion)

"""

def run_live(time_array: list, volt_array: list, identifier: str, xlsfilename: str):
    # Get configuration
    jsonfilename = identifier + '_config.json'
    config = SaveSettings(xlsfilename, jsonfilename)

    fig, (ax1, ax2) = plt.subplots(2)
    fig.tight_layout()
    # fig.suptitle(identifier + ' : Mass Spectrometery')
    ax1.plot(time_array, volt_array)
    ax1.set_title('Before Conversion')
    ax1.set_xlabel('Time (us)')
    ax1.set_ylabel('Intensity (mV)')

    processed_data = convert_to_calibrated(identifier, config, time = time_array, volt = volt_array)
    if processed_data is not None:
        processed_data.to_csv(identifier + '_processed.csv', index=False)  # make sure to save unprocessed too
    ax2.plot(processed_data["m/z"], processed_data["Counts"])
    ax2.set_xlabel("m/z")
    ax2.set_ylabel("Intensity (counts)")
    ax2.set_title('After Conversion')

    wm = plt.get_current_fig_manager()
    wm.window.state('zoomed')  # full screen the data


    plt.show(block=False)

    # print(processed_data)
    
    return processed_data

if __name__ == "__main__":

    # Input arguments must be directory or file to be converted
    # If directory is provided, most recent file in directory is converted

    if len(sys.argv) != 3:
        print("Invalid arguments")
        exit(0)
    inputStr = sys.argv[1]

    # Current location
    currentdir = os.getcwd()

    try:
        l = os.listdir(inputStr)
        run_most_recent(inputStr, os.path.join(currentdir, "CurrentConfig.xlsx"))
    except NotADirectoryError:
        run_single_file(inputStr, os.path.join(currentdir, "CurrentConfig.xlsx"))
