import SlowControl
import SingleCable
import TesterBoard
from ALCT        import *
from common import Now
from common import Day
import delays
import random
import datetime
import time
import os

def main():
    ALCT384=1
    global  alcttype
    alcttype=ALCT384
    #delays.SetDelayChips(ALCT384)
    #k=input("delete me later")
    MainMenu()
    print("SIC TRANSIT GLORIA MUNDI")
    sleep(0.1)
    
def MainMenu():
    while True:
        os.system('cls')
        print("\n====================")
        print(  " ALCT JTAG Test Menu")
        print(  "====================\n")
        ReadIDCodes()
        DetectMezzanineType()
        print("")
        print("\t 0 ALCT Automatic Full Test")
        print("\t 1 Slow Control Tests")
        print("\t 2 Thresholds Linearity Full Scan")
        print("\t 3 Delay ASICs Pattern Test")
        print("\t 4 Delay ASICs Delay Test")
        print("\t 5 Single Cable Test")
        print("\t 8 Initialize JTAG Chains")

        k=input("\nChoose Test: ")
        if not k: break
        os.system('cls')

            
        ALCT384=1
        global  alcttype
        alcttype=ALCT384

        if k=="0":
            AutomaticFullTest()
        if k=="1":
            SlowControl.SubtestMenu(alcttype)
        if k=="2":
            SlowControl.CheckThresholds(alct[alcttype].groups*alct[alcttype].chips,1)
        if k=="3":
            delays.SubtestMenu(alcttype)
        if k=="4":
            TesterBoard.SubtestMenu(alcttype)
        if k=="5":
            SingleCable.SubtestMenu(alcttype)
        if k=="8":
            ChooseJTAGChain() 


def ChooseJTAGChain():
        while True: 
            os.system('cls')
            print("\n==========================")
            print(  " JTAG Chain Initialization")
            print(  "==========================\n")
            print("\t 0 Slow Control Programming Chain")
            print("\t 1 Slow Control Control Chain")
            print("\t 2 Mezzanine Programming Chain")
            print("\t 3 Mezzanine Control Chain")

            k=input("\nChoose chain or <cr> to return to Main Menu: ")
            os.system('cls')
            print("")
            if not k: break

            if k=="0": 
                SetChain(arJTAGChains[0])
            if k=="1": 
                SetChain(arJTAGChains[1])
            if k=="2": 
                SetChain(arJTAGChains[2])
            if k=="3":
                SetChain(arJTAGChains[3])
            k=input("\n<cr> to return to menu: ")

def AutomaticFullTest():
    k=input("\nLoad Single Cable Firmware. Press s to skip, any key to Continue\n")
    if k!="s":
        SingleCable.SingleCableSelfTest()
    
    k=input("\nLoad Test Firmware. Press s to skip, any key to Continue\n")

    k=input("\nLoad Normal Firmware. Press s to skip, any key to Continue\n")
    if k!="s":
        SlowControl.SelfTest(alcttype)    


def ReadIDCodes():
    print("\t Slow Control Firmware ID: 0x%X" % SlowControl.ReadIDCode(0))
    print("\t Fast Control Firmware ID: 0x%X" % SlowControl.ReadIDCode(1))
    print("\t Board Serial Number:      0x%X" % SlowControl.ReadBoardSN(0x2))
    print("\t Mezz. Serial Number:      0x%X" % SlowControl.ReadBoardSN(0x3))

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
