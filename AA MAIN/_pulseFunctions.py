import TopLevelVariables
from API.PulseGenPy import pulseGenerator
import time

class pulseFunctions:

    def setupPulse(self):
        """Check if Pulse Generator is connected and run it"""

        # Try to connect to Pulse Generator
        try:
            self.pulse()
        except Exception:
            # Error Messaeg
            self.open_toplevel(message="Can't Find Pulse Generator")
            return None
        
        self.pulseButton.configure(text='Send Pulse Again')

    
    def pulse(self):
        """connects to pulse generator and sends a single pulse of appropriate width and delay"""
        if TopLevelVariables.gen == 0:
            TopLevelVariables.gen = pulseGenerator(resourceName = f'ASRL{TopLevelVariables.pulseCOM}::INSTR')

        
        TopLevelVariables.gen.width = float(self.pulseWidthInput.get())*1e-3
        TopLevelVariables.gen.mode = 'SING'
        TopLevelVariables.gen.delay = float(self.pulseDelayInput.get())*1e-3
        TopLevelVariables.gen.trigger = 'DIS'

        TopLevelVariables.gen.run() # sends pulse

    def data_collection(self):
        """Sends out a pulse and gets data"""

        if float(self.pulseDelayInput.get()) < 500:
            self.open_toplevel(message="Delay too low. Picoscope won't be triggered.")

        else:
            self.setupPulse()
            self.get_data()


# print(time.strftime("%d%b%Y", time.gmtime()))