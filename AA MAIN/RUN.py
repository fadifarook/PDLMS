import customtkinter as ctk
import sys
import numpy as np
import pandas as pd
import time
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from API.MassSpec6000 import massSpecProgram
from CAENpy.CAENDesktopHighVoltagePowerSupply import CAENDesktopHighVoltagePowerSupply, OneCAENChannel
from API.PulseGenPy import pulseGenerator

import TopLevelVariables
from _pulseFunctions import pulseFunctions
from _voltageFunctions import voltageFunctions
from _picoscopeFunctions import picoscopeFunctions




class ToplevelWindow(ctk.CTkToplevel):
    """Top Window for error messages"""
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


class ctkApp(pulseFunctions, voltageFunctions, picoscopeFunctions):
    """Main GUI"""
    def __init__(self):
        
        """Theme Preferences"""
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme('dark-blue')

        self.toplevel_window = None  #variable for error window

        global mass_calibration

        """Definitions for Setting up Main GUI"""
        self.root = ctk.CTk()
        self.root.protocol("WM_DELETE_WINDOW", self.closing)  # Closing GUI Behavior
        self.root.after(0, lambda:self.root.state('zoomed'))  # Maximize the window
        self.root.geometry("1200x400+200x200")
        self.root.title("Mass Spectrometer Controller")
        self.root.update()


        """Most of below is GUI definitions"""

        # Frame for the Uncalibrated graph
        self.frame = ctk.CTkFrame(master=self.root,
                                  height= self.root.winfo_height()*0.3,
                                  width = self.root.winfo_width()*0.45,
                                  fg_color="#020202")
        self.frame.place(relx=0.35, rely=0.025)


        # Frame for calibrated Graph
        self.frame2 = ctk.CTkFrame(master=self.root,
                                  height= self.root.winfo_height()*0.3,
                                  width = self.root.winfo_width()*0.45,
                                  fg_color="#020202")
        self.frame2.place(relx=0.35, rely=0.52)


        # Frames for Voltage and Pulse Values (to look nice)
        self.frameTop = ctk.CTkFrame(master=self.root,
                                  height= self.root.winfo_height()*0.5,
                                  width = self.root.winfo_width()*0.32,
                                  fg_color="transparent",
                                  border_color="#000000",
                                  border_width=4)
        self.frameTop.place(relx=0.002, rely=0.01)

        # Frame for Slider and Save Stuff
        self.frameBot = ctk.CTkFrame(master=self.root,
                                  height= self.root.winfo_height()*0.45,
                                  width = self.root.winfo_width()*0.32,
                                  fg_color="transparent",
                                  border_color="#000000",
                                  border_width=4)
        self.frameBot.place(relx=0.002, rely=0.54)



        """Voltage Labels and Boxes"""
        # Cone 1 voltage
        self.voltage1Text = ctk.CTkLabel(master=self.root,
                                          width=100,
                                          height=25,
                                          text='Cone 1(V)',
                                          fg_color='transparent')
        self.voltage1Text.place(relx=0.01, rely=0.02)

        self.voltage1Input =  ctk.CTkEntry(master=self.root,
                                   placeholder_text=100,
                                   justify='center',
                                   width=100,
                                   height=50,
                                   fg_color="#515151")
        self.voltage1Input.insert(0,str(5))
        self.voltage1Input.place(relx=0.01,rely=0.05)

        #Cone 2 Voltage
        self.voltage2Text = ctk.CTkLabel(master=self.root,
                                          width=100,
                                          height=25,
                                          text = 'Lens 1 (V)',
                                          fg_color='transparent')
        self.voltage2Text.place(relx=0.08, rely=0.02)

        self.voltage2Input =  ctk.CTkEntry(master=self.root,
                                   placeholder_text=100,
                                   justify='center',
                                   width=100,
                                   height=50,
                                   fg_color="#515151")
        self.voltage2Input.insert(0,str(5))
        self.voltage2Input.place(relx=0.08,rely=0.05)

        #3
        self.voltage3Text = ctk.CTkLabel(master=self.root,
                                          width=100,
                                          height=25,
                                          text='PDL High Voltage (V)',
                                          fg_color='transparent')
        self.voltage3Text.place(relx=0.15, rely=0.02)

        self.voltage3Input =  ctk.CTkEntry(master=self.root,
                                   placeholder_text=100,
                                   justify='center',
                                   width=100,
                                   height=50,
                                   fg_color="#515151")
        self.voltage3Input.insert(0,str(5))
        self.voltage3Input.place(relx=0.15,rely=0.05)

        #4
        self.voltage4Text = ctk.CTkLabel(master=self.root,
                                          width=100,
                                          height=25,
                                          text='Spec HV (V)',
                                          fg_color='transparent')
        self.voltage4Text.place(relx=0.22, rely=0.02)

        self.voltage4Input =  ctk.CTkEntry(master=self.root,
                                   placeholder_text=100,
                                   justify='center',
                                   width=100,
                                   height=50,
                                   fg_color="#515151")
        self.voltage4Input.insert(0,str(5))
        self.voltage4Input.place(relx=0.22,rely=0.05)


        #MCP Voltage
        self.MCPText = ctk.CTkLabel(master=self.root,
                                          width=100,
                                          height=25,
                                          text='MCP Negative (V)',
                                          fg_color='transparent')
        self.MCPText.place(relx=0.01, rely=0.11)

        self.MCPInput =  ctk.CTkEntry(master=self.root,
                                   placeholder_text=100,
                                   justify='center',
                                   width=100,
                                   height=50,
                                   fg_color="#515151")
        self.MCPInput.insert(0,str(5))
        self.MCPInput.place(relx=0.01,rely=0.14)


        # From file or not checkbox
        self.checkbox = ctk.CTkCheckBox(master=self.root, 
                                        text="From File", 
                                        command=None)
        self.checkbox.place(relx=0.25, rely = 0.12)

        '''Pulse Labels and Boxes'''
        # Pulse Width
        self.pulseWidthText = ctk.CTkLabel(master=self.root,
                                          width=150,
                                          height=25,
                                          text='Pulse Width (ms)',
                                          fg_color='transparent')
        self.pulseWidthText.place(relx=0.01, rely=0.2)

        self.pulseWidthInput =  ctk.CTkEntry(master=self.root,
                                   placeholder_text=100,
                                   justify='center',
                                   width=150,
                                   height=50,
                                   fg_color="#515151")
        self.pulseWidthInput.insert(0,str(0.003))
        self.pulseWidthInput.place(relx=0.01,rely=0.23)

        # Pulse Delay
        self.pulseDelayText = ctk.CTkLabel(master=self.root,
                                          width=150,
                                          height=25,
                                          text='Pulse Delay (ms)',
                                          fg_color='transparent')
        self.pulseDelayText.place(relx=0.12, rely=0.2)

        self.pulseDelayInput =  ctk.CTkEntry(master=self.root,
                                   placeholder_text=100,
                                   justify='center',
                                   width=150,
                                   height=50,
                                   fg_color="#515151")
        self.pulseDelayInput.insert(0,str(500))
        self.pulseDelayInput.place(relx=0.12,rely=0.23)



        """Bottom Frame"""
        # Theoretical Value
        mass_calibration = TopLevelVariables.pre_factor/np.sqrt(float(self.voltage1Input.get()))
        self.inputText = ctk.CTkLabel(master=self.root,
                                          width=200,
                                          height=25,
                                          text=f'Theoretical Value : NA',
                                          fg_color='transparent')
        self.inputText.place(relx=0.01, rely=0.75)

        #slider
        self.slider = ctk.CTkSlider(master=self.root,
                                    width=400,
                                    height=20,
                                    from_=1,
                                    to=10,
                                    number_of_steps=1000,
                                    command=self.update_surface,
                                    state='disabled')  # this command is the function it does
        self.slider.set(mass_calibration)
        self.slider.place(relx= 0.01,rely=0.8) 

        # Mass Calibration Textbox
        self.input =  ctk.CTkEntry(master=self.root,
                                   placeholder_text=100,
                                   justify='center',
                                   width=200,
                                   height=50,
                                   fg_color="#515151")
        self.input.insert(0,'NA')
        self.input.place(relx=0.01,rely=0.83)



        """Buttons"""

        #Activate the HV
        self.activate = ctk.CTkButton(master = self.root,
                               text="Set Up Voltages",
                               width=150,
                               height=50,
                               command=self.setupRest)  # updates with the button
        self.activate.place(relx=0.04,rely=0.32)

        # Pulse Button
        self.pulseButton = ctk.CTkButton(master = self.root,
                               text="Send Pulse",
                               width=150,
                               height=50,
                               command=self.setupPulse)  # updates with the button
        self.pulseButton.place(relx=0.04,rely=0.4) 

        # Get Data from Picoscope
        self.picoscope = ctk.CTkButton(master = self.root,
                               text="Setup Picoscope",
                               width=150,
                               height=50,
                               command=self.get_data)  # updates with the button
        self.picoscope.place(relx=0.16,rely=0.32)

        # Pulse and GetData from Picoscope
        self.dataCollection = ctk.CTkButton(master = self.root,
                               text="Get Data",
                               width=150,
                               height=50,
                               command=self.data_collection,
                               state='disabled',
                               fg_color='green')  # updates with the button
        self.dataCollection.place(relx=0.16,rely=0.4)

        # Update Graph
        self.button = ctk.CTkButton(master = self.root,
                               text="Update Graph",
                               width=200,
                               height=50,
                               command=self.update_window,
                               state='disabled')  # updates with the button
        self.button.place(relx=0.15,rely=0.83)



        # saveFile Name
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





        """Monitoring labels + Kill Button"""

        # Kill Button
        self.killButton = ctk.CTkButton(master=self.root,
                                        text = 'Kill',
                                        width = 80,
                                        height = 25,
                                        command=self.kill,
                                        fg_color='#8b0000',
                                        state='normal')
        self.killButton.place(relx = 0.25, rely=0.56)

        #Monitoring Labels
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
        


        """Setup for Monitor looping and overall looping"""
        self.root.after(0, self.looping)  # updates in time

        mass_calibration = TopLevelVariables.pre_factor/np.sqrt(float(self.voltage1Input.get()))
        self.root.mainloop()


    def closing(self):
        """When closing the gui, it shows error if not killed"""
        # global TopLevelVariables.gen
        if isinstance(TopLevelVariables.caen, CAENDesktopHighVoltagePowerSupply):
            self.open_toplevel(message="Kill the HV and PulseGenFirst")
        # time.sleep(3)
        else:
            sys.exit()


    def open_toplevel(self, message, buttonText='OK'):
        """Error message opening"""
        if self.toplevel_window is None or not self.toplevel_window.winfo_exists():
            self.toplevel_window = ToplevelWindow()  # create window if its None or destroyed
            self.toplevel_window.label.configure(text=message)
            self.toplevel_window.button.configure(text=buttonText)
            self.toplevel_window.after(10, self.toplevel_window.lift)
        else:
            self.toplevel_window.focus()  # if window exists focus it

if __name__ == "__main__":        
    CTK_Window = ctkApp()