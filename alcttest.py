#!/usr/bin/env python3

#alct specific includes
import slowcontrol
import singlecable
import testerboard
import common
import delays
import alct
from config import logFile

#generic python includes
import random
import datetime
import time
import os.path
import logging

# default to ALCT-384
alcttype = 1

def main():
    MainMenu()
    print("SIC TRANSIT GLORIA MUNDI")
    time.sleep(0.1)

def MainMenu():
    while True:
        common.ClearScreen()
        print("\n================================================================================")
        print(  " ALCT JTAG Test Menu")
        print(  "================================================================================\n")
        PrintIDCodes()
        mezztype = alct.DetectMezzanineType()
        print("")
        print("\t ALCT Type = %s" % StringALCTType(alcttype))
        print("")
        print("\t 0 ALCT Automatic Full Test")
        print("\t 1 Slow Control Tests")
        print("\t 2                    ")
        print("\t 3 Delay ASICs Pattern Test")
        print("\t 4 Delay ASICs Delay Test")
        print("\t 5 Single Cable Test")
        print("\t 7 Change ALCT Type")
        print("\t 8 Initialize JTAG Chains")
        k=input("\nChoose Test: ")
        if not k: break
        common.ClearScreen()

        if k=="0": AutomaticFullTest()
        if k=="1": slowcontrol.SubtestMenu(alcttype)
        if k=="3": delays.SubtestMenu(alcttype)
        if k=="4": testerboard.SubtestMenu(alcttype)
        if k=="5": singlecable.SubtestMenu(alcttype)
        if k=="7": ChooseALCTType()
        if k=="8": ChooseJTAGChain()

# Menu to change type of ALCT 
def ChooseALCTType():
    while True:
        common.ClearScreen()
        print("\n================================================================================"  )
        print(  " Choose ALCT Baseboard Type"                                                       )
        print(  "================================================================================\n")
        print("\t 0 ALCT-288")
        print("\t 1 ALCT-384")
        print("\t 2 ALCT-672")

        k=input("\nChoose baseboard type or <cr> to return to Main Menu: ")
        common.ClearScreen
        print("")
        if not k: break

        global alcttype

        if k=="0": alcttype = 0
        if k=="1": alcttype = 1
        if k=="2": alcttype = 2

        k=input("\n<cr> to return to menu: ")
        if not k: break


def ChooseJTAGChain():
    while True:
        common.ClearScreen()
        print("\n================================================================================")
        print(  " JTAG Chain Initialization")
        print(  "================================================================================\n")
        print("\t 0 Slow Control Programming Chain")
        print("\t 1 Slow Control Control Chain")
        print("\t 2 Mezzanine Programming Chain")
        print("\t 3 Mezzanine Control Chain")

        k=input("\nChoose chain or <cr> to return to Main Menu: ")
        common.ClearScreen
        print("")
        if not k: break

        if k=="0": alct.SetChain(alct.SLOWCTL_PROGRAM) # Slow Control Programming
        if k=="1": alct.SetChain(alct.SLOWCTL_CONTROL) # Slow Control Control
        if k=="2": alct.SetChain(alct.VIRTEX_PROGRAM)  # Mezzanine Programming
        if k=="3": alct.SetChain(alct.VIRTEX_CONTROL)  # Mezzanine Control

        k=input("\n<cr> to return to menu: ")
        if not k: break

def AutomaticFullTest():
    print("Starting ALCT automatic full test..")
    baseboardSN = input("\n ALCT Baseboard Serial Number (<cr> to skip logging): ")
    mezzanineSN = input("\n ALCT Mezzanine Serial Number (<cr> to skip logging): ")

    # Create Log if baseboard and mezzanine have S/N specified
    if (baseboardSN and mezzanineSN):
        logFileName = time.strftime("%Y%m%d-%H%M%S") + "_alct" + baseboardSN + "_mezz" + mezzanineSN + ".txt"
        logFileDir = os.path.join(os.path.dirname(__file__),"testlogs/")
        if not os.path.exists(logFileDir):
            os.makedirs(logFileDir)

        logFile = open(os.path.join(logFileDir,logFileName), 'w')
    # Send logging to Null elsewise
    else:
        logFile = open(os.devnull, 'w')

    logFile.write('ID Codes Detected: ')
    logFile.write("\n %s" % PrintIDCodes())
    logFile.write("\n")

    # error accumulator
    errors = 0

    # Single cable loopback tests to Check Connectivity of AFEB Connectors,
    # connectivity of Delay Chips, connectivity of ALCT mezzanine tx (J5)
    k=input("\nPlease load Single Cable Firmware. Press s to skip, any key to Continue\n")
    if k!="s":
        errors += singlecable.SingleCableSelfTest(alcttype,logFile)

    # Special board tests:
    # Verifies delay chip pattern write/read
    # Verifies delay chip setting of Delays
    # Verifies linearity of AFEB thresholds (read/write)
    k=input("\nPlease load Test Firmware. Press s to skip, any key to Continue\n")
        # Delays Chips Test
        # Tester Board Test
        # Thresholds Linearity Test

    # "Normal" firmware self-test
    # Checks voltages, currents with standard firmware installed
    # Checks functioning of slow control features
    k=input("\nPlease load Normal Firmware. Press s to skip, any key to Continue\n")
    if k!="s":
        errors += slowcontrol.SelfTest(alcttype,logFile)

    # Manual check of Test Pulse
    # need to implement this..

    # Manual check of clock select jumper
    print("Please verify the position of clock select jumpers is set to EXTERNAL!")
    print("\t ALCT-288: SW3 to position 2/3")
    print("\t ALCT-384: SW1 to position 2/3")
    print("\t ALCT-672: SW2 to position 2/3")

    logFile.write("\n")

    while True: 
        k=input("\n<y> to confirm: ")
        if k=="y": break
    logFile.write("\nUser confirmed that Clock source shunts are set to correct position")

    # Manual check of crystal oscillator
    print("Verify that the crystal oscillator is removed")
    while True: 
        k=input("\n<y> to confirm: ")
        if k=="y": break
    logFile.write("\nUser confirmed that crystal oscillator is removed")

    #Pass? Fail? Summary.
    if (errors == 0):
        print ("PASS: ALCT %s with mezzanine %s passed all tests" % (baseboardSN, mezzanineSN))
    else:
        print ("FAIL: ALCT %s with mezzanine %s failed with %i errors" % (baseboardSN, mezzanineSN, errors))

def PrintIDCodes():
    idcodestr  = ("\t Slow Control Firmware ID: 0x%X\n" % alct.ReadIDCode (0x0))
    idcodestr += ("\t Fast Control Firmware ID: 0x%X\n" % alct.ReadIDCode (0x1))
    idcodestr += ("\t Board Serial Number:      0x%X\n" % alct.ReadBoardSN(0x2))
    idcodestr += ("\t Mezz. Serial Number:      0x%X"   % alct.ReadBoardSN(0x3))

    print (idcodestr)
    return (idcodestr)

def StringALCTType(type):
    if   type == 0: s = "ALCT 288"
    elif type == 1: s = "ALCT 384"
    elif type == 2: s = "ALCT 672"
    return(s)

if __name__ == "__main__":
    main()
