# PDLMS
Software for PDLMS in 249. 

CAENDesktopHighVoltagePowerSupply.py is the modification made to the source code from https://github.com/SengerM/CAENpy to work with HV DT5533EP and DT547.

AA MAIN contains all the code for controlling the High Voltage, Pulse Generator and Picoscope simultaneously. It allows you to set voltages, send a single shot of arbitrary width and delay, and see the spectrum. A slider controls the calibration
from time to mass/charge ratios.


RUN contains the GUI code and the other files contain all the relevant functions, this is the only file that is run. TopLevelVariables is the only variables that need changing.

**Required modules:**

1. CAENpy: https://github.com/SengerM/CAENpy  with my modification  -- High Voltage Controller
2. customtkinter: https://customtkinter.tomschimansky.com/  -- GUI
3. pyvisa: https://pyvisa.readthedocs.io/en/latest/  -- Pulse Generator Commands
4. picosdk: https://github.com/picotech/picosdk-python-wrappers  -- Picoscope Controller

