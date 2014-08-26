#!/usr/bin/env python3

################################################################################
# alct specific includes
import slowcontrol
import singlecable
import testerboard
import common
import delays
import alct
import ctypes
#-------------------------------------------------------------------------------
# generic python includes
import random
import datetime
import time
import os.path
import os
import atexit
#-------------------------------------------------------------------------------
# logging 
import logging
################################################################################

# default to ALCT-384
alcttype = 1

def main():
    if os.name == 'nt': 
        ctypes.windll.inpout32.Closedriver()
        ctypes.windll.inpout32.Opendriver(True)
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

    # Get Baseboard + Mezzanine Serial Numbers for Logging Purposes
    while True: 
        baseboardSN = input("\n ALCT Baseboard Serial Number: ")
        if baseboardSN: 
            mezzanineSN = input(" ALCT Mezzanine Serial Number: ")
            if mezzanineSN: 
                break
        else: 
            k=input("\n No serial number entered! <y> to continue without logging: ")
            if k=="y" or k=="Y" or k=="yes": 
                break


    # Create Log if baseboard and mezzanine have S/N specified
    # Otherwise just log to Null
    if (baseboardSN and mezzanineSN):
        logFileName = time.strftime("%Y%m%d-%H%M%S") + "_alct" + baseboardSN + "_mezz" + mezzanineSN + ".txt"
        logFileDir = os.path.join(os.path.dirname(__file__),"testlogs/")
        if not os.path.exists(logFileDir):
            os.makedirs(logFileDir)

        logFile = os.path.join(logFileDir,logFileName)
    else:
        baseboardSN = 0
        mezzanineSN = 0
        logFile = os.devnull

    # Log File Configuration
    logging.basicConfig(filename=logFile, level=logging.DEBUG, format='%(message)s')

    # Error Accumulators
    errors = 0
    skipped = 0

    #-------------------------------------------------------------------------------
    # Board Info
    #-------------------------------------------------------------------------------

    logging.info("Testing %s #%s with Mezzanine #%s" % (StringALCTType(alcttype), baseboardSN, mezzanineSN))
    logging.info('\nID Codes Detected: ')
    logging.info(" %s" % PrintIDCodes())

    #-------------------------------------------------------------------------------
    # Single cable loopback tests to Check Connectivity of AFEB Connectors,
    # connectivity of Delay Chips, connectivity of ALCT mezzanine tx (J5)
    #-------------------------------------------------------------------------------

    k=input("\nPlease load Single Cable Firmware. \n\t <s> to skip, <cr> to Continue: ")
    if k!="s":
        errors += singlecable.SingleCableSelfTest(alcttype)
    else: 
        skipped += 1
        logging.info("\nSKIPPED: Single Cable Self Test ")

    #-------------------------------------------------------------------------------
    # Special board tests:
    # Verifies delay chip pattern write/read
    # Verifies delay chip setting of Delays
    # Verifies linearity of AFEB thresholds (read/write)
    #-------------------------------------------------------------------------------

    k=input("\nPlease load Test Firmware. \n\t <s> to skip, <cr> to Continue: ")
    if k!="s":
        # Delays Chips Pattern Tests
        errors += delays.PatternsSelfTest(alcttype)

        # Thresholds Linearity Test

        # Tester Board Test
        errors += testerboard.TestboardDelaysCheck(alcttype)

        #Test Pulse Self Test
        errors += testerboard.TestPulseSelfCheck(alcttype)
    else:
        skipped += 1
        logging.info("SKIPPED: Test Firmware Tests")

    #-------------------------------------------------------------------------------
    # "Normal" firmware self-test
    # Checks voltages, currents with standard firmware installed
    # Checks functioning of slow control features
    #-------------------------------------------------------------------------------

    k=input("\nPlease load Normal Firmware. \n\t <s> to skip, <cr> to Continue: ")
    if k!="s":
        errors += slowcontrol.SelfTest(alcttype)
    else: 
        skipped += 1
        logging.info("SKIPPED: Slow Control Self Test")

    #-------------------------------------------------------------------------------
    # Manually performed tests which are verified solely by eye..
    #-------------------------------------------------------------------------------

    #-------------------------------------------------------------------------------
    logging.info("\nTest Pulse Amplitude and Mask Check:")
    print("\nTest Pulse Generator Tests: ")

    print("\t For each test pulse channel, Please verify:")
    print("\t 1) Test pulse can correctly turn ON and OFF")
    print("\t 2) Test pulse amplitude is correct")
    print("\t Recommended scope settings: 200 us, 500mV")

    slowcontrol.SetTestPulsePower(1)       # Turn on Test Pulse Generator
    slowcontrol.SetTestPulsePowerAmp(208)  # Set amplitude to approximately 1V
    for i in range (6):
        print("    Connect oscilloscope to Lemo connector S%i" % (i+1))

        # Turn OFF test-channel, turn ON all others
        slowcontrol.SetTestPulseStripLayerMask(~(0x1 << i))
        while (True): 
            k=input("\tChannel %i: Verify no test pulse. \n\t\t <p> to pass, <f> to fail, <s> to skip: " % i)
            if k=="p": 
                logging.info("\t PASS: Channel %i confirmed test pulse power down" %i)
                break
            if k=="f": 
                logging.info("\t FAIL: Channel %i failed test pulse power down" %i)
                errors+=1
                break
            if k=="s": 
                logging.info("\t SKIPPED: Channel %i User neglected to check Test Pulse Power Down" % i)
                skipped+=1
                break

        # Turn ON test-channel, turn OFF all others
        slowcontrol.SetTestPulseStripLayerMask(0x1 << i)
        while (True): 
            k=input("\tChannel %i: Verify test pulse amplitude=1.2V. \n\t\t <p> to pass, <f> to fail, <s> to skip: " % i)
            if k=="p": 
                logging.info("\t PASS: Channel %i confirmed test pulse power up" %i)
                break
            if k=="f": 
                logging.info("\t FAIL: Channel %i failed test pulse power up" %i)
                errors+=1
                break
            if k=="s": 
                logging.info("\t SKIPPED: Channel %i User neglected to check Test Pulse Power Up" % i)
                skipped+=1
                break
    slowcontrol.SetTestPulsePower(0)  # Turn off Test Pulse Generator

    #-------------------------------------------------------------------------------
    logging.info("\nVoltage Reference Check:")
    print("\nVoltage Reference Check:")

    # Manual check of reference voltage
    print("\n    Please verify the precision voltage reference on chips: ")
    print("\t * U2, U3, U4         for ALCT-288")
    print("\t * U2, U3, U4         for ALCT-384")
    print("\t * U2, U3, U4, U5, U6 for ALCT-672")
    print("")
    print("\t Use a voltmeter to measure the voltage on pin number 14:")
    print("\t     From the corner of the chip nearest to LEMO connectors,")
    print("\t     it is the 4th pin down")
    print("\t ")
    print("\t    +--------------+              ")
    print("\t    | *            |              ")
    print("\t   -|  01      20  |-             ")
    print("\t   -|  02      19  |-             ")
    print("\t   -|  03      18  |-             ")
    print("\t   -|  04      17  |-             ")
    print("\t   -|  05      16  |-             ")
    print("\t   -|  06      15  |-             ")
    print("\t   -|  07      14  |- <-- 1.225 V ")
    print("\t   -|  08      13  |-             ")
    print("\t   -|  09      12  |-             ")
    print("\t   -|  10      11  |-             ")
    print("\t    +--------------+              ")
    print("")
    print("\tDC voltage MUST be 1.225 +- 0.001V")
    print("")


    for i in range(2,7): 
        while True: 
            # Don't check U5 and U6 for 288 and 384 boards
            if (alcttype==1 or alcttype==2) and (i>4): break 

            # Loop over boards and check
            k=input("\tU%i voltage: <p> to pass, <f> to fail, <s> to skip: " % i)
            if k=="p": 
                logging.info("\t PASS: User confirmed good U%i reference voltage" %i)
                break
            if k=="f": 
                logging.info("\t FAIL: User indicates bad U%i reference voltage" % i)
                errors+=1
                break
            if k=="s": 
                logging.info("\t SKIPPED: User failed to check U%i reference voltage" % i)
                skipped+=1
                break

    #-------------------------------------------------------------------------------
    logging.info("\nFinal configuration: ")

    # Manual check of clock select jumper
    print("\nPlease verify the position of clock select jumpers is set to EXTERNAL!")
    print("     * ALCT-288: SW3 to position 2/3")
    print("     * ALCT-384: SW1 to position 2/3")
    print("     * ALCT-672: SW2 to position 2/3")
    while True: 
        k=input("\t<y> to confirm, <s> to skip: ")
        if k=="y": 
            logging.info("\t PASS: User confirmed that Clock source shunts are set to correct position")
            break
        if k=="s": 
            logging.info("SKIPPED: Clock select shunt check")
            skipped +=1
            break

    # Manual check of crystal oscillator
    print("\nVerify that the crystal oscillator is removed")
    while True: 
        k=input("\t<y> to confirm, <s> to skip: ")
        if k=="y": 
            logging.info("\t PASS: User confirmed that crystal oscillator is removed")
            break
        if k=="s": 
            logging.info("SKIPPED: Crystal oscillator removal")
            skipped +=1
            break

    #Pass? Fail? Summary.
    logging.info("\n================================================================================")
    logging.info("\nFinal Tests Summary: ")
    print       ("\nFinal Tests Summary: ")
    if (skipped > 0): 
        print        ("\t ====> NOTE: %i Tests were Skipped!" % (skipped))
        logging.info ("\t NOTE: %i Tests were Skipped!" % (skipped))

    if (errors > 0):
        print        ("\t ====> FAIL: ALCT #%s with mezzanine #%s failed with %i errors" % (baseboardSN, mezzanineSN, errors))
        logging.info ("\t FAIL: ALCT #%s with mezzanine #%s failed with %i errors" % (baseboardSN, mezzanineSN, errors))
    elif (errors == 0 and skipped==0):
        print        ("\t ====> PASS: ALCT #%s with mezzanine #%s passed all tests" % (baseboardSN, mezzanineSN))
        logging.info ("\t PASS: ALCT #%s with mezzanine #%s passed all tests" % (baseboardSN, mezzanineSN))
    else:
        print        ("\t ====> FAIL: ALCT #%s with mezzanine #%s passed all tests performed, but tests were skipped." % (baseboardSN, mezzanineSN))
        logging.info ("\t FAIL: ALCT #%s with mezzanine #%s passed all tests performed, but tests were skipped" % (baseboardSN, mezzanineSN))

    k=input("\nAutomatic Self Test Finished ! Any key to return to main menu: ")


# Prints and Returns hardware ID codes.. doesn't read some of them out. Need to understand why. 
def PrintIDCodes():
    idcodestr  = ("\t Slow Control Firmware ID: 0x%X\n" % alct.ReadIDCode (0x0))
    #idcodestr += ("\t Fast Control Firmware ID: 0x%X\n" % alct.ReadIDCode (0x1))
    #idcodestr += ("\t Board Serial Number:      0x%X\n" % alct.ReadBoardSN(0x2))
    #idcodestr += ("\t Mezz. Serial Number:      0x%X"   % alct.ReadBoardSN(0x3))

    print (idcodestr)
    return (idcodestr)

# Generates a string of the ALCT Type.. useful in some limited cases.. 
def StringALCTType(type):
    if   type == 0: s = "ALCT-288"
    elif type == 1: s = "ALCT-384"
    elif type == 2: s = "ALCT-672"
    return(s)

if os.name == 'nt': 
    atexit.register(ctypes.windll.inpout32.Closedriver)

if __name__ == "__main__":
    main()
