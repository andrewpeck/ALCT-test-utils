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
from config import logFile

TestNames = ['',                #Dummy entry to number from 1
             'Custom Data ',
             'Walking 1   ', 
             'Walking 0   ', 
             'Filling 1   ', 
             'Filling 0   ', 
             'Shifting 5/A', 
             'Random Data ']

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
    test                   -= 1             # we enumerate from zero inside code, but from 1 in the interface


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
    for npass in range(npasses):
        for bit in range(multiple): 

            if (test==0 and npass==0 and bit==0):                               # 0 = Custom Data Test
                k=input("\nEnter Custom Data or <cr> for %04X" % CustomData)
                senddata=CustomData 
            if test==1: senddata = 0x0000   |   (0xFFFF & (1 << (bit % 16)))    # 1 = Walking 1 Test
            if test==2: senddata = 0xFFFF   & (~(0xFFFF & (1 << (bit % 16))))   # 2 = Walking 0 Test
            if test==3:                                                         # 3 = Filling 1 Test
                if bit%16==0: senddata=0x0001
                else: senddata = senddata | (0xFFFF & (1 << (bit % 16)))
            if test==4:                                                         # 4 = Filling 0 Test
                if bit%16 == 0: senddata=0xFFFE
                else: senddata = senddata & (~(0xFFFF & (1 << (bit % 16))))
            if test==5:                                                         # 5 = Shifting 5 and A
                if    ((bit+1) % 2)==1: senddata = 0x5555
                else:                   senddata = 0xAAAA
            if test==6: senddata = random.getrandbits(16)                       # 6 = Random Data

            if bit==0: print ('\t Pass %2i' % (npass+1))

            # Select Channel
            alct.WriteRegister(alct.DelayCtrlWrite,0x1FF & channel,9)
            alct.ReadRegister(alct.DelayCtrlRead,9)

            # Write Data
            alct.WriteRegister(0x18,0xFFFF & senddata,16)

            # Read Back Data
            readdata = alct.ReadRegister(0x17,16)

            #if readdata != senddata:
            #    errcnt += 1
            #    #if ((not SuppressErrsSingleCable) or (SuppressErrsSingleCable and (errcnt <= ErrCntSingleTest))):
            #    print('\t ERROR: Set Mask Register to 0x%04X Readback 0x%04X' % (senddata,readdata))

            #    if StopOnErrorSingleCable:
            #        return(0)

            # Select Channel
            alct.WriteRegister(alct.DelayCtrlWrite, channel | 0x40, 9)

            # Read Data
            alct.WriteRegister(alct.DelayCtrlWrite, channel | 0x1FF, 9)
            readdata = alct.ReadRegister(0x19, 16)

            if (readdata != senddata):
                errcnt += 1
                print("\t\t ====> Fail: ", end="")
                if StopOnErrorSingleCable:
                    return(0)
            else: 
                print("\t\t ====> Pass: ", end="")

            print('Read=0x%04X Expect=0x%04X' % (readdata,senddata))

    if errcnt==0:
        print('\n\t ====> Passed')
    else:
        print('\n\t ====> Failed Single Cable Test with %i Errors' % errcnt)
    return (errcnt)

def SingleCableSelfTest(alcttype,logFile):
    print("\n%s > Starting Single Cable Automatic Test\n" % common.Now())
    errcnt = 0 

    logFile.write("\nStarting Single Cable Self Test:")
    for (channel) in range (alct.alct[alcttype].groups * alct.alct[alcttype].chips):
        k = input ("Please connect ALCT connector J5 to AFEB connector %i. s to skip, <cr> to continue" % channel)

        # skip connector
        if (k=="s" or k=="S"): 
            errcnt += 1
            continue

        # perform all tests for this AFEB
        else: 
            logFile.write("\n\tSingle Cable Test on Channel %i" % channel)
            for i in range(1,7): #prefer NOT to do custom data test for the Self-Test 
                fail = SingleCableTest(i,0,10)
                if fail: 
                    errcnt += fail
                    logFile.write("\n\t\t ====> Failed %s with %3i Errors" % (TestNames[i], fail))
                else: 
                    logFile.write("\n\t\t ====> Passed %s " % TestNames[i])

    # Tests Summary

    print        ("Summary:")
    logFile.write("\n\tSummary:")

    if errcnt==0:
        print        ('\n\t ====> Passed')
        logFile.write('\n\t\t ====> Passed Single Cable Test')
    else:
        print        ('\n\t ====> Failed Single Cable Test with %i Total Errors' % errcnt)
        logFile.write('\n\t\t ====> Failed Single Cable Test with %i Total Errors' % errcnt)

    return (errcnt) 

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
