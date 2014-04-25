from SlowControl import *
from ALCT        import *
from common import Now
from common import Day
import delays
import random
import datetime
import time

def main():
    ALCT384=1
    global  alcttype
    alcttype=ALCT384
    SelfTest(alcttype)
    k=input("press close to exit")
    
    #ActiveHW = 1
    #SetALCTType(ALCT384)
    #WriteAllThresholds(random.getrandbits(8))
    #ReadAllThresholds()
    #ReadAllVoltages()
    #ReadAllCurrents()
    #CheckTemperature()
    #delays.ReadPatterns(SendPtrns,alcttype)
    # for i in range(alct[alcttype].groups): 
       #for j in range(NUM_OF_DELAY_CHIPS_IN_GROUP): 
           # print(SendPtrns[i][j].Pattern)

    #ReadIDCodes()
    #delays.Walking1(ALCT384)
       #delays.SetDelaysChips(ALCT384)



def ReadIDCodes():
    print("\n%s> Read Board/Firmware ID Codes" % Now()) 
    print("\t  Slow Control Firmware ID: 0x%X" % ReadIDCode(0))
    print("\t  Fast Control Firmware ID: 0x%X" % ReadIDCode(1))
    print("\t  Board Serial Number:      0x%X" % ReadBoardSN(0x2))
    print("\t  Mezz. Serial Number:      0x%X" % ReadBoardSN(0x3))

def ReadAllVoltages():
    print("\n%s> Read Power Supply Voltages" % Now())
    npwrchannels = alct[1].pwrchans
    for i in range (alct[alcttype].pwrchans): 
        ADC     = ReadVoltageADC(i)
        voltage = ADC * arVoltages[i].coef
        print ("\t  %s\tExpect=%.2fV   Read=%2.2fV  (ADC=0x%03X)" % (arVoltages[i].ref, arVoltages[i].refval, voltage, ADC))

def ReadAllCurrents(): 
    print("\n%s> Read Power Supply Currents" % Now())
    for i in range (alct[alcttype].pwrchans): 
        ADC     = ReadCurrentADC(i)
        current = ADC * arCurrents[i].coef
        print ("\t  %s\tExpect=%.2fA   Read=%2.2fA  (ADC=0x%03X)" % (arCurrents[i].ref, arCurrents[i].refval, current, ADC))
    
def ReadAllThresholds(): 
    NUM_AFEB=24
    print("\n%s> Read All Thresholds" % Now())
    for j in range (NUM_AFEB): 
        thresh = ReadThreshold(j)
        print("\t  AFEB #%02i:  Threshold=%.3fV (ADC=0x%03X)" % (j, (ADC_REF/1023)*thresh, thresh))

def WriteAllThresholds(thresh):
    print("\n%s> Write All Thresholds to %i" % (Now(), thresh))
    for i in range(NUM_AFEB): 
        SetThreshold(i, thresh);
    print("\t  All thresholds set to %i" % thresh)

def CheckTemperature():
    print("\n%s> Check Board Temperature" % Now())
    print("\t  Board Temperature=%0.2fF" % ReadTemperature())

def Now():
    ts = time.time()
    st = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')
    return(st)

def Day():
    ts = time.time()
    st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
    return(st)


if __name__ == "__main__":
    main()
