#!/usr/bin/env python3

# ------------------------------------------------------------------------------
# Functions for performing Single Cable Loopback Test. 
# Data is sent from the mezzanine, out from the ALCT-TX (J5) Connector, and
# received at each of the AFEB connectors. From there it passes through the
# delay 18/24/42 delay ASICs, through the 9/12/21 Mux chips, and back to the
# mezzanine. 
# ------------------------------------------------------------------------------

import alct
import common

import os
import random

TestNames = ['Custom Data', 'Walking 1', 'Walking 0', 'Filling 1', 'Filling 0', 'Shifting 5s and As', 'Random Data']

# ------------------------------------------------------------------------------

# test is an integer specifying which test to perform, i.e.: 
#       0 = 'Custom Data'
#       1 = 'Walking 1'
#       2 = 'Walking 0'
#       3 = 'Filling 1'
#       4 = 'Filling 0'
#       5 = 'Shifting 5s and As'
#       6 = 'Random Data'
def SingleCableTest(test,channel,npasses=50):
    alct.SetChain(alct.arJTAGChains[3])
    errcnt                  = 0
    CustomData              = 0x1234
    senddata                = 0x0000
    SuppressErrsSingleCable = True
    StopOnErrorSingleCable  = False
    ErrCntSingleTest        = 50


    print('Running %s test on Channel %i' % (TestNames[test],channel))

    # The multiple is a simple coefficient to accomodate for the fact that some
    # tests require more loops than others... e.g. to do one pass of the single
    # cable test, each bit has to be checked so we loop 16 times. Random data
    # requires only one loop. Shifting 5s and As requires two loops (one for 5,
    # one for A), etc... 

    if test==0: multiple = 1
    if test==1: multiple = 16
    if test==2: multiple = 16
    if test==3: multiple = 16
    if test==4:
        senddata    = 0xFFFF
        multiple    = 16
    if test==5: multiple = 2
    if test==6: multiple = 1

    # Main test loop
    for cnt in range(npasses*multiple):
        if test==0:                                                         # 0 = Custom Data Test
            k=input("\nEnter Custom Data or <cr> for %04X" % CustomData)
        if test==1: senddata = 0x0000   |   (0xFFFF & (1 << (cnt % 16)))    # 1 = Walking 1 Test
        if test==2: senddata = 0xFFFF   & (~(0xFFFF & (1 << (cnt % 16))))   # 2 = Walking 0 Test
        if test==3:                                                         # 3 = Filling 1 Test
            if cnt%16==0: senddata=0x0001
            else: senddata = senddata | (0xFFFF & (1 << (cnt % 16)))
        if test==4:                                                         # 4 = Filling 0 Test
            if cnt%16 == 0: senddata=0xFFFE
            else: senddata = senddata & (~(0xFFFF & (1 << (cnt % 16))))
        if test==5:                                                         # 5 = Shifting 5 and A
            if    ((cnt+1) % 2)==1: senddata = 0x5555
            else:                   senddata = 0xAAAA
        if test==6: senddata = random.getrandbits(16)                       # 6 = Random Data

        # Select Channel
        alct.WriteRegister(0x16,0x1FF & channel)
        alct.ReadRegister(0x15)

        # Write Data
        alct.WriteRegister(0x18,0xFFFF & senddata)

        # Read Back Data
        readdata = alct.ReadRegister(0x17)

        if readdata != senddata:
            errcnt += 1
            #if ((not SuppressErrsSingleCable) or (SuppressErrsSingleCable and (errcnt <= ErrCntSingleTest))):
                #print('\t ERROR: Pass #%02i Set Mask Register to 0x%04X Readback 0x%04X' % (cnt,senddata,readdata))
            if StopOnErrorSingleCable:
                return(0)

        # Select Channel
        alct.WriteRegister(0x16,channel | 0x40)

        # Read Data
        alct.WriteRegister(0x16,channel | 0x1FF)
        readdata = alct.ReadRegister(0x19)

        status = ('\t Pass #%02i Read=0x%04X Expect=0x%04X' % (cnt//multiple+1,readdata,senddata))
        common.Printer(status)

        if (readdata != senddata):
            errcnt += 1
            if ((not SuppressErrsSingleCable) or (SuppressErrsSingleCable and (errcnt <= ErrCntSingleTest))):
                print('\n\t ERROR: Pass #%02i Read=0x%04X Expect=0x%04X' % (cnt,readdata,senddata))
            if StopOnErrorSingleCable:
                return(0)

    if errcnt==0:
        print('\n\t ====> Passed')
    else:
        print('\n\t ====> Failed Single Cable Test with %i Errors' % errcnt)
    return (errcnt)

def SingleCableSelfTest(alcttype,logFile):
    print("\n%s > Starting Single Cable Automatic Test\n" % common.Now())
    errors = 0 

    for (channel) in range (alct[alcttype].groups * alct[alcttype].chips):
        k = input ("Please connect ALCT connector J5 to AFEB connector %i. s to skip, <cr> to continue" % channel)

        # skip connector
        if (k=="s" or k=="S"): 
            errors += 1
            continue

        # perform all tests for this AFEB
        else: 
            for i in range(7):
                fail = SingleCableTest(i,0,10)
                if fail: 
                    errors += fail
                    logFile.write ("Failed %s Single Cable Test with %i Errors" % TestNames[i], fail)
                else: 
                    logFile.write ("Passed %s Single Cable Test" % TestNames[i])

    # Tests Summary

    print         ("Summary:")
    logFile.write ("Summary:")

    if errcnt==0:
        print        ('\n\t ====> Passed')
        logFile.write('\n\t ====> Passed')
    else:
        print        ('\n\t ====> Failed Single Cable Test with %i Total Errors' % errcnt)
        logFile.write('\n\t ====> Failed Single Cable Test with %i Total Errors' % errcnt)

    return (errors) 

def SubtestMenu(alcttype):
    channel=0
    while True:
        common.ClearScreen()
        print("\n================================================================================"  )
        print(  " Single Cable Test Submenu"                                                        )
        print(  "================================================================================\n")
        print("\t 0 Run All Tests")
        print("\t 1 Custom Data Test")
        print("\t 2 Walking 1 Test")
        print("\t 3 Walking 0 Test")
        print("\t 4 Filling 1 Test")
        print("\t 5 Filling 0 Test")
        print("\t 6 Shifting 5 and A Test")
        print("\t 7 Random Data Test")

        k=input("\nChoose Test or <cr> to return to Main Menu: ")
        if not k: break
        test = int(k,10)

        k=input("\nChannel (<cr> for ch=%i):" % channel)
        if k:
            channel = int(k,10)
        common.ClearScreen()
        print("")

        if test==0:
            for i in range(7):
                SingleCableTest(i,channel,25)
        elif (test<8 and test>0):
            SingleCableTest(test,channel,25)

        k=input("\n<cr> to return to menu: ")
