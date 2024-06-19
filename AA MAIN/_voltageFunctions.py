import customtkinter as ctk
import sys
import numpy as np
import pandas as pd
import time
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from API.MassSpec6000 import massSpecProgram, closePicoscope
from CAENpy.CAENDesktopHighVoltagePowerSupply import CAENDesktopHighVoltagePowerSupply, OneCAENChannel
from API.PulseGenPy import pulseGenerator

import TopLevelVariables




class voltageFunctions:

    def setupRest(self):
        """Connects to the voltage Supply"""

        if not TopLevelVariables.vacuumReady:
            self.open_toplevel(message='Make sure the Vacuum is Working', buttonText='Done')
            TopLevelVariables.vacuumReady= True
            return None


        # Try to connect to voltage Supply
        try:
            if not TopLevelVariables.voltageSupplyOpened:
                TopLevelVariables.caen = CAENDesktopHighVoltagePowerSupply(port=f'COM{TopLevelVariables.voltageCOM}') 

                # Now create 4 independent power supplies, one for each channel:
                TopLevelVariables.HV0 = OneCAENChannel(caen=TopLevelVariables.caen, channel_number=0)
                TopLevelVariables.HV1 = OneCAENChannel(caen=TopLevelVariables.caen, channel_number=1)
                TopLevelVariables.HV2 = OneCAENChannel(caen=TopLevelVariables.caen, channel_number=2)
                TopLevelVariables.HV3 = OneCAENChannel(caen=TopLevelVariables.caen, channel_number=3)

                TopLevelVariables.voltageSupplyOpened = True

                # print(1)

        except:
            # Error Message
            self.open_toplevel(message="Can't find HV Supply")
            return None


        # Connect to MCP Voltage Supply
        try:
            if not TopLevelVariables.MCPOpened:
                TopLevelVariables.MCPcaen= CAENDesktopHighVoltagePowerSupply(port=f'COM{TopLevelVariables.MCPCOM}') 
                TopLevelVariables.MCP = OneCAENChannel(caen=TopLevelVariables.MCPcaen, channel_number=None)

                TopLevelVariables.MCPOpened = True
        
        except:
            # Error Message
            self.open_toplevel(message="Can't find MCP HV Supply")
            return None
        
        self.setVoltage(v0=float(self.voltage1Input.get()), v1=float(self.voltage2Input.get()),
                                v2=float(self.voltage3Input.get()), v3=float(self.voltage4Input.get()),
                                v4=float(self.MCPInput.get()))
        
        self.activate.configure(text='Setup Voltages with New Values')



    def setVoltage(self, v0 = 5, v1 = 5, v2=2, v3=5, v4=5 ,ramp=TopLevelVariables.rampup):
        """Powers up the channels, sets rampup voltage and sets the voltage"""
        # global HV0, HV1, HV2, HV3, MCP

        TopLevelVariables.HV0.set(PAR='ON', VAL=None)
        TopLevelVariables.HV1.set(PAR='ON', VAL=None)
        TopLevelVariables.HV2.set(PAR='ON', VAL=None)
        TopLevelVariables.HV3.set(PAR='ON', VAL=None)
        TopLevelVariables.MCP.set(PAR='ON', VAL=None)

        TopLevelVariables.HV0.set(PAR='RUP',VAL=ramp)
        TopLevelVariables.HV1.set(PAR='RUP',VAL=ramp)
        TopLevelVariables.HV2.set(PAR='RUP',VAL=ramp)
        TopLevelVariables.HV3.set(PAR='RUP',VAL=ramp)
        TopLevelVariables.MCP.set(PAR='RUP',VAL=ramp)

        TopLevelVariables.HV0.set(PAR='VSET',VAL=v0)
        TopLevelVariables.HV1.set(PAR='VSET',VAL=v1)
        TopLevelVariables.HV2.set(PAR='VSET',VAL=v2)
        TopLevelVariables.HV3.set(PAR='VSET',VAL=v3)
        TopLevelVariables.MCP.set(PAR='VSET',VAL=v4)

        # print(voltageSupplyOpened)


    def looping(self):
        """Loop for monitoring the voltage and currents of each channel"""

        if TopLevelVariables.voltageSupplyOpened:
            for label, source in {self.Label0:TopLevelVariables.HV0, self.Label1:TopLevelVariables.HV1, self.Label2:TopLevelVariables.HV2, self.Label3:TopLevelVariables.HV3}.items():
                name = label.get(0.0, 1.9)
                label.delete(0.0, 100.0)
                label.insert(0.0, f'{name} \n Vset: {float(source.V_set[:-1])} V \n Vmon: {float(source.V_mon[:-1])}V\n Iset: {float(source.I_set[:-1])}A\n Imon {float(source.I_mon)}A')
            name = self.LabelMCP.get(0.0, 1.9)
            self.LabelMCP.delete(0.0, 100.0)
            self.LabelMCP.insert(0.0, f'''{name} \n Vset: {float(TopLevelVariables.MCP.V_set)} V \n Vmon: {float(TopLevelVariables.MCP.get(PAR='VMON'))}V\n Iset: {float(TopLevelVariables.MCP.get(PAR='ISET'))}A\n Imon {float(TopLevelVariables.MCP.get(PAR='IMON'))}A''')
        

            # print(int(TopLevelVariables.HV1.get(PAR='STAT')[:-1]))
            

            # Error if OverCurrent
            status = int(TopLevelVariables.HV1.get(PAR='STAT')[:-1])
            if status == 4:
                self.open_toplevel(message="Caution: Overvoltage")
        
        self.root.after(1000, self.looping)  # updates in time



    def kill(self, ramp=TopLevelVariables.rampdown):
        """Shuts down connection to HV and Pulse Gen"""
        TopLevelVariables.repeat = False  # stops any data collection

        if isinstance(TopLevelVariables.gen, pulseGenerator): #If defined at all
            TopLevelVariables.gen.stop()  # switches off the pulser
            TopLevelVariables.gen = 0

        if isinstance(TopLevelVariables.caen, CAENDesktopHighVoltagePowerSupply):
            
            TopLevelVariables.HV0.V_set = 0
            TopLevelVariables.HV1.V_set = 0
            TopLevelVariables.HV2.V_set = 0
            TopLevelVariables.HV3.V_set = 0
            # MCP.V_set = 0

            TopLevelVariables.HV0.set(PAR='RDW',VAL=ramp)
            TopLevelVariables.HV1.set(PAR='RDW',VAL=ramp)
            TopLevelVariables.HV2.set(PAR='RDW',VAL=ramp)
            TopLevelVariables.HV3.set(PAR='RDW',VAL=ramp)

            TopLevelVariables.HV0.set(PAR='OFF', VAL=None)
            TopLevelVariables.HV1.set(PAR='OFF', VAL=None)
            TopLevelVariables.HV2.set(PAR='OFF', VAL=None)
            TopLevelVariables.HV3.set(PAR='OFF', VAL=None)

            TopLevelVariables.caen = 0
        
        if isinstance(TopLevelVariables.MCPcaen, CAENDesktopHighVoltagePowerSupply):

            TopLevelVariables.MCP.V_set = 0
            TopLevelVariables.MCP.set(PAR='RDW',VAL=ramp)
            TopLevelVariables.MCP.set(PAR='OFF', VAL=None)

            TopLevelVariables.MCPcaen = 0
        
        if TopLevelVariables.picoOpened:
            closePicoscope(chandle=TopLevelVariables.handle)
            TopLevelVariables.picoOpened = False

            self.dataCollection.configure(state='disabled')
            self.picoscope.configure(state='normal')
            self.picoscope.configure(text='Setup Picoscope')
