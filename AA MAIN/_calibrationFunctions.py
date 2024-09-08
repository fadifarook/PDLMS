import customtkinter as ctk
import sys
import numpy as np
import pandas as pd
import time
import os
import matplotlib
matplotlib.use('Agg')
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
    """Helper function that waits until voltage is reached, stops if it takes too long (more than one minute)"""
    mustend = time.time() + timeout
    while time.time() < mustend:
        if (voltageReference - 3) < float(voltageSource.V_mon[:-1]) < (voltageReference + 3): 
            return True
        time.sleep(period)
    return False

class calibrationFunctions:

    def averageOneVoltage(self, numOfData = 50, specifiedVoltage=2):
        """Take numOfData measurements at a specified voltage (only used for saveFile name) and return averaged maximum of the data"""
        
        i = 0

        while i < numOfData:
            # Shoot laser and get oscilloscope data
            self.runPulse()  # laser
            TopLevelVariables.x, TopLevelVariables.y, TopLevelVariables.handle = massSpecProgram(waittime=60000, opened=TopLevelVariables.picoOpened, chandle=TopLevelVariables.handle)  # get data

            try:
                self.savecalibration(voltageValue=specifiedVoltage, number=i, x_array=TopLevelVariables.x, y_array=TopLevelVariables.y)  # Save the data
            except:
                print('Failed save')

            if i ==0:
                addedY = np.array(TopLevelVariables.y)
            else:
                addedY += np.array(TopLevelVariables.y)

            # Halfway through, show an example plot
            if i == numOfData//2:
                self.update_window()
                time.sleep(0.2)

            time.sleep(0.03)
            i += 1

        # Average all measurements and save
        averagedY = np.array(addedY)/numOfData
        self.savecalibration(specifiedVoltage, number='avg', x_array=TopLevelVariables.x ,y_array=averagedY)

        # Flip data since it is usually negative
        positiveData = -1 * averagedY

        # Find maximum
        maxIndex = (np.argmax(positiveData),)

        # Ignore the data if the intensity is lower than 100mV
        if positiveData[maxIndex] < 100:
            return 3

        mainWidth = peak_widths(positiveData, maxIndex, rel_height=0.5)  # Finds FWWHM

        modified = [x * 20 / 6248 for x in mainWidth] # peak_widths returns the width in terms of number of indexes. Convert that into microsecond

        return modified[0][0]  # returns the width 

        # return np.min(averagedY)  # minimum since its an inverted thing

    # def calibrateVoltage(self, voltageList, averageMaxList):
    #     """REPLACED BY BAYESIAN OPTIMIZATION 
        
    #     interpolate averageList containing the average maximum of data of all voltages.
    #     Then find the maximum of this new list, and corresponding voltage"""
        
    #     voltageList = np.array(voltageList)
    #     averageMaxList = np.array(averageMaxList)

    #     interpolateFunction = scipy.interpolate.interp1d(voltageList, averageMaxList)

    #     x = np.linspace(voltageList[0], voltageList[-1], 2000)
    #     y = interpolateFunction(x)

    #     optimizedVoltage = x[np.argmin(y)]  # since its all negative

    #     # plt.plot(voltageList,averageMaxList, '.')
    #     # plt.plot(x, y, '--')
    #     # plt.axvline(optimizedVoltage,color='g')
    #     # plt.show()

    #     plt.switch_backend('agg')
    #     TopLevelVariables.fig1.clf()
    #     ax1 = TopLevelVariables.fig1.add_subplot(1,1, 1)        
    #     ax1.plot(voltageList,averageMaxList, '.')
    #     ax1.plot(x, y, '--')
    #     ax1.axvline(optimizedVoltage,color='g')
    #     ax1.set_xlabel('Average Maximum Voltage (mV)')
    #     ax1.set_ylabel('PDL Voltages (V)')
    #     ax1.set_title('Interpolated Graph')
    #     TopLevelVariables.canvas1.draw()

    #     return optimizedVoltage

    # def calibrationFunction(self, voltageAddition = 5, startVoltage=5, endVoltage = 30):
    #     """ REPLACED BY BAYESIAN OPTIMIZATION
        
    #     Increase the voltage by voltageAddition, find the averagemax of each data, put them all into a list,
    #     get the maximum of all this data and corresponding calibrated voltage"""

    #     if (not TopLevelVariables.picoOpened) or (TopLevelVariables.gen == 0) or (not TopLevelVariables.voltageSupplyOpened):
    #         self.open_toplevel(message="Start Picoscope, Pulse Gen and Voltage Supply")
    #         return None
        
    #     if float(self.pulseDelayInput.get()) < 10:
    #         self.open_toplevel(message="Delay too low. Picoscope won't be triggered.")
    #         return None
        
        
    #     startVoltage = float(self.startCalibrationInput.get())
    #     voltageAddition = float(self.stepCalibrationInput.get())
    #     endVoltage= float(self.stopCalibrationInput.get())
    #     numberOfData = int(self.collectionNumberInput.get())


    #     currentVoltage = startVoltage
    #     currentMax = 0
    #     maxVoltageList = []
    #     totalTime = 0.5 * 50 * (endVoltage - startVoltage) / voltageAddition

    #     totalTime = 6.5 * (endVoltage - startVoltage) / voltageAddition  * numberOfData/100

    #     while currentVoltage < endVoltage:
    #         # print(list(range(startVoltage, 30, voltageAddition)))

    #         status = (currentVoltage-startVoltage) / (endVoltage - startVoltage)
    #         timeLeft = totalTime * (1 - status) / 60
    #         self.calibrationText.configure(text = f'Time Left: {round(timeLeft, 2)} min')

    #         self.progressbar.set(status)

    #         TopLevelVariables.HV2.set(PAR='VSET',VAL=currentVoltage)
    #         continueFlag = wait_until(voltageSource=TopLevelVariables.HV2, voltageReference=currentVoltage)

    #         if not continueFlag:
    #             self.open_toplevel(message="The voltage hasn't changed in a minute")
    #             return None
            
    #         start =time.time()
    #         currentMax = self.averageOneVoltage(numOfData=numberOfData, specifiedVoltage=currentVoltage)
    #         print(time.time() - start)
    #         # print(currentMax)
            
    #         maxVoltageList.append(currentMax)

    #         currentVoltage += voltageAddition

    #         self.open_toplevel(message="Change Position")
    #         time.sleep(30)

    #     calibratedVoltage = self.calibrateVoltage(voltageList=list(np.arange(startVoltage, endVoltage, voltageAddition)), averageMaxList=maxVoltageList)
    #     self.calibrationText.configure(text = f'Calibrated Voltage: {round(calibratedVoltage, 2)}')
    #     self.progressbar.set(1)

    #     # print("Desired Voltage is ",calibratedVoltage)
    #     # return None



    def calibrationFunctionBO(self, parameter1Voltage = 2800, parameter2Voltage = 2650):
        """Black Box Function for Bayesian Optimization. Sets the desired voltage and returns FWHM of the highest peak for resolution"""
        
        if (not TopLevelVariables.picoOpened) or (TopLevelVariables.gen == 0) or (not TopLevelVariables.voltageSupplyOpened):
            self.open_toplevel(message="Start Picoscope, Pulse Gen and Voltage Supply")
            return None
        
        if float(self.pulseDelayInput.get()) < 10:
            self.open_toplevel(message="Delay too low. Picoscope won't be triggered.")
            return None        
        
        numberOfData = int(self.collectionNumberInput.get())

        # Don't take floats as voltage
        parameter2Voltage = int(parameter2Voltage)
        parameter1Voltage = int(parameter1Voltage)

        tempDict = {"Cone 1": TopLevelVariables.HV0, "Lens 1": TopLevelVariables.HV1, "Deflection Voltage": TopLevelVariables.HV2}
        parameter1Object = tempDict[self.parameter1ComboBox.get()]
        parameter2Object = tempDict[self.parameter2ComboBox.get()]


        # Set the voltages and wait until it is reached before shooting laser
        parameter1Object.set(PAR='VSET',VAL=parameter1Voltage)
        parameter2Object.set(PAR='VSET',VAL=parameter2Voltage)

        continueFlag = wait_until(voltageSource=parameter2Object, voltageReference=parameter2Voltage)

        if not continueFlag:
            self.open_toplevel(message="The parameter 2 voltage hasn't changed in a minute")
            return None
        
        continueFlag = wait_until(voltageSource=parameter1Object, voltageReference=parameter1Voltage)

        if not continueFlag:
            self.open_toplevel(message="The parameter 1 voltage hasn't changed in a minute")
            return None

        # start =time.time()
        savefileName = str(parameter1Voltage) + str(parameter2Voltage)
        currentMin = self.averageOneVoltage(numOfData=numberOfData, specifiedVoltage=savefileName)
        # print(time.time() - start)

       # 10s is given to change the position of the sample
        time.sleep(10)

        return currentMin * (-1)  # Bayesian optimization maximixes the value, while we are looking for minimum. minimum in positive = maximum in negative

    
    def bayesianOptimizationFunction(self):
        """Main optimizer function. Gets the desired start and stop voltages from the inputs, sets the number of measurements, does the bayesian optimization,
        and plots acontour plot of the predicted resolution"""
        
        parameter1Start = float(self.parameter1StartInput.get())
        parameter1End = float(self.parameter1StopInput.get())

        parameter2Start = float(self.parameter2StartInput.get())
        parameter2End = float(self.parameter2StopInput.get())

        # Doesn't allow one variable BO only (since contour plot)
        if parameter1Start == parameter1End or parameter2Start == parameter2End:
            self.open_toplevel(message="Start and Stop shouldn't be equal")
            return None
        
        # Bounded region of parameter space
        pbounds = {'parameter1Voltage': (parameter1Start, parameter1End), 'parameter2Voltage': (parameter2Start, parameter2End)}

        optimizer = BayesianOptimization(f=self.calibrationFunctionBO, pbounds=pbounds, random_state=None)

        randomPoints = int(self.randomMeasurementsInput.get())
        bayesianPoints = int(self.bayesianMeasurementsInput.get())

        # runs the optimizer. init_points is the random points. n_iter is the points that are discovered through the algorithn. 
        # Utility function (expected improvement) is the aquisition function that finds new points
        optimizer.maximize(init_points=randomPoints, n_iter=bayesianPoints, acquisition_function = UtilityFunction(kind='ei',xi=0.0))

        print(optimizer.max)


        # Contour plot for visualizing the resolution with voltages
        x = np.array([[res["params"]["parameter1Voltage"]] for res in optimizer.res])
        y = np.array([[res["params"]["parameter2Voltage"]] for res in optimizer.res])
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
        ax1.set_xlabel('Parameter 1 Voltage')
        ax1.set_ylabel('Paremeter 2 Voltage')
        ax1.set_title('Triangular Contour Plot')
        TopLevelVariables.canvas1.draw()


    def threadCalibrationFunction(self):
        """Starts the calibration in a thread, otherwise it would pause the whole GUI while doing all this"""
        # TopLevelVariables.threadFunc = threading.Thread(target=self.calibrationFunction)
        TopLevelVariables.threadFunc = threading.Thread(target=self.bayesianOptimizationFunction)
        TopLevelVariables.threadFunc.start()
        # self.calibrationFunction()

    
    def savecalibration(self, voltageValue, number, x_array=TopLevelVariables.x, y_array=TopLevelVariables.y):
        """Saves data in <Today's Date>/Calibration/voltageValue/<number>.txt"""
        calibrationFolder = f'{TopLevelVariables.saveFolder}\\Calibration'

        if not os.path.exists(TopLevelVariables.saveFolder):
            os.mkdir(TopLevelVariables.saveFolder)  # makes savefolder

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