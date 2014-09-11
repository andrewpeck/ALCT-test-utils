#!/usr/bin/env python3

################################################################################
# alct specific includes
import slowcontrol
import singlecable
import testerboard
import common
import delays
import alct
import beeper
#-------------------------------------------------------------------------------
# generic python includes
import ctypes
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
# user can change it later..
alcttype = 1

def main():
    if (alct.DetectMezzanineType()==alct.VIRTEX1000):
        global alcttype
        alcttype = alct.ALCT672

    MainMenu()

def MainMenu():
    while True:
        common.ClearScreen()

        print("                                                                               ")
        print("===============================================================================")
        print(" ALCT JTAG Test Menu")
        print("===============================================================================")
        print("    %s" % PrintIDCodes()                                                        )
        print("    %s" % PrintMezzType()                                                       )
        print("    ALCT Type = %s" % StringALCTType(alcttype)                                  )
        print("                                                                               ")
        print("    0 ALCT Automatic Full Test                                                 ")
        print("    1 Slow Control Tests                                                       ")
        print("    2 Delay ASICs Pattern Test                                                 ")
        print("    3 Specialty Tester Board Tests                                             ")
        print("    4 Single Cable Tests                                                       ")
        print("    5 Change ALCT Type                                                         ")
        print("    6 Load ALCT Firmware                                                       ")
        print("                                                                               ")

        k=input("Choose Test: ")
        common.ClearScreen()

        if k=="0": AutomaticFullTest()
        if k=="1": slowcontrol.SubtestMenu(alcttype)
        if k=="2": delays.SubtestMenu(alcttype)
        if k=="3": testerboard.SubtestMenu(alcttype)
        if k=="4": singlecable.SubtestMenu(alcttype)
        if k=="5": ChooseALCTType()
        if k=="6": LoadFirmware()

# Menu to change type of ALCT
def ChooseALCTType():
    while True:
        common.ClearScreen()
        print("                                                                               ")
        print("===============================================================================")
        print(" Choose ALCT Baseboard Type"                                                    )
        print("===============================================================================")
        print("                                                                               ")
        print("    0 ALCT-288                                                                 ")
        print("    1 ALCT-384                                                                 ")
        print("    2 ALCT-672                                                                 ")

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

def LoadFirmware():
    while True:
        common.ClearScreen()
        print("                                                                               ")
        print("===============================================================================")
        print(" Firmware Loading / JTAG Chain Initialization                                  ")
        print("===============================================================================")
        print("                                                                               ")
        print("    0 Load Mezzanine Firmware                                                  ")
        print("    1 Load Slow Control Firmware                                               ")
        print("                                                                               ")
        print("    2 Initialize Slow Control Programming Chain                                ")
        print("    3 Initialize Slow Control Control Chain                                    ")
        print("    4 Initialize Mezzanine Programming Chain                                   ")
        print("    5 Initialize Mezzanine Control Chain                                       ")

        k=input("\nChoose chain or <cr> to return to Main Menu: ")

        common.ClearScreen
        print("")
        if not k: break

        if k=="0": LoadMezzanineFirmware()
        if k=="1": LoadSlowControlFirmware()
        if k=="2": alct.SetChain(alct.SLOWCTL_PROGRAM) # Slow Control Programming
        if k=="3": alct.SetChain(alct.SLOWCTL_CONTROL) # Slow Control Control
        if k=="4": alct.SetChain(alct.VIRTEX_PROGRAM)  # Mezzanine Programming
        if k=="5": alct.SetChain(alct.VIRTEX_CONTROL)  # Mezzanine Control

        k=input("\n<cr> to return to menu: ")
        if not k: break

def LoadMezzanineFirmware():
    print("Walkthrough to load mezzanine firmware...")

    while True:
        print("1. Disable the built-in clock: (switch located just left of top of mezzanine card).")
        print("     a. ALCT-288: SW3 to position 2/3")
        print("     b. ALCT-384: SW1 to position 2/3")
        print("     c. ALCT-672: SW2 to position 2/3")
        k=input("\t <y> to continue: ")
        if k=="y": break
    while True:
        print("2. Power cycle the ALCT board")
        k=input("\t <y> to continue: ")
        if k=="y": break
    while True:
        print("3. Power cycle the ALCT board")
        print("3. Open iMPACT software")
        print("     a. Under iMPACT Project, hit 'Cancel'")
        print("     b. In top left window, double-click Boundary Scan")
        print("     c. Initialize Chain Under File/Initialize Chain or pressing [Ctrl + I]")
        print("     d. You should see 2 or 3 devices show up ")
        print("        depending on Virtex-600E or Virtex 1000E mezzanine.")
        print("     e. Bypass the first device (FPGA)")
        print("4. Assign firmware to the EEPROM(s):")
        print("     a. Make sure to select 'Parallel Mode'  and 'Load FPGA'")
        print("        in the programming properties")
        print("5. Press 'Program Device'")
        alct.SetChain(alct.VIRTEX_PROGRAM)  # Mezzanine Programming
        k=input("\t <y> to continue: ")
        if k=="y": break
    while True:
        print("6. Restore clock to position 1/2")
        k=input("\t <y> to continue: ")
        if k=="y": break
    while True:
        print("Programming Finished")
        k=input("\t <cr> to continue")
        if not k: break


def LoadSlowControlFirmware():
    while True:
        print  ("1. Disable the built-in clock: (switch located just left of top of mezzanine card).")
        print  ("     a. ALCT-288: SW3 to position 2/3")
        print  ("     b. ALCT-384: SW1 to position 2/3")
        print  ("     c. ALCT-672: SW2 to position 2/3")
        k=input("        <y> to continue: ")
        if k=="y": break
    while True:
        print  ("2. Power cycle the ALCT board")
        k=input("        <y> to continue: ")
        if k=="y": break
    while True:
        alct.SetChain(alct.SLOWCTL_PROGRAM)  # Mezzanine Programming
        print  ("3. Open iMPACT software")
        print  ("     a. Under iMPACT Project, hit 'Cancel'")
        print  ("     b. In top left window, double-click Boundary Scan")
        print  ("     c. Initialize Chain Under File/Initialize Chain or pressing [Ctrl + I]")
        print  ("     d. You should see 2 devices show up ")
        print  ("     e. Bypass the first device (FPGA)")
        print  ("4. Assign firmware to the EEPROM(s):")
        print  ("     a. Make sure to select 'Parallel Mode'  and 'Load FPGA'")
        print  ("        in the programming properties")
        print  ("5. Press 'Program Device'")
        k=input("        <y> to continue: ")
        if k=="y": break
    while True:
        print  ("6. Restore clock to position 1/2")
        k=input("        <y> to continue: ")
        if k=="y": break
    while True:
        print  ("Programming Finished")
        k=input("        <cr> to continue")
        if not k: break

def AutomaticFullTest():
    print("Starting ALCT automatic full test..")

    # Get Baseboard + Mezzanine Serial Numbers for Logging Purposes
    while True:
        baseboardSN = int(input("\n ALCT Baseboard Serial Number: "),10)
        if baseboardSN:
            mezzanineSN = int(input(" ALCT Mezzanine Serial Number: "),10)
            if mezzanineSN:
                break
        else:
            k=input("\n No serial number entered! <y> to continue without logging: ")
            if k=="y" or k=="Y" or k=="yes":
                break


    # Create Log if baseboard and mezzanine have S/N specified
    # Otherwise just log to Null
    if (baseboardSN and mezzanineSN):
        logFileName = str.format("%s_alct%03i_mezz%04i_.txt" % (time.strftime("%Y%m%d-%H%M%S"), baseboardSN, mezzanineSN))
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
    logging.info("\t%s" % PrintIDCodes())

    #-------------------------------------------------------------------------------
    # Single cable loopback tests to Check Connectivity of AFEB Connectors,
    # connectivity of Delay Chips, connectivity of ALCT mezzanine tx (J5)
    #-------------------------------------------------------------------------------

    print("")
    print("Single Cable Tests:")
    print("    * Please load Single Cable Firmware")
    print("    * Ensure that Clock source jumper is set to position 1/2")
    print("    * Check that 40Mhz oscillator is installed")
    while True:
        k=input("\t <s> to skip, <j> to set jtag programming chain, <cr> to Continue: ")
        print("")

        if k=="j":
            alct.SetChain(alct.VIRTEX_PROGRAM)  # Mezzanine Programming
        if k=="s":
            skipped += 1
            logging.info("\nSKIPPED: Single Cable Self Test ")
            break
        if not k:
            errors += singlecable.SingleCableSelfTest(alcttype)
            break

    #-------------------------------------------------------------------------------
    # Special board tests:
    # Verifies delay chip pattern write/read
    # Verifies delay chip setting of Delays
    # Verifies linearity of AFEB thresholds (read/write)
    #-------------------------------------------------------------------------------

    while True:
        print("Testing Firmware Tests:")
        print("    * Please load Test Firmware")
        print("    * Set Clock Source Jumper to position 2/3.")
        print("    * Connect Tester Board")
        k=input("\t <s> to skip, <j> to set JTAG programming chain, <cr> to Continue: ")
        print("")

        if k=="j":
            alct.SetChain(alct.VIRTEX_PROGRAM)  # Mezzanine Programming
        if k=="s":
            skipped += 1
            logging.info("\nSKIPPED: Test Firmware Tests")
            break
        if not k:
            # Delays Chips Pattern Tests
            print       ('Delay ASICs Pattern Test:')
            logging.info('Delay ASICs Pattern Test:')

            while True:
                k=input("\t<s> to skip, <cr> to continue test: ")
                print("")
                if k=="s":
                    skipped += 1
                    logging.info("\nSKIPPED: Delay ASICs Pattern Injection Test")
                    break
                if not k:
                    errors += delays.PatternsSelfTest(alcttype)
                    break

            # Tester Board Test
            print ('\nTester Board Delay ASICs Delay Verification Test:')
            while True:
                k=input("\t<s> to skip, <cr> to continue test: ")
                if k=="s":
                    skipped += 1
                    logging.info("\nSKIPPED: Delay ASICs Delay Verification Test")
                    break
                if not k:
                    errors += testerboard.TestboardDelaysCheck(alcttype)
                    break

            #Test Pulse Semi-auto self Test
            print("\nTest Pulse Semi-Automatic Self Test: ")
            while True:
                k=input("\t<s> to skip, <cr> to continue test: ")
                if k=="s":
                    skipped += 1
                    logging.info("\nSKIPPED: Test Pulse Semi-Automatic Self-Test")
                    break
                if not k:
                    errors += testerboard.TestPulseSelfCheck(alcttype)
                    break

            # Standby Mode Semi-auto Self Check
            print("\nAFEB Standby Mode Semi-Automatic Self Test: ")
            while True:
                k=input("\t<s> to skip, <cr> to continue test: ")
                print("")
                if k=="s":
                    skipped += 1
                    logging.info("\nSKIPPED: Standby Mode Semi-Automatic Self-Test")
                    break
                if not k:
                    errors += testerboard.StandbySelfCheck(alcttype)
                    break

            #-----------------------------
            break

    #-------------------------------------------------------------------------------
    # "Normal" firmware self-test
    # Checks voltages, currents with standard firmware installed
    # Checks functioning of slow control features
    #-------------------------------------------------------------------------------

    while True:
        print  ("Normal Firmware Tests:")
        print  ("    * Please load Normal Firmware")
        print  ("    * Disconnect Tester Board")
        print  ("    * Ensure that Clock source jumper is set to position 1/2")
        k=input("         <s> to skip, <j> to set JTAG programming chain, <cr> to Continue: ")

        if k=="j":
            alct.SetChain(alct.VIRTEX_PROGRAM)  # Mezzanine Programming
        if k=="s":
            skipped += 1
            logging.info("\nSKIPPED: Slow Control Self Test")
            break
        if not k:
            errors += slowcontrol.SelfTest(alcttype)
            break

    #-------------------------------------------------------------------------------
    # Manually performed tests which are verified solely by eye..
    #-------------------------------------------------------------------------------

    #-------------------------------------------------------------------------------
    logging.info("\nTest Pulse Amplitude and Mask Check:")
    print("")
    print("Test Pulse Generator Tests: ")
    print("    For each test pulse channel, Please verify:")
    print("        1) Test pulse can correctly turn ON and OFF")
    print("        2) Test pulse amplitude is correct")
    print("    Recommended scope settings: 200 us, 500mV")
    print("")

    slowcontrol.SetTestPulsePower(1)       # Turn on Test Pulse Generator
    slowcontrol.SetTestPulsePowerAmp(208)  # Set amplitude to approximately 1V
    for i in range (6):
        print("    Connect oscilloscope to Lemo connector S%i" % (i+1))

        # Turn OFF test-channel, turn ON all others
        slowcontrol.SetTestPulseStripLayerMask(~(0x1 << i))
        while (True):
            k=input("\t Channel %i: Verify no test pulse. \n\t\t <p> to pass, <f> to fail, <s> to skip: " % i)
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
            k=input("\t Channel %i: Verify test pulse amplitude=1.2V. \n\t\t <p> to pass, <f> to fail, <s> to skip: " % i)
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
    print("")
    print("Voltage Reference Check:")

    # Manual check of reference voltage
    print("    Please verify the precision voltage reference on chips:     ")
    print("        * U2, U3, U4         for ALCT-288                       ")
    print("        * U2, U3, U4         for ALCT-384                       ")
    print("        * U2, U3, U4, U5, U6 for ALCT-672                       ")
    print("                                                                ")
    print("    Use a voltmeter to measure the voltage on pin number 14:    ")
    print("        From the corner of the chip nearest to LEMO connectors, ")
    print("        it is the 4th pin down                                  ")
    print("                                                                ")
    print("       +--------------+                                         ")
    print("       | *            |                                         ")
    print("      -|  01      20  |-                                        ")
    print("      -|  02      19  |-                                        ")
    print("      -|  03      18  |-                                        ")
    print("      -|  04      17  |-                                        ")
    print("      -|  05      16  |-                                        ")
    print("      -|  06      15  |-                                        ")
    print("      -|  07      14  |- <-- 1.225 V                            ")
    print("      -|  08      13  |-                                        ")
    print("      -|  09      12  |-                                        ")
    print("      -|  10      11  |-                                        ")
    print("       +--------------+                                         ")
    print("                                                                ")
    print("    DC voltage MUST be 1.225 +- 0.001V                          ")
    print("                                                                ")


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

    # Manual check of crystal oscillator
    print("\nVerify that all Power Indicator LEDs are on, and approx. same brightness")
    while True:
        k=input("\t<y> to confirm, <s> to skip: ")
        if k=="y":
            logging.info("\tPASS: Power LED Brightness Check")
            break
        if k=="s":
            logging.info("\tSKIPPED: Power LED Brightness Check")
            skipped +=1
            break


    # Manual check of crystal oscillator
    print("\nVerify that the crystal oscillator is removed")
    while True:
        k=input("\t<y> to confirm, <s> to skip: ")
        if k=="y":
            logging.info("\tPASS: User confirmed that crystal oscillator is removed")
            break
        if k=="s":
            logging.info("\tSKIPPED: Crystal oscillator removal")
            skipped +=1
            break


    # Manual check of clock select jumper
    print("")
    print("Please verify the position of clock select jumpers is set to EXTERNAL!")
    print("     * ALCT-288: SW3 to position 2/3")
    print("     * ALCT-384: SW1 to position 2/3")
    print("     * ALCT-672: SW2 to position 2/3")
    while True:
        k=input("\t<y> to confirm, <s> to skip: ")
        if k=="y":
            logging.info("\tPASS: User confirmed that Clock source shunts are set to correct position")
            break
        if k=="s":
            logging.info("\tSKIPPED: Clock select shunt check")
            skipped +=1
            break

    #Pass? Fail? Summary.
    logging.info("\n===============================================================================")
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

    beeper.playTune(beeper.FINI)
    k=input("\nAutomatic Self Test Finished ! Any key to return to main menu: ")


# Prints and Returns hardware ID codes..
# FIXME: doesn't read some of them out. Need to understand why.
def PrintIDCodes():
    #idcodestr  = ("Fast Control Firmware ID: 0x%X\n"     % alct.ReadIDCode (0x0))
    #idcodestr += ("    EEPROM1 ID Code:          0x%X\n" % alct.ReadIDCode (0x1))
    #idcodestr += ("    EEPROM2 ID Code:          0x%X\n" % alct.ReadIDCode (0x2))
    idcodestr = ("    Slow Control Firmware ID: 0x%X\n" % alct.ReadIDCode (0x3))

    return (idcodestr)

def PrintMezzType():
    mezztype = alct.DetectMezzanineType()
    if mezztype == -1:
        msg = 'ERROR: Mezzanine Card Not Detected'
    if mezztype ==  alct.VIRTEX1000:
        msg = 'Mezzanine Board with Xilinx Virtex 1000 chip is detected'
    if mezztype ==  alct.VIRTEX600:
        msg = 'Mezzanine Board with Xilinx Virtex 600 chip is detected'
    return(msg)

# Generates a string of the ALCT Type.. useful in some limited cases..
def StringALCTType(type):
    if   type == alct.ALCT288:
        s = "ALCT-288"
    elif type == alct.ALCT384:
        s = "ALCT-384"
    elif type == alct.ALCT672:
        s = "ALCT-672"
    return(s)

if __name__ == "__main__":
    main()
