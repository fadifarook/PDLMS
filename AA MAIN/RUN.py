import customtkinter as ctk
import sys
import numpy as np
import pandas as pd
import time
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from API.MassSpec6000 import massSpecProgram
from CAENpy.CAENDesktopHighVoltagePowerSupply import CAENDesktopHighVoltagePowerSupply, OneCAENChannel
from API.PulseGenPy import pulseGenerator

import TopLevelVariables
from _pulseFunctions import pulseFunctions
from _voltageFunctions import voltageFunctions
from _picoscopeFunctions import picoscopeFunctions
from _calibrationFunctions import calibrationFunctions


"""
Variables for ctkApp Class GUI:

    -mass_calibration (float): Calibration value for mass spectrometer calculations.
    -theoreticalText (ctk.CTkLabel): Label widget for displaying theoretical value of the calibration.
    -currentCalibrationText (ctk.CTkLabel): Label widget for displaying current calibration value.

    -slider (ctk.CTkSlider): Slider widget for controlling calibration factor.
    -input (ctk.CTkEntry): Entry widget for typing the calibration value.
    -button (ctk.CTkButton): Button widget for updating graph with the given calibration value.

    -activateHV (ctk.CTkButton): Button widget for sending voltages to high voltage supplies.
    -setupPulseButton (ctk.CTkButton): Button widget for setting up pulse generator.
    -pulseButton (ctk.CTkButton): Button widget for sending a pulse.
    -picoscope (ctk.CTkButton): Button widget for setting up Picoscope.
    -dataCollection (ctk.CTkButton): Button widget for sending a pulse and getting the data from the picoscope.

    -saveInput (ctk.CTkEntry): Entry widget for typing the file name to save.
    -saveButton (ctk.CTkButton): Button widget for saving the current data.
    -killButton (ctk.CTkButton): Button widget for killing all operations.
    
    -Label0 (ctk.CTkTextbox): Textbox widget for displaying channel 0 (Cone 1) information.
    -Label1 (ctk.CTkTextbox): Textbox widget for displaying channel 1 (Lens 1) information.
    -Label2 (ctk.CTkTextbox): Textbox widget for displaying channel 2 (Deflection) information.
    -Label3 (ctk.CTkTextbox): Textbox widget for displaying channel 3 (Sample) information.
    -LabelMCP (ctk.CTkTextbox): Textbox widget for displaying MCP information.

    -LabelWidth (ctk.CTkTextbox): Textbox widget for displaying current pulse width information.
    -LabelDelay (ctk.CTkTextbox): Textbox widget for displaying current pulse delay information.
    
    -checkbox (ctk.CTkCheckBox): Checkbox widget for opening data from a file instead.
    -voltage1Text (ctk.CTkLabel): Label widget for Cone 1 voltage.
    -voltage1Input (ctk.CTkEntry): Entry widget for Cone 1 voltage input.
    -voltage2Text (ctk.CTkLabel): Label widget for Lens 1 voltage.
    -voltage2Input (ctk.CTkEntry): Entry widget for Lens 1 voltage input.
    -voltage3Text (ctk.CTkLabel): Label widget for PDL Deflection voltage.
    -voltage3Input (ctk.CTkEntry): Entry widget for PDL Deflection voltage input.
    -voltage4Text (ctk.CTkLabel): Label widget for Species voltage.
    -voltage4Input (ctk.CTkEntry): Entry widget for Species voltage input.
    -MCPText (ctk.CTkLabel): Label widget for MCP voltage.
    -MCPInput (ctk.CTkEntry): Entry widget for MCP voltage input.

    Calibration Tab:
    -calibrationButton (ctk.CTkButton): Button widget for starting calibration process.
    -collectionNumberLabel (ctk.CTkLabel): Label widget displaying 'Number of Shots' for calibration.
    -collectionNumberInput (ctk.CTkEntry): Entry widget where the user inputs the number of shots for calibration.

    -randomMeasurementsLabel (ctk.CTkLabel): Label widget displaying 'Random Measurements' for calibration.
    -randomMeasurementsInput (ctk.CTkEntry): Entry widget where the user inputs the number of random measurements for calibration.
    -bayesianMeasurementsLabel (ctk.CTkLabel): Label widget displaying 'Bayesian Measurements' for calibration.
    -bayesianMeasurementsInput (ctk.CTkEntry): Entry widget where the user inputs the number of Bayesian measurements for calibration.

    -parameter1Label (ctk.CTkLabel): Label widget displaying 'Parameter 1:' for configuration.
    -parameter1ComboBox (ctk.CTkComboBox): ComboBox widget for selecting Parameter 1 options (e.g., 'Lens 1', 'Cone 1', 'Deflection Voltage').
    -parameter1StartLabel (ctk.CTkLabel): Label widget displaying 'Start:' for Parameter 1 configuration.
    -parameter1StartInput (ctk.CTkEntry): Entry widget for inputting the starting value of Parameter 1.
    -parameter1StopLabel (ctk.CTkLabel): Label widget displaying 'Stop:' for Parameter 1 configuration.
    -parameter1StopInput (ctk.CTkEntry): Entry widget for inputting the stopping value of Parameter 1.

    -parameter2Label (ctk.CTkLabel): Label widget displaying 'Parameter 2:' for configuration.
    -parameter2ComboBox (ctk.CTkComboBox): ComboBox widget for selecting Parameter 2 options (e.g., 'Lens 1', 'Cone 1', 'Deflection Voltage').
    -parameter2StartLabel (ctk.CTkLabel): Label widget displaying 'Start:' for Parameter 2 configuration.
    -parameter2StartInput (ctk.CTkEntry): Entry widget for inputting the starting value of Parameter 2.
    -parameter2StopLabel (ctk.CTkLabel): Label widget displaying 'Stop:' for Parameter 2 configuration.
    -parameter2StopInput (ctk.CTkEntry): Entry widget for inputting the stopping value of Parameter 2.
    
    Window GUI:
    -root (ctk.CTk): Main application window.
    -toplevel_window (ToplevelWindow or None): Object that refers to Top-level error message window.
    -frame (ctk.CTkFrame): Frame widget for displaying uncalibrated graph.
    -frame2 (ctk.CTkFrame): Frame widget for displaying calibrated graph.
    -frameBot (ctk.CTkFrame): Frame widget for sliders and buttons.
    -navFrame (ctk.CTkFrame): Frame widget for navigation buttons,i.e the monitoring, kill, save etc.
"""


class ToplevelWindow(ctk.CTkToplevel):
    """Top Window for error messages

    The label is overridden with whatever message we set it to.
    Opened by the open_toplevel(message='<text>') of the main class.
    """
    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.geometry("400x100")

        self.label = ctk.CTkLabel(self, text="Test", text_color='white')
        self.label.pack(padx=20, pady=20)

        # Ok Button
        self.button = ctk.CTkButton(self,
                               text="OK",
                               width=100,
                               height=100,
                               command=self.destroy,
                               hover=True,
                               state='enabled',
                               cursor='hand2')  # updates with the button
        self.button.pack(side=ctk.RIGHT, pady=2, padx=2)


class ctkApp(pulseFunctions, voltageFunctions, picoscopeFunctions, calibrationFunctions):
    """Main GUI class. Imports functions from pulseFunctions, voltageFunctions, picoscopeFunctions, calibrationFunctions classes"""

    def __init__(self):
        
        """Theme Preferences"""
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme('dark-blue')


        self.toplevel_window = None  #variable for error window
        global mass_calibration

        """Setting up Main Window"""
        self.root = ctk.CTk()
        self.root.protocol("WM_DELETE_WINDOW", self.closing)  # GUI Behavior when closing. Launches the closing function
        self.root.after(0, lambda:self.root.state('zoomed'))  # Maximize the window immediately
        self.root.geometry("1200x400+200x200")
        self.root.title("Mass Spectrometer Controller")
        self.root.update()


        """Creating Tabs. 2 Tabs for Main and Calibration Gui"""
        tabview = ctk.CTkTabview(master = self.root,
                                height= self.root.winfo_height()*0.5,
                                width = self.root.winfo_width()*0.32,
                                fg_color="transparent",
                                border_color="#000000",
                                border_width=4)
        tabview.place(relx=0.002, rely=0.01)

        mainTab = tabview.add("Main")  # add tab at the end
        calibrationTab = tabview.add("Calibration")  # add tab at the end
        tabview.set("Main") # set currently visible tab



        """Most of below is GUI definitions"""

        # Frame (window) for showing the Uncalibrated graph
        self.frame = ctk.CTkFrame(master=self.root,
                                  height= self.root.winfo_height()*0.3,
                                  width = self.root.winfo_width()*0.45,
                                  fg_color="#020202")
        self.frame.place(relx=0.35, rely=0.025)


        # Frame (window) for shwoing the Calibrated graph
        self.frame2 = ctk.CTkFrame(master=self.root,
                                  height= 500,
                                  width = 1125,
                                  fg_color="#020202")
        self.frame2.place(relx=0.35, rely=0.52)


        # # Frames for Voltage and Pulse Values (to look nice)
        # self.frameTop = ctk.CTkFrame(master=self.root,
        #                           height= self.root.winfo_height()*0.5,
        #                           width = self.root.winfo_width()*0.32,
        #                           fg_color="transparent",
        #                           border_color="#000000",
        #                           border_width=4)
        # self.frameTop.place(relx=0.002, rely=0.01)

        # Frame (window) for Slider and Save Stuff. bottom left
        self.frameBot = ctk.CTkFrame(master=self.root,
                                  height= self.root.winfo_height()*0.45,
                                  width = self.root.winfo_width()*0.32,
                                  fg_color="transparent",
                                  border_color="#000000",
                                  border_width=4)
        self.frameBot.place(relx=0.002, rely=0.54)

        # Frame (window) for zooming in buttons
        self.navFrame = ctk.CTkFrame(master=self.root,
                                  height= 50,
                                  width = 200,
                                  fg_color="transparent",
                                  border_color="#000000",
                                  border_width=4)        
        self.navFrame.place(relx=0.01,rely=0.92)



        """Voltage Labels and Boxes. <Text> is the text on top of the box, <Input> is the place we type the voltage"""
        # Cone 1 voltage
        self.voltage1Text = ctk.CTkLabel(master=mainTab,
                                          width=100,
                                          height=25,
                                          text='Cone 1(V)',
                                          fg_color='transparent')
        self.voltage1Text.place(relx=0.01/0.32, rely=0.02/0.5)

        self.voltage1Input =  ctk.CTkEntry(master=mainTab,
                                   placeholder_text=100,
                                   justify='center',
                                   width=100,
                                   height=50,
                                   fg_color="#515151")
        self.voltage1Input.insert(0,str(5))  # default value
        self.voltage1Input.place(relx=0.010/0.32,rely=0.05/0.5)

        #Lens 1 Voltage
        self.voltage2Text = ctk.CTkLabel(master=mainTab,
                                          width=100,
                                          height=25,
                                          text = 'Lens 1 (V)',
                                          fg_color='transparent')
        self.voltage2Text.place(relx=0.08/0.32, rely=0.02/0.5)

        self.voltage2Input =  ctk.CTkEntry(master=mainTab,
                                   placeholder_text=100,
                                   justify='center',
                                   width=100,
                                   height=50,
                                   fg_color="#515151")
        self.voltage2Input.insert(0,str(5))  # default value
        self.voltage2Input.place(relx=0.08/0.32,rely=0.05/0.5)

        # PDL Deflection Voltage
        self.voltage3Text = ctk.CTkLabel(master=mainTab,
                                          width=100,
                                          height=25,
                                          text='PDL High Voltage (V)',
                                          fg_color='transparent')
        self.voltage3Text.place(relx=0.15/0.32, rely=0.02/0.5)

        self.voltage3Input =  ctk.CTkEntry(master=mainTab,
                                   placeholder_text=100,
                                   justify='center',
                                   width=100,
                                   height=50,
                                   fg_color="#515151")
        self.voltage3Input.insert(0,str(5))  # default value
        self.voltage3Input.place(relx=0.15/0.32,rely=0.05/0.5)

        # Species Voltage (usually maxed)
        self.voltage4Text = ctk.CTkLabel(master=mainTab,
                                          width=100,
                                          height=25,
                                          text='Spec HV (V)',
                                          fg_color='transparent')
        self.voltage4Text.place(relx=0.22/0.32, rely=0.02/0.5)

        self.voltage4Input =  ctk.CTkEntry(master=mainTab,
                                   placeholder_text=100,
                                   justify='center',
                                   width=100,
                                   height=50,
                                   fg_color="#515151")
        self.voltage4Input.insert(0,str(5))  # default value
        self.voltage4Input.place(relx=0.22/0.32,rely=0.05/0.5)


        #MCP Voltage
        self.MCPText = ctk.CTkLabel(master=mainTab,
                                          width=100,
                                          height=25,
                                          text='MCP Negative (V)',
                                          fg_color='transparent')
        self.MCPText.place(relx=0.01/0.32, rely=0.11/0.5)

        self.MCPInput =  ctk.CTkEntry(master=mainTab,
                                   placeholder_text=100,
                                   justify='center',
                                   width=100,
                                   height=50,
                                   fg_color="#515151")
        self.MCPInput.insert(0,str(5))  # default value
        self.MCPInput.place(relx=0.01/0.32,rely=0.14/0.5)


        """CheckBox that changes the behavior to opening a file"""
        self.checkbox = ctk.CTkCheckBox(master=mainTab, 
                                        text="From File", 
                                        command=None)
        self.checkbox.place(relx=0.25/0.32, rely = 0.12/0.5)

        # # Pulse Repeated or not
        # self.repeated = ctk.CTkCheckBox(master=mainTab, 
        #                                 text="2 Hz pulse", 
        #                                 command=self.repeat)
        # self.repeated.place(relx=0.25, rely = 0.15)

        # """To have shots at repeated intervals"""
        # self.repeated = ctk.CTkComboBox(master=mainTab,
        #                                 values=["Single Shot", "1Hz", "2Hz"],
        #                                 command=self.repeat)
        # self.repeated.place(relx=0.24/0.32, rely = 0.15/0.5)

        '''Pulse Generator Labels and Boxes. <Text> is the text on top of the box, <Input> is the place we type the voltage'''
        # Pulse Width
        self.pulseWidthText = ctk.CTkLabel(master=mainTab,
                                          width=150,
                                          height=25,
                                          text='Pulse Width (ms)',
                                          fg_color='transparent')
        self.pulseWidthText.place(relx=0.01/0.32, rely=0.2/0.5)

        self.pulseWidthInput =  ctk.CTkEntry(master=mainTab,
                                   placeholder_text=100,
                                   justify='center',
                                   width=150,
                                   height=50,
                                   fg_color="#515151")
        self.pulseWidthInput.insert(0,str(10))  # default value
        self.pulseWidthInput.place(relx=0.01/0.32,rely=0.23/0.5)

        # Pulse Delay
        self.pulseDelayText = ctk.CTkLabel(master=mainTab,
                                          width=150,
                                          height=25,
                                          text='Pulse Delay (ms)',
                                          fg_color='transparent')
        self.pulseDelayText.place(relx=0.12/0.32, rely=0.2/0.5)

        self.pulseDelayInput =  ctk.CTkEntry(master=mainTab,
                                   placeholder_text=100,
                                   justify='center',
                                   width=150,
                                   height=50,
                                   fg_color="#515151")
        self.pulseDelayInput.insert(0,str(5))  # default value
        self.pulseDelayInput.place(relx=0.12/0.32,rely=0.23/0.5)



        """Bottom Frame. Readouts for the voltage, sliders, save button, etc."""
        # Calculated Theoretical Value based on voltage
        mass_calibration = TopLevelVariables.pre_factor/np.sqrt(float(self.voltage1Input.get()))
        self.theoreticalText = ctk.CTkLabel(master=self.root,
                                          width=200,
                                          height=25,
                                          text=f'Theoretical Value : NA',
                                          fg_color='transparent')
        self.theoreticalText.place(relx=0.01, rely=0.75)

        # Currently used calibration factor
        self.currentCalibrationText = ctk.CTkLabel(master=self.root,
                                          width=200,
                                          height=25,
                                          text=f'Current Value : NA',
                                          fg_color='transparent')
        self.currentCalibrationText.place(relx=0.1, rely=0.75)

        #Slider for controlling the calibration factor
        self.slider = ctk.CTkSlider(master=self.root,
                                    width=400,
                                    height=20,
                                    from_=1,
                                    to=5,
                                    number_of_steps=1000,
                                    command=self.update_surface,
                                    state='disabled')  # this command is the function it does
        self.slider.set(mass_calibration)
        self.slider.place(relx= 0.01,rely=0.8) 

        # Mass Calibration Textbox. Type the calibration value required
        self.input =  ctk.CTkEntry(master=self.root,
                                   placeholder_text=100,
                                   justify='center',
                                   width=200,
                                   height=50,
                                   fg_color="#515151")
        self.input.insert(0,'NA')
        self.input.place(relx=0.01,rely=0.83)



        """Buttons"""

        #Activate the High Voltage Supplies
        self.activateHV = ctk.CTkButton(master = mainTab,
                               text="Set Up Voltages",
                               width=150,
                               height=50,
                               command=self.setupRest)  # updates with the button
        self.activateHV.place(relx=0.02/0.32,rely=0.32/0.5)

        # Setup Pulse Button
        self.setupPulseButton = ctk.CTkButton(master=mainTab,
                                        text = 'Setup Pulse Gen',
                                        width = 150,
                                        height = 50,
                                        command=self.setupPulse)
        self.setupPulseButton.place(relx=0.22/0.32, rely=0.23/0.5)

        # Start Pulse Button
        self.pulseButton = ctk.CTkButton(master = mainTab,
                               text="Start Pulse",
                               width=150,
                               height=50,
                               command=self.runPulse,
                               state='disabled')  # updates with the button
        self.pulseButton.place(relx=0.02/0.32,rely=0.4/0.5) 

        # Setup the Picoscope
        self.picoscope = ctk.CTkButton(master = mainTab,
                               text="Setup Picoscope",
                               width=150,
                               height=50,
                               command=self.setup_picoscope)
        self.picoscope.place(relx=0.12/0.32,rely=0.32/0.5)

        # Pulse and GetData from Picoscope
        self.dataCollection = ctk.CTkButton(master = mainTab,
                               text="Get Data",
                               width=150,
                               height=50,
                               command=self.data_collection,
                               state='disabled',
                               fg_color='green')  # updates with the button
        self.dataCollection.place(relx=0.12/0.32,rely=0.4/0.5)

        # Update Graph
        self.button = ctk.CTkButton(master = self.root,
                               text="Update Graph",
                               width=200,
                               height=50,
                               command=self.update_window,
                               state='disabled')  # updates with the button
        self.button.place(relx=0.15,rely=0.83)



        # saveFile Name Input Box
        self.saveInput =  ctk.CTkEntry(master=self.root,
                                   placeholder_text='Name of Your File',
                                   justify='center',
                                   width=150,
                                   height=50,
                                   fg_color="#515151")
        # self.saveInput.insert(0,'N')
        self.saveInput.place(relx=0.15,rely=0.92)

        # Save Button
        self.saveButton = ctk.CTkButton(master=self.root,
                                        text = 'Save',
                                        width = 80,
                                        height = 50,
                                        command=self.save)
        self.saveButton.place(relx = 0.25, rely=0.92)


        # # # Stop Repeat
        # self.stopRepeatButton = ctk.CTkButton(master=mainTab,
        #                                 text = 'Stop repeat',
        #                                 width = 80,
        #                                 height = 25,
        #                                 command=self.stopRepeat,
        #                                 fg_color='#8b0000',
        #                                 state='normal')
        # self.stopRepeatButton.place(relx = 0.25, rely=0.18)





        """Monitoring voltages labels + Kill Button"""

        # Kill Button
        self.killButton = ctk.CTkButton(master=self.root,
                                        text = 'Kill',
                                        width = 80,
                                        height = 25,
                                        command=self.kill,
                                        fg_color='#8b0000',
                                        state='normal')
        self.killButton.place(relx = 0.25, rely=0.56)

        #Monitoring Labels. 0 -> 3 corresponds to HV0 -> HV3
        self.Label0 = ctk.CTkTextbox(master=self.root,
                                          width=120,
                                          height=120,
                                          fg_color='transparent')
        self.Label0.insert(0.0, f'Channel 0 \n Vset: \n Vmon: \n Iset: \n Imon')
        self.Label0.place(relx=0.005, rely=0.6)

        self.Label1 = ctk.CTkTextbox(master=self.root,
                                          width=120,
                                          height=120,
                                          fg_color='transparent')
        self.Label1.insert(0.0, f'Channel 1 \n Vset: \n Vmon: \n Iset: \n Imon')
        self.Label1.place(relx=0.085, rely=0.6)

        self.Label2 = ctk.CTkTextbox(master=self.root,
                                          width=120,
                                          height=120,
                                          fg_color='transparent')
        self.Label2.insert(0.0, f'Channel 2 \n Vset: \n Vmon: \n Iset: \n Imon')
        self.Label2.place(relx=0.165, rely=0.6)

        self.Label3 = ctk.CTkTextbox(master=self.root,
                                          width=120,
                                          height=120,
                                          fg_color='transparent')
        self.Label3.insert(0.0, f'Channel 3 \n Vset: \n Vmon: \n Iset: \n Imon')
        self.Label3.place(relx=0.245, rely=0.6)

        self.LabelMCP = ctk.CTkTextbox(master=self.root,
                                          width=120,
                                          height=120,
                                          fg_color='transparent')
        self.LabelMCP.insert(0.0, f'MCP \n Vset: \n Vmon: \n Iset: \n Imon')
        self.LabelMCP.place(relx=0.245, rely=0.69)


        """Displaying the Pulse generator setup"""
        self.LabelWidth = ctk.CTkTextbox(master=mainTab,
                                          width=150,
                                          height=10,
                                          fg_color='transparent')
        self.LabelWidth.insert(0.0, f'Pulse Width: ')
        self.LabelWidth.place(relx=0.13/0.32, rely=0.47/0.5)

        self.LabelDelay = ctk.CTkTextbox(master=mainTab,
                                          width=150,
                                          height=10,
                                          fg_color='transparent')
        self.LabelDelay.insert(0.0, f'Pulse Delay: ')
        self.LabelDelay.place(relx=0.2/0.32, rely=0.47/0.5)




        """All calibration Tools"""
        # Status of Calibration
        # self.calibrationText = ctk.CTkLabel(master=calibrationTab,
        #                                   width=150,
        #                                   height=25,
        #                                   text='Calibrated Voltage: NA',
        #                                   fg_color='transparent')
        # self.calibrationText.place(relx=0.21/0.32,rely=0.35/0.5)

        # Calibration Button
        self.calibrationButton = ctk.CTkButton(master = calibrationTab,
                               text="Start Calibration",
                               width=150,
                               height=50,
                               command=self.threadCalibrationFunction,
                               fg_color='green')
        self.calibrationButton.place(relx=0.22/0.32,rely=0.85)

        """Parameter 1 dropdowns and input boxes for the start and stop voltages"""

        self.parameter1Label = ctk.CTkLabel(master=calibrationTab,
                                            width = 100,
                                            height=25,
                                            text = 'Parameter 1:',
                                            fg_color='transparent')
        self.parameter1Label.place(relx=0.01, rely = 0.3)

        self.parameter1ComboBox = ctk.CTkComboBox(master=calibrationTab,
                                        values=["Lens 1", "Cone 1", "Deflection Voltage"],
                                        command=None, state="readonly")
        self.parameter1ComboBox.place(relx=0.02, rely = 0.38)
        self.parameter1ComboBox.set('Cone 1')


        # Start and stop label and input for Parameter 1
        self.parameter1StartLabel = ctk.CTkLabel(master=calibrationTab,
                                            width = 100,
                                            height=25,
                                            text = 'Start:',
                                            fg_color='transparent')
        self.parameter1StartLabel.place(relx=0.35, rely = 0.3)

        self.parameter1StartInput =  ctk.CTkEntry(master=calibrationTab,
                                   placeholder_text=100,
                                   justify='center',
                                   width=100,
                                   height=50,
                                   fg_color="#515151")
        self.parameter1StartInput.insert(0,2000)
        self.parameter1StartInput.place(relx=0.35,rely=0.35)

        self.parameter1StopLabel = ctk.CTkLabel(master=calibrationTab,
                                            width = 100,
                                            height=25,
                                            text = 'Stop:',
                                            fg_color='transparent')
        self.parameter1StopLabel.place(relx=0.6, rely = 0.3)

        self.parameter1StopInput =  ctk.CTkEntry(master=calibrationTab,
                                   placeholder_text=100,
                                   justify='center',
                                   width=100,
                                   height=50,
                                   fg_color="#515151")
        self.parameter1StopInput.insert(0,3200)
        self.parameter1StopInput.place(relx=0.6,rely=0.35)


        """Parameter 2 dropdowns and input boxes for the start and stop voltages"""

        self.parameter2Label = ctk.CTkLabel(master=calibrationTab,
                                            width = 100,
                                            height=25,
                                            text = 'Parameter 2:',
                                            fg_color='transparent')
        self.parameter2Label.place(relx=0.01, rely = 0.6)

        self.parameter2ComboBox = ctk.CTkComboBox(master=calibrationTab,
                                        values=["Lens 1", "Cone 1", "Deflection Voltage"],
                                        command=None, state="readonly")
        self.parameter2ComboBox.place(relx=0.02, rely = 0.68)
        self.parameter2ComboBox.set('Deflection Voltage')


        # Start and stop label and input for Parameter 2
        self.parameter2StartLabel = ctk.CTkLabel(master=calibrationTab,
                                            width = 100,
                                            height=25,
                                            text = 'Start:',
                                            fg_color='transparent')
        self.parameter2StartLabel.place(relx=0.35, rely = 0.6)

        self.parameter2StartInput =  ctk.CTkEntry(master=calibrationTab,
                                   placeholder_text=100,
                                   justify='center',
                                   width=100,
                                   height=50,
                                   fg_color="#515151")
        self.parameter2StartInput.insert(0,2000)
        self.parameter2StartInput.place(relx=0.35,rely=0.65)

        self.parameter2StopLabel = ctk.CTkLabel(master=calibrationTab,
                                            width = 100,
                                            height=25,
                                            text = 'Stop:',
                                            fg_color='transparent')
        self.parameter2StopLabel.place(relx=0.6, rely = 0.6)

        self.parameter2StopInput =  ctk.CTkEntry(master=calibrationTab,
                                   placeholder_text=100,
                                   justify='center',
                                   width=100,
                                   height=50,
                                   fg_color="#515151")
        self.parameter2StopInput.insert(0,3200)
        self.parameter2StopInput.place(relx=0.6,rely=0.65)


        # # Start Step Stop
        # self.startCalibrationLabel = ctk.CTkLabel(master=calibrationTab,
        #                                   width=100,
        #                                   height=25,
        #                                   text='Start Voltage (V)',
        #                                   fg_color='transparent')
        # self.startCalibrationLabel.place(relx=0.01/0.32, rely=0.02/0.5)

        # self.startCalibrationInput =  ctk.CTkEntry(master=calibrationTab,
        #                            placeholder_text=100,
        #                            justify='center',
        #                            width=100,
        #                            height=50,
        #                            fg_color="#515151")
        # self.startCalibrationInput.insert(0,str(5))
        # self.startCalibrationInput.place(relx=0.010/0.32,rely=0.05/0.5)

        # self.stepCalibrationLabel = ctk.CTkLabel(master=calibrationTab,
        #                                   width=100,
        #                                   height=25,
        #                                   text='Step Voltage (V)',
        #                                   fg_color='transparent')
        # self.stepCalibrationLabel.place(relx=0.08/0.32, rely=0.02/0.5)

        # self.stepCalibrationInput =  ctk.CTkEntry(master=calibrationTab,
        #                            placeholder_text=100,
        #                            justify='center',
        #                            width=100,
        #                            height=50,
        #                            fg_color="#515151")
        # self.stepCalibrationInput.insert(0,str(5))
        # self.stepCalibrationInput.place(relx=0.08/0.32,rely=0.05/0.5)

        # self.stopCalibrationLabel = ctk.CTkLabel(master=calibrationTab,
        #                                   width=100,
        #                                   height=25,
        #                                   text='Stop Voltage (V)',
        #                                   fg_color='transparent')
        # self.stopCalibrationLabel.place(relx=0.15/0.32, rely=0.02/0.5)

        # self.stopCalibrationInput =  ctk.CTkEntry(master=calibrationTab,
        #                            placeholder_text=100,
        #                            justify='center',
        #                            width=100,
        #                            height=50,
        #                            fg_color="#515151")
        # self.stopCalibrationInput.insert(0,str(30))
        # self.stopCalibrationInput.place(relx=0.15/0.32,rely=0.05/0.5)

        # Number of Collection Per Voltage
        self.collectionNumberLabel = ctk.CTkLabel(master=calibrationTab,
                                          width=100,
                                          height=25,
                                          text='Number of Shots',
                                          fg_color='transparent')
        self.collectionNumberLabel.place(relx=0.22/0.32, rely=0.02/0.5)

        self.collectionNumberInput =  ctk.CTkEntry(master=calibrationTab,
                                   placeholder_text=100,
                                   justify='center',
                                   width=100,
                                   height=50,
                                   fg_color="#515151")
        self.collectionNumberInput.insert(0,str(10))
        self.collectionNumberInput.place(relx=0.22/0.32,rely=0.05/0.5)

        # Number of Random Measurements
        self.randomMeasurementsLabel = ctk.CTkLabel(master=calibrationTab,
                                          width=100,
                                          height=25,
                                          text='Random Measurements',
                                          fg_color='transparent')
        self.randomMeasurementsLabel.place(relx=0.1, rely=0.02/0.5)

        self.randomMeasurementsInput =  ctk.CTkEntry(master=calibrationTab,
                                   placeholder_text=100,
                                   justify='center',
                                   width=100,
                                   height=50,
                                   fg_color="#515151")
        self.randomMeasurementsInput.insert(0,str(10))
        self.randomMeasurementsInput.place(relx=0.1,rely=0.05/0.5)

        # Number of Bayesian measurements
        self.bayesianMeasurementsLabel = ctk.CTkLabel(master=calibrationTab,
                                          width=100,
                                          height=25,
                                          text='Bayesian Measurements',
                                          fg_color='transparent')
        self.bayesianMeasurementsLabel.place(relx=0.4, rely=0.02/0.5)

        self.bayesianMeasurementsInput =  ctk.CTkEntry(master=calibrationTab,
                                   placeholder_text=100,
                                   justify='center',
                                   width=100,
                                   height=50,
                                   fg_color="#515151")
        self.bayesianMeasurementsInput.insert(0,str(20))
        self.bayesianMeasurementsInput.place(relx=0.4,rely=0.05/0.5)

        # self.progressbar = ctk.CTkProgressBar(master=calibrationTab, 
        #                                       orientation="horizontal",
        #                                       width=200,
        #                                       height=10,
        #                                       progress_color='green')
        # self.progressbar.place(relx=0.2,rely=0.85)
        # self.progressbar.set(0)


        


        """Runs the looping function constantly"""
        self.root.after(0, self.looping)  # updates in time

        mass_calibration = TopLevelVariables.pre_factor/np.sqrt(float(self.voltage1Input.get()))
        self.root.mainloop()


    def closing(self):
        """When closing the gui, it shows error if not killed"""
        # global TopLevelVariables.gen

        # If the voltage supply is open, error
        if isinstance(TopLevelVariables.caen, CAENDesktopHighVoltagePowerSupply) and TopLevelVariables.block:
            self.open_toplevel(message="Remember to Kill the Voltage Supply and the Negative Voltage Supply")
            TopLevelVariables.block = False  # This is so we can override the error and shutdown the program
        # time.sleep(3)
        else:
            sys.exit()


    def open_toplevel(self, message, buttonText='OK'):
        """Opens an errormessage with the desired <message> on top of the GUI
        
        Use this to display any known errors or stop the user from doing restricted activity. It opens the the TopLevelWindow Class"""

        if self.toplevel_window is None or not self.toplevel_window.winfo_exists():
            self.toplevel_window = ToplevelWindow()  # create window if its None or destroyed
            self.toplevel_window.label.configure(text=message)
            self.toplevel_window.button.configure(text=buttonText)
            self.toplevel_window.after(10, self.toplevel_window.lift)
        else:
            self.toplevel_window.focus()  # if window exists focus it

if __name__ == "__main__":        
    CTK_Window = ctkApp()