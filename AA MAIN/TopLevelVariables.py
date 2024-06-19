import time

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




# These are used to indicate moments in the gui. Don't change unless you know what you are doing.
first_time = 1
voltageSupplyOpened = False
MCPOpened = False
picoOpened = False
gen = 0
caen = 0
MCPcaen = 0
vacuumReady = False

handle = None
block = True

repeat = False
threadFunc = 0

HV0 = HV1 = HV2 = HV3 = MCP = 0