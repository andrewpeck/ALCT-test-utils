#!/usr/bin/env python3

################################################################################
# delays.py -- Functions and tests for checking delay ASIC Pattern read/write
################################################################################
#-------------------------------------------------------------------------------
import random
import sys
import os
#-------------------------------------------------------------------------------
import jtaglib as jtag
import common
import alct
import time
import beeper
#-------------------------------------------------------------------------------
import logging
logging.getLogger()
#-------------------------------------------------------------------------------
debug = 0

# converts 1D array[number of chips on board]
#     into 2D array[number of groups][number of chips in group]
def ConvertArray1Dto2D(array,alcttype):
    ngroups = alct.alct[alcttype].groups
    nchips  = 6*ngroups
    out = [[0 for j in range(6)] for i in range(ngroups)]

    for i in range(ngroups):
        for j in range(6):
            out[i][j] = array[i*6 + j]

    return(out)

# converts 2D array[number of groups][number of chips in group]
#     into 1D array[number of chips on board]
def ConvertArray2Dto1D(array,alcttype):
    ngroups = alct.alct[alcttype].groups
    nchips  = 6*ngroups
    out     = [0]*nchips

    for i in range(ngroups):
        for j in range(6):
            array[i*6 + j] =  out[i][j]
    return(out)

# Write Patterns and Delays to Delay Chip
# Patterns and Delays are both stored in array of format
# array[group][chip-in-group]
def SetDelayLines(cs, patterns, delays, alcttype):
    # cs = chip select bitmask
    # patterns = array of patterns to write
    # delays = array of delay values to write
    alct.SetChain(alct.VIRTEX_CONTROL)
    PinMapOnRead = True
    parlen = alct.alct[alcttype].groups + 2  # Length of Data to Write

    for group in range (alct.alct[alcttype].groups):
        if ((cs & 0x7F) & (0x1 << group)) > 0:
            data = 0x1FF & (~((cs & (0x1 << group)) << 2) )

            alct.WriteRegister(alct.DelayCtrlWrite,data,parlen)
            jtag.WriteIR(alct.Wdly, alct.V_IR)

            jtag.StartDRShift()

            for j in range(6):
                DlyVal      =  delays[group][j]
                DlyPtrn     =  patterns[group][j]

                #=== Pin Remapping ===
                if not PinMapOnRead:
                    DlyPtrn=PinRemap(group,j,patterns[group][group])

                DlyValTmp   = jtag.ShiftData(DlyVal, 4, False)
                if j==5:
                    DlyPtrnTmp  = jtag.ShiftData(DlyPtrn, 16, True)
                else:
                    DlyPtrnTmp  = jtag.ShiftData(DlyPtrn, 16, False)

            jtag.ExitDRShift()

            alct.WriteRegister(alct.DelayCtrlWrite,0x1FF,parlen)

# Returns Array of  Delay Chip Patterns read from Board
def ReadPatterns(alcttype):
    ngroups = alct.alct[alcttype].groups
    pattern = [[0 for j in range(6)] for i in range(ngroups)]

    alct.SetChain(alct.VIRTEX_CONTROL)
    Wires = (alct.alct[alcttype].channels)

    PinMapOnRead = True

    #------------------------------------------------------------------------------
    # This is a workaround... kind of silly.. but the easiest way to do it (and
    # not too slow) # A legacy of the old string-based PASCAL/Delphi code, which
    # I haven't yet modified to be a little more sensible:
    #
    # If we write pattern =
    # ABCD EFGH IJKL MNOP QRST UVWX YZ12 3456 7890 (truncated)

    # The Data Register is read LongWord by LongWord (16 bits) in a mixed up order
    # 7809 4356 YZ21 VUWX QRTS NMOP IJLK EFHG BACD

    # This gets reversed completely..
    # DCAB GHFE KLJI POMN STRQ XWUV 12ZY 6534 9087
    #
    # Then if Pin remapping is selected... this rearranges into :
    #       Even Longwords have their last byte flipped
    #       Odd Longwords have their first byte flipped
    #       Then each LongWord is individually reversed
    #       Then we recover our original pattern...
    #       ABCD EFGH IJKL MNOP QRST UVWX YZ12 3456 7890 (truncated)
    #
    # Why is this? I don't know.
    #------------------------------------------------------------------------------

    alct.WriteRegister(0x11, 0x4001, 16)         # Enable Patterns from DelayChips into ALCT Register
    jtag.WriteIR      (0x10, alct.V_IR)          # Send ALCT Register to PC via JTAG
    DR = jtag.ReadDR  (0x0,Wires) & (2**Wires-1) # Read Data and Mask off one bit for each channel

    if alcttype==0:
        fmt = '072X'
    elif alcttype==1:
        fmt = '096X'
    elif alcttype==2:
        fmt = '0168X'

    stringDR = format(DR, fmt)               # Convert to Hexdecimal string
    stringDR = stringDR[::-1]                   # Invert the String

    for i in range(alct.alct[alcttype].groups):
        for j in range(6):
            num = int(stringDR[0:4],16)         # extract the first four hex digits
            stringDR = stringDR[4:]             # cut off first 4 hex digits since we are done with them

            pattern[i][j] = (num) & 0xFFFF
            # Invert the patterns
            if PinMapOnRead:
                pattern[i][j]=PinRemap(i,j,pattern[i][j])

            stringPat = hex(pattern[i][j])
            stringPat = stringPat[2:]
            stringPat = stringPat.zfill(4)
            stringPat = stringPat[::-1]
            pattern[i][j]=int(stringPat,16)
    return(pattern)

# Remaps pins according to some scheme..
# Please see notes accompanying ReadPatterns
def PinRemap(i,j,pattern):
    a = pattern & 0xFF00
    b = pattern & 0x00FF
    tmp = 0
    if (j % 2)==0:
        for k in range(8):
            bit = 0x1 & (pattern >> 7-k)
            tmp = tmp | (bit << (k))
        tmp = tmp & 0x00FF
        pattern = a | tmp

    if (j % 2)==1:
        for k in range(8):
            bit = 0x1 & (pattern >> 15-k)
            tmp = tmp | (bit << (k+8))
        tmp = tmp & 0xFF00
        pattern = tmp | b
    return (pattern)

# Checks two patterns arrays against eachother---returns number of Errors found
def CheckPatterns(SendPtrns, ReadPtrns,alcttype):
    Errs = 0
    for i in range(alct.alct[alcttype].groups):       # Loop over number of groups
        for j in range(6):                            # Loop over number of chips in a group
            for bit in range (16):                    # Loop over number of channels in a chip
                if ((ReadPtrns[i][j] >> bit) & 0x1) != ((SendPtrns[i][j] >> bit) & 0x1):
                    Errs = Errs + 1
    return(Errs)

# Make some nice output of sent/received patterns
def PrintPatterns(alcttype, SendPtrns, ReadPtrns):
    sentstr = ''
    readstr = ''
    output  = ''
    for i in range(alct.alct[alcttype].groups):
        for j in range(6):
            sentstr = ("%04X" % SendPtrns[i][j]) + ' ' + sentstr
            readstr = ("%04X" % ReadPtrns[i][j]) + ' ' + readstr
    output += ('\n\t ->Sent: %s' % sentstr)
    output += ('\n\t <-Read: %s' % readstr)
    print(output)

def WalkingBit(sign,alcttype):
    ngroups = alct.alct[alcttype].groups
    SendPtrns  = [[0 for j in range(6)] for i in range(ngroups)]
    ReadPtrns  = [[0 for j in range(6)] for i in range(ngroups)]
    SendValues = [[0 for j in range(6)] for i in range(ngroups)]

    Wires = alct.alct[alcttype].channels
    Errs        = 0
    ErrOnePass  = 0
    fStop       = False
    fStopOnError= True

    if sign==1:
        print('    Walking 1 Test')
    elif sign==0:
        print('    Walking 0 Test')
    else:
        raise Exception("Invalid test selected")

    alct.SetChain(alct.VIRTEX_CONTROL)

    for bit in range(Wires):
        alct.WriteRegister(0x11,0x4000,16)

        for i in range(alct.alct[alcttype].groups):
            for j in range(6):
                if sign==1:
                    SendValues[i][j]    = 0
                    SendPtrns [i][j]    = 0 or ((bit // 16) == ((i*6)+j)) << (bit % 16)
                    ReadPtrns [i][j]    = 0
                if sign==0:
                    SendValues[i][j] = 0x0000
                    SendPtrns [i][j] = 0xFFFF & (~(((bit//16)==((i*6)+j)) << (bit%16)))

        SetDelayLines(0x7F, SendPtrns, SendValues, alcttype)
        ReadPtrns = ReadPatterns(alcttype)

        ErrOnePass = CheckPatterns(SendPtrns, ReadPtrns,alcttype)
        Errs = Errs + ErrOnePass
        if (ErrOnePass > 0):
            print("\t    Error on bit %3i (Chip #%2i Channel %2i)" % (bit+1, bit//16 + 1, bit%16 + 1 ))
        else:
            common.Printer("\tBit %3i of %3i" % (bit+1,Wires))

        #PrintPatterns(alcttype, SendPtrns, ReadPtrns)

    # Fini
    print('')
    if (Errs == 0):
        if sign==1:
            print       ('\tPASSED: Walking 1 Test')
            logging.info('\tPASSED: Walking 1 Test')
        if sign==0:
            print       ('\tPASSED: Walking 0 Test')
            logging.info('\tPASSED: Walking 0 Test')
        beeper.passed()
    else:
        if sign==1:
            print       ('\tFAILED: Walking 1 Test Finished with %i Errors ' % Errs)
            logging.info('\tFAILED: Walking 1 Test Finished with %i Errors ' % Errs)
        if sign==0:
            print       ('\tFAILED: Walking 0 Test Finished with %i Errors ' % Errs)
            logging.info('\tFAILED: Walking 0 Test Finished with %i Errors ' % Errs)
        beeper.failed()
    return (Errs)

# Sends a walking 1 pattern through the delay ASICs
def Walking1(alcttype):
    errs=WalkingBit(1,alcttype)
    return(errs)

# Sends a walking 1 pattern through the delay ASICs
def Walking0(alcttype):
    errs=WalkingBit(0,alcttype)
    return(errs)

def FillingBit(sign,alcttype):
    ngroups = alct.alct[alcttype].groups
    SendPtrns  = [[0 for j in range(6)] for i in range(ngroups)]
    SendValues = [[0 for j in range(6)] for i in range(ngroups)]

    Wires = alct.alct[alcttype].channels
    Errs       = 0
    ErrOnePass = 0
    fStop      = False

    if sign==1:
        print       ('    Filling 1s Test')
    elif sign==0:
        print       ('    Filling 0s Test')
    else:
        raise Exception("Invalid Test Selected")

    alct.SetChain(alct.VIRTEX_CONTROL)

    for i in range(alct.alct[alcttype].groups):
        for j in range(6):
            if sign==1:
                SendValues[i][j] = 0x0000
                SendPtrns [i][j] = 0x0000
            if sign==0:
                SendValues[i][j] = 0x0000
                SendPtrns [i][j] = 0xFFFF

    SetDelayLines(0xF,SendPtrns,SendValues,alcttype)

    for bit in range (Wires):
        alct.WriteRegister(0x11,0x4000,0x16)

        for i in range(alct.alct[alcttype].groups):
            for j in range(6):
                if sign==1:
                    SendValues[i][j] = 0
                    SendPtrns [i][j] = SendPtrns[i][j] | (((bit//16) == ((i*6)+j)) << (bit % 16))
                if sign==0:
                    SendValues[i][j] = 0x0000
                    SendPtrns [i][j] = SendPtrns[i][j] & (~(((bit // 16) == ((i*6)+j)) << (bit % 16)))

        SetDelayLines(0xF, SendPtrns, SendValues, alcttype)
        ReadPtrns = ReadPatterns(alcttype)

        ErrOnePass = CheckPatterns(SendPtrns, ReadPtrns,alcttype)
        Errs       = Errs + ErrOnePass
        if (ErrOnePass > 0):
            print("\t    Error on bit %3i (Possible Problem with Chip #%2i Channel %2i" % (bit+1, bit//16 + 1, bit%16 + 1 ))
        else:
            common.Printer("\tBit %3i of %3i" % (bit+1,Wires))
    # Fini
    print('')
    if (Errs==0):
        if sign==1:
            print       ('\tPASSED: Filling by 1s Test')
            logging.info('\tPASSED: Filling by 1s Test')
        if sign==0:
            print        ('\tPASSED: Filling by 0s Test')
            logging.info ('\tPASSED: Filling by 0s Test')
        beeper.passed()
    else:
        if sign==1:
            print       ('\tFAILED: Filling by 1s Test Finished with %i Errors ' % Errs)
            logging.info('\tFAILED: Filling by 1s Test Finished with %i Errors ' % Errs)
        if sign==0:
            print        ('\tFAILED: Filling by 0s Test Finished with %i Errors ' % Errs)
            logging.info ('\tFAILED: Filling by 0s Test Finished with %i Errors ' % Errs)
        beeper.failed()

    return (Errs)

# Fills delay ASICs with a Walking 1
def Filling1(alcttype):
    return(FillingBit(1,alcttype))

# Unfills delay ASICs with a Walking 0
def Filling0(alcttype):
    return(FillingBit(0,alcttype))

# Shifts 5 and A through the delay asic... 0101010101 --> 10101010101..
# Uses HIGH current.. maybe not a good test.
def Shifting5andA(alcttype, npasses=10):
    ngroups = alct.alct[alcttype].groups
    SendPtrns  = [[0 for j in range(6)] for i in range(ngroups)]
    SendValues = [[0 for j in range(6)] for i in range(ngroups)]

    Wires       = (alct.alct[alcttype].channels) #Number of wires on this kind of board

    # Initialize Vars
    Errs        = 0
    ErrOnePass  = 0
    fStop       = False

    print        ('    Shifting 5 and A Test')

    alct.SetChain(alct.VIRTEX_CONTROL)
    for p in range(npasses):
        time.sleep(.2)  # DO NOT TAKE THIS SLEEP OUT
                        # The delay chips cannot handle Shifting too fast
                        # (causes overcurrent on the board, esp. ALCT-672)


        alct.WriteRegister(0x11,0x4000,0x16)

        for i in range(alct.alct[alcttype].groups):
            for j in range(6):
                SendValues[i][j]        = 0     # delay value to set
                if ((p+1) % 2)==1:
                    SendPtrns[i][j] = 0x5555    # delay pattern to set even/odd
                else:
                    SendPtrns[i][j] = 0xAAAA    # delay pattern to set even/odd


        SetDelayLines(0xF, SendPtrns, SendValues, alcttype) # write delay patterns/values
        ReadPtrns = ReadPatterns(alcttype)             # read delay patterns
        ErrOnePass      = CheckPatterns(SendPtrns, ReadPtrns,alcttype)
        Errs            = Errs + ErrOnePass

        # Generate a hexdecimal formatted string of the read/write patterns
        read = "0x"
        send = "0x"
        for i in range(alct.alct[alcttype].groups):
            read = read + format(ReadPtrns[i][j],'04X')
            send = send + format(SendPtrns[i][j],'04X')

        if ErrOnePass > 0:
            print("        Pass %2i of %2i" % (p+1, npasses))
            print("            Error: Write=%s Read=%s " % (send, read))
        else:
            if debug:
                print ("    Pass %2i of %2i" % (p+1, npasses))
                print("\tPASSED")
            else:
                common.Printer ("        Pass %2i of %2i Write=%s Read=%s" % (p+1, npasses,send, read))

    # Reset Delay Chips (returns Current to normal values
    for i in range(alct.alct[alcttype].groups):
        for j in range(6):
            SendValues [i][j] = 0x0000
            SendPtrns  [i][j] = 0x0000
    SetDelayLines(0xF, SendPtrns, SendValues, alcttype)

    # Fini
    print('')
    if (Errs == 0):
        print        ('\tPASSED: Shifting 5 and A Test')
        logging.info ('\tPASSED: Shifting 5 and A Test')
        beeper.passed()
    else:
        print        ('\tFAILED: Shifting 5 and A Test Finished with %i Errors ' % Errs)
        logging.info ('\tFAILED: Shifting 5 and A Test Finished with %i Errors ' % Errs)
        beeper.failed()

    return (Errs)

# Sends random patterns into delay ASICs
def RandomData(alcttype, npasses=25):
    ngroups = alct.alct[alcttype].groups
    SendPtrns  = [[0 for j in range(6)] for i in range(ngroups)]
    SendValues = [[0 for j in range(6)] for i in range(ngroups)]

    # Wires
    Wires = alct.alct[alcttype].channels

    # Number of errors
    Errs       = 0
    ErrOnePass = 0
    fStop      = False

    print        ('    Random Data Test')

    # Select virtex control register
    alct.SetChain(alct.VIRTEX_CONTROL)

    # Seed random number generator
    random.seed()

    for p in range(npasses):
        time.sleep(0.1)

        alct.WriteRegister(0x11,0x4000,0x16)

        # Set Delay ASICs with random patterns
        for i in range(alct.alct[alcttype].groups):
            for j in range(6):
                SendValues[i][j]    = 0
                SendPtrns[i][j]     = random.getrandbits(16)
        SetDelayLines(0xF, SendPtrns, SendValues, alcttype)

        ReadPtrns  = ReadPatterns(alcttype)
        ErrOnePass = CheckPatterns(SendPtrns, ReadPtrns,alcttype)
        Errs       = Errs + ErrOnePass

        # Generate a hexdecimal formatted string of the read/write patterns
        read = "0x"
        send = "0x"
        for i in range(alct.alct[alcttype].groups):
            read = read + format(ReadPtrns[i][0],'04X')
            send = send + format(SendPtrns[i][0],'04X')

        # If error, print pattern
        if ErrOnePass > 0:
            print("        Pass %2i of %2i" % (p+1, npasses))
            print("            Error: Write=%s Read=%s " % (send, read))
        else:
            if debug:
                print ("    Pass %i of %i" % (p+1, npasses))
                print("\tPASSED")
            else:
                common.Printer ("        Pass %2i of %2i Write=%s Read=%s" % (p+1, npasses,send, read))

    # Reset Delay Chips (returns Current to normal values
    for i in range(alct.alct[alcttype].groups):
        for j in range(6):
            SendValues[i][j] = 0x0000
            SendPtrns [i][j] = 0x0000

    SetDelayLines(0xF, SendPtrns, SendValues, alcttype)

    # Fini
    print('')
    if (Errs==0):
        print        ('\tPASSED: Random Data Test')
        logging.info ('\tPASSED: Random Data Test')
        beeper.passed()
    else:
        print        ('\tFAILED: Random Data Test Finished with %i Errors ' % Errs)
        logging.info ('\tFAILED: Random Data Test Finished with %i Errors ' % Errs)
        beeper.failed()
    return (Errs)

def SubtestMenu(alcttype):
    while True:
        common.ClearScreen()
        print("\n===============================================================================")
        print(  " Delay Chips Test Submenu")
        print(  "===============================================================================\n")
        print("    0 Run All Tests")
        print("    1 Walking 1 Test")
        print("    2 Walking 0 Test")
        print("    3 Filling 1 Test")
        print("    4 Filling 0 Test")
        print("    5 Shifting 5 and A Test")
        print("    6 Random Data Test")

        k=input("\nChoose Test or <cr> to return to Main Menu: ")
        common.ClearScreen()
        print("")
        if not k: break

        if k=="0": PatternsSelfTest(alcttype)
        if k=="1": Walking1(alcttype)
        if k=="2": Walking0(alcttype)
        if k=="3": Filling1(alcttype)
        if k=="4": Filling0(alcttype)
        if k=="5": Shifting5andA(alcttype)
        if k=="6": RandomData(alcttype)

        k=input("\n<cr> to return to menu: ")

def PatternsSelfTest(alcttype):
    Errs = 0
    Errs += Walking1(alcttype)
    Errs += Walking0(alcttype)
    Errs += Filling1(alcttype)
    Errs += Filling0(alcttype)
    Errs += Shifting5andA(alcttype)
    Errs += RandomData(alcttype)
    return (Errs)
