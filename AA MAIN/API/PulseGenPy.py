import pyvisa 
import time

# rm = pyvisa.ResourceManager()
# print(rm.list_resources())


# pulseGen = rm.open_resource('ASRL6::INSTR')
# pulseGen.baud_rate = 38400

# print(pulseGen.query("IDN?"))

# pulseGen.write(":PULSE1:STATE ON")
# pulseGen.write(":PULSE1:WIDT 0.01")
# pulseGen.write(":PULSE0:MODE NORM")
# pulseGen.write(":PULSE0:STATE ON")
# time.sleep(5)
# pulseGen.write(":PULSE0:STATE OFF")


# pulseGen.close()


class pulseGenerator:

    def __init__(self, resourceName = 'ASRL9::INSTR') -> None:  # 5 for my laptop

        try:
            self.pulseGen = pyvisa.ResourceManager().open_resource(resource_name=resourceName)

        except:
            raise ValueError("Can't find the Pulse Generator, check your resource name")

        self.pulseGen.baud_rate = 38400  # from trial and error I found this works , maybe 115200
        
        self.width = 0.01  # in seconds
        self.laser_width = 3e-6
        self.mode = 'NORM'  # among 'NORM', 'SING', 'BURS', 'DCYC'
        
        self.delay = 0
        self.trigger = 'TRIG'  # among 'DIS', 'TRIG'
        self.per = 0.001

    def setup(self):
        self.pulseGen.write("*RST")
        time.sleep(0.1)
        self.switchRestOff()
        time.sleep(0.1)

        delayBelkhe = 50 * 10**(-6)

        self.pulseGen.write(":PULSE1:STATE ON")  # uses channel A = 1: Trigger
        self.pulseGen.write(f":PULSE1:WIDT {self.width}")
        self.pulseGen.write(f":PULSE1:DELAY {self.delay}")

        self.pulseGen.write(":PULSE2:STATE ON")  # uses channel B=2 : Laser
        self.pulseGen.write(f":PULSE2:WIDT {self.laser_width}")
        self.pulseGen.write(f":PULSE2:DELAY {self.delay}")

        # self.pulseGen.write(":PULSE3:STATE ON")  # uses channel C=2 : Belkhe
        # self.pulseGen.write(f":PULSE3:WIDT {self.width}")
        # self.pulseGen.write(f":PULSE3:DELAY {self.delay - delayBelkhe}")

        self.pulseGen.write(f":PULSE0:MODE {self.mode}")
        self.pulseGen.write(f":PULSE0:PER {self.per}")

        time.sleep(0.1)

        if self.trigger == 'TRIG':
            self.pulseGen.write(f":PULSE:TRIG:MODE {self.trigger}")
            self.pulseGen.write(f":PULS:EXT:LEV 1")
            self.pulseGen.write(f":PULS:EXT:EDGE RIS")
        else:
            self.pulseGen.write(f":PULSE:TRIG:MODE {self.trigger}")
            self.pulseGen.write(":PULSE0:EXT:MODE DIS")

    def run(self):
        # self.setup()
        # time.sleep(0.1)  # otherwise its too fast
        self.pulseGen.write(":PULSE0:STATE ON")
        # time.sleep(0.2)
        # if self.trigger == 'TRIG':
        #     self.pulseGen.write('*TRG') # Remove when actual trigger
        # else:
        #     # self.pulseGen.write(":PULSE0:STATE ON")
        #     time.sleep(0.2)
        # # print(self.mode)

    def stop(self):
        self.pulseGen.write(":PULSE0:STATE OFF")
        time.sleep(0.1)
        self.pulseGen.write(":PULSE1:STATE OFF")
        self.pulseGen.write(":PULSE2:STATE OFF")
        self.pulseGen.write(":PULSE3:STATE OFF")
        self.pulseGen.write(":PULSE0:EXT:MODE DIS")
        self.pulseGen.write(f":PULSE:TRIG:MODE DIS")
        self.pulseGen.close()
        print('Connection to Pulse Generator Closed')

    def switchRestOff(self):
        # self.pulseGen.write(":PULSE2:STATE OFF")
        self.pulseGen.write(":PULSE3:STATE OFF")
        self.pulseGen.write(":PULSE4:STATE OFF")
        self.pulseGen.write(":PULSE5:STATE OFF")
        self.pulseGen.write(":PULSE6:STATE OFF")
        self.pulseGen.write(":PULSE7:STATE OFF")
        self.pulseGen.write(":PULSE8:STATE OFF")


        

def woutTrigger():
    "Test Function"
    gen = pulseGenerator()
    gen.width = 1
    gen.mode = 'NORM'
    gen.delay = 0
    gen.trigger = 'DIS'

    # print(gen.trigger)

    gen.run()

    time.sleep(10)
    gen.stop()
    # gen.close()

def wTrigger():
    "Test Function"
    gen = pulseGenerator()
    gen.width = 0.02
    gen.mode = 'SING'
    gen.delay = 0.01
    gen.trigger = 'TRIG'

    gen.run()
    time.sleep(3)
    gen.stop()

# woutTrigger()


# gen =pulseGenerator()
# gen.run()