import TopLevelVariables
from API.PulseGenPy import pulseGenerator
import time
import threading
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib._pylab_helpers as pylhelp

class pulseFunctions:

    def setupPulse(self):
        """Check if Pulse Generator is connected and setup"""

        # Try to connect to Pulse Generator
        try:
            self.pulse()
        except Exception:
            # Error Message
            self.open_toplevel(message="Can't Find Pulse Generator")
            return None
        
        self.setupPulseButton.configure(text='Setup Pulse again')
        self.pulseButton.configure(state='normal')

        # Displays the settings on gui
        self.LabelWidth.delete(0.0, 100.0)
        self.LabelDelay.delete(0.0, 100.0)
        self.LabelWidth.insert(0.0, f'Pulse Width: {self.pulseWidthInput.get()}')
        self.LabelDelay.insert(0.0, f'Pulse Delay: {self.pulseDelayInput.get()}')

    
    def pulse(self):
        """connects to pulse generator and changes setting to a single pulse of given width and delay"""
        if TopLevelVariables.gen == 0:
            TopLevelVariables.gen = pulseGenerator(resourceName = f'ASRL{TopLevelVariables.pulseCOM}::INSTR')

        
        TopLevelVariables.gen.width = float(self.pulseWidthInput.get())*1e-3
        TopLevelVariables.gen.mode = 'SING'  # single shot
        TopLevelVariables.gen.delay = float(self.pulseDelayInput.get())*1e-3
        TopLevelVariables.gen.trigger = 'TRIG'  # disable a trigger for pulse generator

        TopLevelVariables.gen.setup()  # API function

        # TopLevelVariables.gen.start_trigger()

    def data_collection(self):
        """Sends out a pulse and gets data"""

        if float(self.pulseDelayInput.get()) < 10:
            self.open_toplevel(message="Delay too low. Picoscope won't be triggered.")
            return None

        if not TopLevelVariables.gen and not self.checkbox.get():
            self.open_toplevel(message = 'Pulse Generator is off')
            return None

        if not TopLevelVariables.repeat:
            """Sends a pulse and make picoscope fair for the trigger."""
            start = time.time()
            if not self.checkbox.get():
                self.runPulse()
            self.setup_picoscope()
            print(time.time() - start)

        else:
            """Old code, not useful right now"""
            wait = 1/int(self.repeated.get()[0:-2])
            TopLevelVariables.threadFunc = threading.Thread(target=self.threadRepeating, args=(wait,))
            TopLevelVariables.threadFunc.start()

    def runPulse(self):
        """Sends a Pulse"""
        # TopLevelVariables.gen.run()
        self.threadNewLaser()

    def newLaser(self):
        """Opens the triggered pulseGen for 0.011 seconds. Should be run in parallel"""
        start = time.time()
        TopLevelVariables.gen.run()
        time.sleep(0.011)
        TopLevelVariables.gen.quickStop()
        print(time.time() - start)

    def threadNewLaser(self):
        """Threads the newLaser function"""
        TopLevelVariables.threadFunc = threading.Thread(target=self.newLaser)
        TopLevelVariables.threadFunc.start()
        

    def repeat(self, choice):
        """Old Code. Not in use. For repeated shots"""

        if choice=="Single Shot":
            TopLevelVariables.repeat = False
            self.repeated.configure(values = ["Single Shot", "1Hz", "2Hz", "3Hz", "5Hz", "10Hz"])
            # print(1)
        else:
            TopLevelVariables.repeat = True
            self.repeated.configure(values = ["Single Shot", choice])
            # print(0)
        # print(choice[0:-2])

    def threadRepeating(self, waittime=0.5):
        """Old code, not in use. Parallel running of repeated shots"""

        TopLevelVariables.gen.width = float(self.pulseWidthInput.get())*1e-3
        TopLevelVariables.gen.mode = 'SING'
        TopLevelVariables.gen.delay = float(self.pulseDelayInput.get())*1e-3
        TopLevelVariables.gen.trigger = 'DIS'

        TopLevelVariables.gen.setup()

        while TopLevelVariables.repeat:
            start = time.time()
            self.runPulse()
            self.setup_picoscope()
            time.sleep(waittime)
            # plt.close('all')
            pylhelp.Gcf().destroy_all()

            print(time.time() - start)
        return
            


# print(time.strftime("%d%b%Y", time.gmtime()))