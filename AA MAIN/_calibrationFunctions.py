import customtkinter as ctk
import sys
import numpy as np
import pandas as pd
import time
import os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import scipy.interpolate
from API.MassSpec6000 import massSpecProgram
from CAENpy.CAENDesktopHighVoltagePowerSupply import CAENDesktopHighVoltagePowerSupply, OneCAENChannel
from API.PulseGenPy import pulseGenerator

from matplotlib.ticker import AutoMinorLocator, MultipleLocator
import matplotlib.backends.backend_tkagg as tkagg
import matplotlib._pylab_helpers as pylhelp

import TopLevelVariables
import threading
import scipy

from bayes_opt import BayesianOptimization
from bayes_opt import UtilityFunction
from scipy.signal import peak_widths


def wait_until(voltageSource, voltageReference, timeout = 60, period=0.25):
    """Waits until voltage is reached, stops if it takes too long"""
    mustend = time.time() + timeout
    while time.time() < mustend:
        if (voltageReference - 3) < float(voltageSource.V_mon[:-1]) < (voltageReference + 3): 
            return True
        time.sleep(period)
    return False

class calibrationFunctions:

    def averageOneVoltage(self, numOfData = 50, specifiedVoltage=2):
        """Take numOfData measurements at a specified voltage and return averaged maximum of the data"""
        
        i = 0

        while i < numOfData:
            self.runPulse()  # laser
            TopLevelVariables.x, TopLevelVariables.y, TopLevelVariables.handle = massSpecProgram(waittime=60000, opened=TopLevelVariables.picoOpened, chandle=TopLevelVariables.handle)  # get data
            # print(TopLevelVariables.x, TopLevelVariables.y)
            try:
                self.savecalibration(voltageValue=specifiedVoltage, number=i, x_array=TopLevelVariables.x, y_array=TopLevelVariables.y)
            except:
                print('Failed')

            if i ==0:
                addedY = np.array(TopLevelVariables.y)
            else:
                addedY += np.array(TopLevelVariables.y)

            if i == numOfData//2:
                # self.update_window()
                time.sleep(0.2)

            # self.update_window() # shows on screen
            # print(time.time() - start)
            time.sleep(0.03)
            i += 1

        averagedY = np.array(addedY)/numOfData
        self.savecalibration(specifiedVoltage, number='avg', x_array=TopLevelVariables.x ,y_array=averagedY)


        positiveData = -1 * averagedY

        maxIndex = (np.argmax(positiveData),)

        if positiveData[maxIndex] < 100:
            return 3

        mainWidth = peak_widths(positiveData, maxIndex, rel_height=0.5)  # Finds FWWHM

        modified = [x * 20 / 6248 for x in mainWidth]

        return modified[0][0]  # returns the width 

        # return np.min(averagedY)  # minimum since its an inverted thing

    def calibrateVoltage(self, voltageList, averageMaxList):
        """REPLACED BY BAYESIAN OPTIMIZATION 
        
        interpolate averageList containing the average maximum of data of all voltages.
        Then find the maximum of this new list, and corresponding voltage"""
        
        voltageList = np.array(voltageList)
        averageMaxList = np.array(averageMaxList)

        interpolateFunction = scipy.interpolate.interp1d(voltageList, averageMaxList)

        x = np.linspace(voltageList[0], voltageList[-1], 2000)
        y = interpolateFunction(x)

        optimizedVoltage = x[np.argmin(y)]  # since its all negative

        # plt.plot(voltageList,averageMaxList, '.')
        # plt.plot(x, y, '--')
        # plt.axvline(optimizedVoltage,color='g')
        # plt.show()

        plt.switch_backend('agg')
        TopLevelVariables.fig1.clf()
        ax1 = TopLevelVariables.fig1.add_subplot(1,1, 1)        
        ax1.plot(voltageList,averageMaxList, '.')
        ax1.plot(x, y, '--')
        ax1.axvline(optimizedVoltage,color='g')
        ax1.set_xlabel('Average Maximum Voltage (mV)')
        ax1.set_ylabel('PDL Voltages (V)')
        ax1.set_title('Interpolated Graph')
        TopLevelVariables.canvas1.draw()

        return optimizedVoltage

    def calibrationFunction(self, voltageAddition = 5, startVoltage=5, endVoltage = 30):
        """ REPLACED BY BAYESIAN OPTIMIZATION
        
        Increase the voltage by voltageAddition, find the averagemax of each data, put them all into a list,
        get the maximum of all this data and corresponding calibrated voltage"""

        if (not TopLevelVariables.picoOpened) or (TopLevelVariables.gen == 0) or (not TopLevelVariables.voltageSupplyOpened):
            self.open_toplevel(message="Start Picoscope, Pulse Gen and Voltage Supply")
            return None
        
        if float(self.pulseDelayInput.get()) < 10:
            self.open_toplevel(message="Delay too low. Picoscope won't be triggered.")
            return None
        
        
        startVoltage = float(self.startCalibrationInput.get())
        voltageAddition = float(self.stepCalibrationInput.get())
        endVoltage= float(self.stopCalibrationInput.get())
        numberOfData = int(self.collectionNumberInput.get())


        currentVoltage = startVoltage
        currentMax = 0
        maxVoltageList = []
        totalTime = 0.5 * 50 * (endVoltage - startVoltage) / voltageAddition

        totalTime = 6.5 * (endVoltage - startVoltage) / voltageAddition  * numberOfData/100

        while currentVoltage < endVoltage:
            # print(list(range(startVoltage, 30, voltageAddition)))

            status = (currentVoltage-startVoltage) / (endVoltage - startVoltage)
            timeLeft = totalTime * (1 - status) / 60
            self.calibrationText.configure(text = f'Time Left: {round(timeLeft, 2)} min')

            self.progressbar.set(status)

            TopLevelVariables.HV2.set(PAR='VSET',VAL=currentVoltage)
            continueFlag = wait_until(voltageSource=TopLevelVariables.HV2, voltageReference=currentVoltage)

            if not continueFlag:
                self.open_toplevel(message="The voltage hasn't changed in a minute")
                return None
            
            start =time.time()
            currentMax = self.averageOneVoltage(numOfData=numberOfData, specifiedVoltage=currentVoltage)
            print(time.time() - start)
            # print(currentMax)
            
            maxVoltageList.append(currentMax)

            currentVoltage += voltageAddition

            self.open_toplevel(message="Change Position")
            time.sleep(30)

        calibratedVoltage = self.calibrateVoltage(voltageList=list(np.arange(startVoltage, endVoltage, voltageAddition)), averageMaxList=maxVoltageList)
        self.calibrationText.configure(text = f'Calibrated Voltage: {round(calibratedVoltage, 2)}')
        self.progressbar.set(1)

        # print("Desired Voltage is ",calibratedVoltage)
        # return None



    def calibrationFunctionBO(self, cone1Voltage = 2800, deflectionVoltage = 2650):
        """Black Box Function for Bayesian Optimization. Sets the desired voltage and returns the maximum voltage value received
        (OR FWHM of the highest peak for resolution)"""
        
        if (not TopLevelVariables.picoOpened) or (TopLevelVariables.gen == 0) or (not TopLevelVariables.voltageSupplyOpened):
            self.open_toplevel(message="Start Picoscope, Pulse Gen and Voltage Supply")
            return None
        
        if float(self.pulseDelayInput.get()) < 10:
            self.open_toplevel(message="Delay too low. Picoscope won't be triggered.")
            return None        
        
        numberOfData = int(self.collectionNumberInput.get())

        # Don't take random floats as voltage
        deflectionVoltage = int(deflectionVoltage)
        cone1Voltage = int(cone1Voltage)

        TopLevelVariables.HV1.set(PAR='VSET',VAL=deflectionVoltage)  # currently lens
        TopLevelVariables.HV0.set(PAR='VSET',VAL=cone1Voltage)

        continueFlag = wait_until(voltageSource=TopLevelVariables.HV1, voltageReference=deflectionVoltage)

        if not continueFlag:
            self.open_toplevel(message="The deflection voltage hasn't changed in a minute")
            return None
        
        continueFlag = wait_until(voltageSource=TopLevelVariables.HV0, voltageReference=cone1Voltage)

        if not continueFlag:
            self.open_toplevel(message="Cone 1 voltage hasn't changed in a minute")
            return None

        # start =time.time()
        savefileName = str(cone1Voltage) + str(deflectionVoltage)
        currentMin = self.averageOneVoltage(numOfData=numberOfData, specifiedVoltage=savefileName)
        # print(time.time() - start)

        # self.open_toplevel(message="Change Position")
        time.sleep(10)

        return currentMin * (-1)  # Flip it since we want maximum

    
    def bayesianOptimizationFunction(self, cone1Start=3100, cone1End = 3200, deflectionStart = 2000, deflectionEnd = 3300):
        
        # Bounded region of parameter space
        pbounds = {'cone1Voltage': (cone1Start, cone1End), 'deflectionVoltage': (deflectionStart, deflectionEnd)}

        optimizer = BayesianOptimization(f=self.calibrationFunctionBO, pbounds=pbounds, random_state=None)

        optimizer.maximize(init_points=15, n_iter=15, acquisition_function = UtilityFunction(kind='ei',xi=0.0))

        print(optimizer.max)

        x = np.array([[res["params"]["cone1Voltage"]] for res in optimizer.res])
        y = np.array([[res["params"]["deflectionVoltage"]] for res in optimizer.res])
        z = np.array([res["target"] for res in optimizer.res])

        # nicer to read
        x = x.ravel()
        y = y.ravel()

        plt.switch_backend('agg')
        TopLevelVariables.fig1.clf()
        ax1 = TopLevelVariables.fig1.add_subplot(1,1, 1)
        ax1.tricontourf(x, y, z, levels=50, cmap='seismic')
        # ax1.colorbar()  # Show color scale
        ax1.scatter(x, y, color='red')  # Plot original points that were measured
        ax1.set_xlabel('Cone 1 Voltage')
        ax1.set_ylabel('Deflection Voltage')
        ax1.set_title('Triangular Contour Plot')
        TopLevelVariables.canvas1.draw()


    def threadCalibrationFunction(self):
        """Starts the calibration in a thread"""
        # TopLevelVariables.threadFunc = threading.Thread(target=self.calibrationFunction)
        TopLevelVariables.threadFunc = threading.Thread(target=self.bayesianOptimizationFunction)
        TopLevelVariables.threadFunc.start()
        # self.calibrationFunction()

    
    def savecalibration(self, voltageValue, number, x_array=TopLevelVariables.x, y_array=TopLevelVariables.y):
        calibrationFolder = f'{TopLevelVariables.saveFolder}\\Calibration'

        # print(x_array, y_array)

        if not os.path.exists(calibrationFolder):
            os.mkdir(calibrationFolder)
        
        calibrationFolder = f'{calibrationFolder}\\{int(voltageValue)}'

        if not os.path.exists(calibrationFolder):
            os.mkdir(calibrationFolder)

        # Save all in a txt file
        with open(f'{calibrationFolder}\\{number}.txt',"w") as f:
            f.write('unconvertedTime, unconvertedIntensity\n')
            for (a, b) in zip(x_array, y_array):
                f.write("{0},{1}\n".format(a, b))