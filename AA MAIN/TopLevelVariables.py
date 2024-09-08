import time
import numpy as np

"""Top Level Variables to be Changed"""
rampup = 50  # Voltage for ramping Up
rampdown = 50

saveFolder = r"C:\Users\pdlms\OneDrive\Desktop\Mass Spec\AA MAIN\Data"   #r'C:\Users\pdlms\OneDrive\Desktop\Mass Spec\Data'
saveFolder = f'{saveFolder}\\{time.strftime("%d%b%Y", time.gmtime())}'

testFile = r'C:\Users\pdlms\OneDrive\Desktop\Mass Spec\Testing4.csv'

voltageCOM = 5  #COM port number, find in device manager
pulseCOM = 9
MCPCOM = 8

pre_factor = 69.18639678433904  # 52.82749284  # This is factor from one set of data




"""These are used to indicate moments in the gui. Don't change unless you know what you are doing."""

# State of the program. Used to check if things have been setup, and used as the relevant object when setup.
first_time = 1
voltageSupplyOpened = False
MCPOpened = False
picoOpened = False
gen = 0
caen = 0
MCPcaen = 0
vacuumReady = False
HV0 = HV1 = HV2 = HV3 = MCP = 0


handle = None
block = True

# Old code not in use
repeat = False
threadFunc = 0

# Plotting variables
# For calibrated graph
canvas = 0
fig = 0

# For uncalibrated graph
canvas1 = 0
fig1 = 0

x = 0
y= 0