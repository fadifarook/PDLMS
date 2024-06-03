import customtkinter as ctk
import sys
import numpy as np
import pandas as pd
import time
import os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from API.MassSpec6000 import massSpecProgram
from CAENpy.CAENDesktopHighVoltagePowerSupply import CAENDesktopHighVoltagePowerSupply, OneCAENChannel
from API.PulseGenPy import pulseGenerator

import TopLevelVariables




# Find and remove infinity signs
# TODO: value is just replaced by 10 V
infty = "\u221E"
neginfty = "-\u221E"

def convert(times, volt, mass_calibration):
    """Converts Data from time-intensity mass charge values"""

    times_us = np.asarray(times, dtype='float64')
    nparr = np.asarray(volt, dtype='float64')
    nparr[nparr == neginfty] = -10  # convert the infinities and neginfinities to +-10
    nparr[nparr == infty] = 10
    mVs = np.asarray(nparr, dtype='float64')
    # mVs = mVs * -1

    mVs = mVs * -1    # this CAUSES ISSUES FOR SOME REASON?
    mVs = mVs[times_us >=0]  # take the positive times
    times_us = times_us[times_us >= 0]
    mzs = (times_us/mass_calibration)**2  # conversion from book
    cnts_temp = (mVs)
    relMax = max(cnts_temp)
    cnts = cnts_temp/relMax

    return mzs, cnts


class picoscopeFunctions:
    

    def get_data(self):
        """Set up picoscope and Wait for a Trigger"""
        global x, y


        if TopLevelVariables.voltageSupplyOpened or self.checkbox.get() or (not TopLevelVariables.picoOpened):
            if not self.checkbox.get():
                try:
                    # run the picoscope software, get the time and intensity respectively
                    if TopLevelVariables.picoOpened:
                        x, y, TopLevelVariables.handle = massSpecProgram(waittime=60000, opened=TopLevelVariables.picoOpened, chandle=TopLevelVariables.handle)
                    
                    else:
                        x, y, TopLevelVariables.handle = massSpecProgram(waittime=1000, opened=TopLevelVariables.picoOpened, chandle=TopLevelVariables.handle)
                        
                    TopLevelVariables.picoOpened = True   # change the waittime when actually doing things, time in us
                    # x = 2

                except:
                    self.open_toplevel(message="Can't Find Picoscope")
                    return None

            # If we are testing use the file provided else piscoscope
            else:
                TopLevelVariables.testFile = ctk.filedialog.askopenfilename()

                # data = np.loadtxt(TopLevelVariables.testFile, delimiter=',', skiprows=3, usecols=(0, 1))

                data = np.genfromtxt(TopLevelVariables.testFile, delimiter=',', skip_header=3, usecols=(0, 1), missing_values=neginfty, 
                                     filling_values=-2, dtype=float)
                
                x, y = np.rollaxis(data, axis=1)


            self.picoscope.configure(text='Picoscope Connected')
            self.picoscope.configure(state='disabled')

            self.dataCollection.configure(state='normal')

            # Enable all the tools
            self.button.configure(state='normal')
            self.slider.configure(state='normal')

            self.update_window()  #removed since we split picoscope from software

        else:
            # Error if voltage supply is not open
            self.open_toplevel(message="You haven't started the Voltage Supply or Pulse Generator")




    def update_window(self):
        """ If Update graph is pressed (changed calibration) or when obtaining first result"""
        mass_calibration = TopLevelVariables.pre_factor/np.sqrt(float(self.voltage1Input.get()))
        self.inputText.configure(text='Theoretical Value: {}'.format(round(mass_calibration, 4)))

        if TopLevelVariables.first_time:
            # Get the calibration factor
            # mass_calibration = TopLevelVariables.pre_factor/np.sqrt(float(self.voltage1Input.get()))
            self.input.delete(0, 100)
            self.input.insert(0,round(mass_calibration, 4))
            # self.inputText.delete(0.0, 100.0)
            # self.inputText.insert(0.0, 'Theoretical Value:{}'.format(round(mass_calibration, 4)))
            # self.inputText.configure(text='Theoretical Value:{}'.format(round(mass_calibration, 4)))
            TopLevelVariables.first_time = 0
        else:
            mass_calibration = float(self.input.get())
        

        # Uncalibrated plotting
        fig1, ax1 = plt.subplots()
        fig1.set_size_inches(11, 5)
        ax1.plot(x, y, '#000000')
        ax1.set_xlabel(r'time ($\mu s$)')
        ax1.set_ylabel('Intensity (V)')
        ax1.set_title('Before Conversion')
        canvas1 = FigureCanvasTkAgg(fig1, master=self.root)
        canvas1.draw()
        canvas1.get_tk_widget().place(relx=0.35, rely=0.025)


        # put the number into the slider
        self.slider.set(float(self.input.get()))

        # Calibrated Plotting
        fig, ax = plt.subplots()
        fig.set_size_inches(11,5)
        x_converted, y_converted = convert(x, y, self.slider.get())
        ax.plot(x_converted, y_converted, color='#000000')
        ax.set_xlabel('Mass/charge')
        ax.set_ylabel('Counts (relative)')
        ax.set_title('After Conversion')
        # fig.subplots_adjust(left=0, right=1, bottom=0, top=1, wspace=0, hspace=0)
        canvas = FigureCanvasTkAgg(fig,master=self.root)
        canvas.draw()
        canvas.get_tk_widget().place(relx=0.35, rely=0.52)
        self.root.update()



        
    def update_surface(self,other):
        """Adjust calibrated plot while moving slider"""

        fig, ax = plt.subplots()
        fig.set_size_inches(11,5)
        x_converted, y_converted = convert(x, y, self.slider.get())
        ax.plot(x_converted, y_converted, color='#000000')
        ax.set_xlabel('Mass/charge')
        ax.set_ylabel('Counts (relative)')
        ax.set_title('After Conversion')
        # fig.subplots_adjust(left=0, right=1, bottom=0, top=1, wspace=0, hspace=0)
        canvas = FigureCanvasTkAgg(fig,master=self.root)
        canvas.draw()
        canvas.get_tk_widget().place(relx=0.35, rely=0.52)
        self.input.delete(0, 100)
        self.input.insert(0,self.slider.get())
        self.root.update()


    def save(self):
        """Save uncalibrated and Calibrated data into a textfile"""

        if not self.saveInput.get():
            self.saveInput.configure(placeholder_text='File Name Not Entered')

        else:
            global x,y
            x_converted, y_converted = convert(x, y, self.slider.get())

            TopLevelVariables.saveFolder = f'{TopLevelVariables.saveFolder}\\{time.strftime("%d%b%Y", time.gmtime())}'

            if not os.path.exists(TopLevelVariables.saveFolder):
                os.mkdir(TopLevelVariables.saveFolder)

            # Save all in a txt file
            with open(f'{TopLevelVariables.saveFolder}\\{self.saveInput.get()}.txt',"w") as f:
                f.write('unconvertedTime, unconvertedIntensity, convertedMZ, convertedIntensity\n')
                for (a, b, c, d) in zip(x, y, x_converted, y_converted):
                    f.write("{0},{1},{2},{3}\n".format(a, b, c, d))


            # Save Plots as well

            fig, axs = plt.subplots(2)
            fig.suptitle(f'{self.saveInput.get()}')

            axs[0].plot(x, y, '#000000')
            axs[0].set_xlabel(r'time ($\mu s$)')
            axs[0].set_ylabel('Intensity (V)')
            axs[0].set_title('Before Conversion')

            axs[1].plot(x_converted, y_converted, color='#000000')
            axs[1].set_xlabel('Mass/charge')
            axs[1].set_ylabel('Counts (relative)')
            axs[1].set_title('After Conversion')

            fig.tight_layout(pad=1.0)

            fig.savefig(f'{TopLevelVariables.saveFolder}\\{self.saveInput.get()}.png')

            self.saveButton.configure(text='Saved!')

        self.root.update()

