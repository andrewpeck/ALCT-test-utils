#!/usr/bin/env python3

################################################################################
# Tools for Verifying delays ASICs using the large external test board
################################################################################

#-------------------------------------------------------------------------------
import alct
import jtaglib as jtag
import common
import slowcontrol
#-------------------------------------------------------------------------------
import logging
logging.getLogger()
#-------------------------------------------------------------------------------
import os
import time
#-------------------------------------------------------------------------------

debug=False

#-------------------------------------------------------------------------------
# Register Locations / Sizes
#-------------------------------------------------------------------------------

# Some commands definitions..
FIFO_RESET = 0xC
FIFO_READ  = 0xA
FIFO_WRITE = 0x9

# Some registers used for Tester board tests
RdDataReg           = 0x01
RdCntReg            = 0x02
WrDatF              = 0x04
WrAddF              = 0x06
WrParamF            = 0x08
RdParamDly          = 0x15
WrParamDly          = 0x16 # Change for Different Boards!!
WrDlyF              = 0x0B
Wdly                = 0x0D
Rdly                = 0x0E
WrFIFO              = 0x0A

#length of the previous registers
lengthOf = {
        0x01:  16, # RdDataReg
        0x02: 128, # RdCntReg
        0x04:  16, # WrDatF
        0x06:  10, # WrAddF
        0x08:   4, # WrParamF
        0x15:   6, # RdParamDly
        0x0B:   8, # WrDlyF
        0x0D: 120, # Wdly
        0x0E: 120, # Rdly
        0x0A:   1} # WrFIFO

################################################################################
# Low Level Test Board FIFO Functions
################################################################################

def SetFIFOChannel(ch,startdly):
    alct.WriteRegister(WrAddF, ch | startdly << 6, lengthOf[WrAddF])

def SetFIFOMode(mode):
    alct.WriteRegister(WrParamF, (0x8 | mode) & 0xF, lengthOf[WrParamF])

def SetFIFOReset():
    alct.WriteRegister(WrParamF,8,          lengthOf[WrParamF])
    alct.WriteRegister(WrParamF,FIFO_RESET, lengthOf[WrParamF])
    alct.WriteRegister(WrParamF,8,          lengthOf[WrParamF])

def SetFIFOWrite():
    alct.WriteRegister(WrParamF,FIFO_WRITE, lengthOf[WrParamF])

def SetFIFORead():
    alct.WriteRegister(WrParamF,FIFO_READ, lengthOf[WrParamF])

def SetFIFOReadWrite():
    alct.WriteRegister(WrParamF,FIFO_WRITE | FIFO_READ, lengthOf[WrParamF])

def FIFOClock():
    alct.WriteRegister(WrFIFO,0x1, lengthOf[WrFIFO])

def ReadFIFOCounters():
    return(alct.ReadRegister(RdCntReg,lengthOf[RdCntReg]))

def SetFIFOValue(val):
    alct.WriteRegister(WrDatF,val, lengthOf[WrDatF])

def SetTestBoardDelay(delay):
    alct.WriteRegister(WrParamF, FIFO_RESET,                                 lengthOf[WrParamF])
    alct.WriteRegister(WrDlyF,   0xFF & common.FlipByte((255-delay) & 0xFF), lengthOf[WrDlyF])
    alct.WriteRegister(WrParamF, 0x8,                                        lengthOf[WrParamF])

def SetALCTBoardDelay(ch, delay, alcttype):
    DelayValue   = [0x0] * 6 # 6 delay chips in group
    DelayPattern = [0x0] * 6 # 6 delay chips in group
    DelayValue[ch % 6] = delay
    if debug: print(DelayPattern)
    if debug: print(DelayValue)
    Write6DelayLines(DelayPattern, DelayValue, 1 << (ch // 6), alcttype)

#unused ? 
#def SetTestBoardFIFO(fifoval, fifochan, numwords, startdelay, alctdelay, testboarddelay, alcttype):
#    numwords        = 1
#    startdelay      = 2
#    alctdelay       = 0
#    testboarddelay  = 0
#
#    SetFIFOReset()
#    SetFIFOChannel(fifochan, startdelay)
#    SetFIFOValue(fifoval)
#    SetTestBoardDelay(testboarddelay)
#    SetALCTBoardDelay(fifochan, alctdelay, alcttype)
#    SetFIFOWrite
#    for i in range(1,numwords+1):
#        FIFOClock

def ReadFIFOValue():
    return(alct.ReadRegister(RdDataReg,lengthOf[RdDataReg]))

def ALCTEnableInput(alcttype):
    parlen = alct.alct[alcttype].groups + 2
    alct.WriteRegister(WrParamDly,0x1FD,parlen)
    return(alct.ReadRegister(RdParamDly,parlen))

def ALCTDisableInput(alcttype):
    parlen = alct.alct[alcttype].groups + 2
    alct.WriteRegister(WrParamDly,0x1FF,parlen)
    return(alct.ReadRegister(RdParamDly,0x1FD,parlen))

def ReadFIFO(numwords, alcttype):
    SetFIFOReset()
    SetFIFOWrite()
    FIFOClock()
    SetFIFOReadWrite()
    ALCTEnableInput(alcttype)

    jtag.WriteIR(WrFIFO,alct.V_IR)             # FIFOClock
    for i in range(numwords):
        jtag.WriteDR(0x1,lengthOf[WrFIFO])     # FIFOClock

    # TODO: 
    # This really sucks please fix it..
    # Have a look at http://stackoverflow.com/questions/7983684/how-to-switch-byte-order-of-binary-data

    cntstr=format(ReadFIFOCounters(), '032X')  # Convert int to string
    cntstr = cntstr[::-1]                      # Reverse String (change endianess)

    cntrs = [0]*16 # "array of byte"
    for i in range (16):
        num = int(cntstr[:2],16)    # We extract the first byte (2 hex characters) and convert them to an integer
        cntstr = cntstr[2:]         # Remove the extracted bytes from the string for the next pass. 
        cntrs[15-i] = num           # fill cntrs array

    return(cntrs)


# Configure FIFO data, channel, ALCT board delays, test board delays
def SetDelayTest(fifoval, fifochan, startdelay=2, alctdelay=0x0000, testboarddelay=0, alcttype=0):
    SetFIFOChannel(fifochan, startdelay)
    SetFIFOValue(fifoval)
    SetTestBoardDelay(testboarddelay)
    SetALCTBoardDelay(fifochan, alctdelay, alcttype)

#-------------------------------------------------------------------------------
# Tester Board Analysis Functions
#-------------------------------------------------------------------------------

def PinPointRiseTime(FIFOvalue, ch, StartDly, alct_dly, num, alcttype):
    return(PinPointTime(FIFOvalue, ch, StartDly, alct_dly, num, alcttype, "rise"))

def PinPointFallTime(FIFOvalue, ch, StartDly, alct_dly, num, alcttype):
    return(PinPointTime(FIFOvalue, ch, StartDly, alct_dly, num, alcttype, "fall"))

def PinPointTime(FIFOvalue, ch, StartDly, alct_dly, num, alcttype, edge):
    # Initialize Values
    tb_dly           = 0         # Initial Test Board Delay
    RegisterMaskDone = 0
    FirstChn         = False     # Is First Channel? 
    cntrs            = [0]*16 # "array of byte"
    Time             = [0]*16 # another array of bytes

    # Load data into FIFO, set ALCT ASIC delay. Also sets an initial value for
    # test-board delay but this will be overwritten.. 
    SetDelayTest(FIFOvalue, ch, StartDly, alct_dly, tb_dly, alcttype)


    # Now look more closely (we now step by individual delay values, rather
    # than multiples of 10)
    if edge=="rise": 

        # Get an idea of where the pulse rise is, stepping in increments 0,10,20...250
        # Once we see a pulse, go decrement the delay by 10 and then perform the deep scan
        # This is just here as a way to speed up the test... 
        for j in range(26):
            tb_dly = 10*j
            SetTestBoardDelay(tb_dly)
            cntrs = ReadFIFO(num, alcttype)

            for i in range(16):
                if(cntrs[i] > 0) and ((FIFOvalue & (1 << i))>0):
                    FirstChn = True
            if (FirstChn): 
                tb_dly = 10*(j-1)
                break

        # Now do a full scan
        for dly in range(tb_dly,256):
            # Set Delay
            SetTestBoardDelay(dly)

            # Read out data
            cntrs = ReadFIFO(num, alcttype)

            # Loop over chip channels and check if they saw something
            for i in range (16):
                if (cntrs[i]>(num/2)) and ((FIFOvalue & (1 << i))>0) and ((RegisterMaskDone & (1 << i))==0):
                    Time[i] = dly+1
                    RegisterMaskDone = RegisterMaskDone | (1 << i)

            # Break when we see a pulse. In the normal tests, FIFOvalue is
            # 0xFFFF, so of course we mean a pulse on ALL channels
            if (RegisterMaskDone == FIFOvalue):
                break

    if edge=="fall":
        for dly in range (256):
            SetTestBoardDelay(dly)
            cntrs = ReadFIFO(num, alcttype)

            for i in range(16):
                if edge=="fall": 
                    if (cntrs[i]<(num/2)) and ((FIFOvalue & (1 << i))>0) and ((RegisterMaskDone & (1 << i))==0):
                        Time[i] = dly
                        RegisterMaskDone = RegisterMaskDone | (1 << i)
            if (RegisterMaskDone == FIFOvalue):
                break
    return(Time)

def FindStartDly(FIFOvalue, ch, alct_dly, num_words, alcttype):
    (FoundTimeBin, StartDly_R, StartDly_F,RegMaskDone) = FindStartDlyPin(FIFOvalue, ch, alct_dly, num_words, 0, alcttype)
    return (FoundTimeBin, StartDly_R, StartDly_F)

# function returns: 
#   bool FoundTimeBin       - true/false basically redundant with RegMaskDone
#   int  StartDly_R         - Delay value when a rising  pulse was first seen on any channel
#   int  StartDly_F         - Delay value when a falling pulse was first seen on any channel
#   int  RegMaskDone        - 16 bit mask that a channel has seen both rising and falling edges
def FindStartDlyPin(FIFOvalue, ch, alct_dly, num_words, RegMaskDone, alcttype):
    if debug: print('Find Start Dly')
    alct.SetChain(alct.VIRTEX_CONTROL)
    FoundTimeBin    = False # Found time bin ?
    FirstChnR       = False # First Channel Rise
    AllChnR         = False # All Channels Rise
    FirstChnF       = False # First Channel Fall
    AllChnF         = False # All Channels Fall
    RegMaskDoneR    = 0     # Rising edge of pulse has been seen?
    RegMaskDoneF    = 0     # Falling edge of pulse has been seen? 
    MaxChannelsCntr = 0     
    StartDly_R      = 5     # Rise Start Delay
    StartDly_F      = 5     # Fall Start Delay
    StartDly        = 5
    tb_dly          = 0     # Test board delay
    cntrs           = [0x00]*16 # "array of byte"

    SetDelayTest(FIFOvalue, ch, StartDly, alct_dly, tb_dly, alcttype)

    for StartDly in range (5,16):

        # Select Channel
        SetFIFOChannel(ch, StartDly)

        # Read FIFO into a 16 entry array. 
        # Each entry is a byte of data, with 16 entries for channel 0-15
        cntrs = ReadFIFO(num_words, alcttype)

        # Initialize vars
        ChannelsCntr = 0
        MaskDoneR    = 0

        # Fill Counters with FIFO Bitmask
        # Loop over all the channels.. 
        # Check that ___ and that there should be data in that channel
        for i in range(16):
            if (cntrs[i] > (num_words/2)) and ((FIFOvalue & (1 << i))>0):
                ChannelsCntr += 1
                MaskDoneR |= (1 << i)

        # Mark whether ALL channels have seen a rising edge
        if (MaskDoneR == FIFOvalue):
            AllChnR = True

        # Check if ANY channel has seen something, and call this the Rising Start Delay
        if (ChannelsCntr > 0):
            FirstChnR = True
        if (not FirstChnR):
            StartDly_R = StartDly
        # If the rising edge has already been seen... start looking for the falling edge: 
        else:
            # If the number of channels seeing a pulse is still equal the
            # number of channels.. then we haven't seen the falling edge
            if ((ChannelsCntr > 0) and (ChannelsCntr >= MaxChannelsCntr)):
                MaxChannelsCntr = ChannelsCntr
                StartDly_F      = StartDly
                RegMaskDoneR    = MaskDoneR
            # At least one channel is not seeing a pulse.. so we've seen a falling edge.. 
            else:
                FirstChnF = True

        # If we've seen at least one channel Fall: 
        if (FirstChnF):
            MaskDoneF = 0
            # Loop over all the channels.. make a bitmask of which channels have seen falling edge
            for i in range (16):
                if (cntrs[i] < (num_words/2)) and ((FIFOvalue & (1 << i))>0):
                    MaskDoneF = MaskDoneF | (1 << i)

            RegMaskDoneF = MaskDoneF

            # If ALL marked channels have fallen: 
            if (MaskDoneF == FIFOvalue):
                AllChnF = True

        # If all channels rose and fell.. then we found a time bin for everything: 
        if (AllChnR and AllChnF):
            FoundTimeBin = True
            break

    # Failed to Find Start Delay? then call it 5..
    if (not FirstChnR):
        StartDly_R = 5

    # Conflate the Rising and Falling edge bitmasks 
    RegMaskDone = RegMaskDoneR & RegMaskDoneF

    # Return tuple of values
    return(FoundTimeBin, StartDly_R, StartDly_F, RegMaskDone)

def MeasureDelay(chip, PulseWidth, BeginTime_Min, DeltaBeginTime, Delay_Time, AverageDelay_Time, RegMaskDone, alcttype):
    MinWidth       = 30
    MaxWidth       = 45
    FIFOvalue      = 0xFFFF
    num            = 100
    ErrMeasDly     = 0
    PulseWidth_min = 0

    # initialize arrays
    TimeR_0        = [0x0]*16
    TimeF_0        = [0x0]*16
    TimeR_15       = [0x0]*16
    DelayTimeR_0   = [0x0]*16
    DelayTimeF_0   = [0x0]*16
    DelayTimeR_15  = [0x0]*16

    # write zeroes to arrays from args
    for i in range(16):
        PulseWidth[i]           = 0
        DeltaBeginTime[chip][i]   = 0
        Delay_Time[chip][i]       = 0

    # 
    alct_dly        = 0
    StartDly_R      = 0
    StartDly_F      = 0

    (FoundTimeBin, StartDly_R, StartDly_F,RegMaskDone) = FindStartDlyPin(FIFOvalue, chip, alct_dly, num, RegMaskDone,alcttype)
    if FoundTimeBin:
        TimeR_0 = PinPointRiseTime(FIFOvalue, chip, StartDly_R, alct_dly, num,alcttype)
        TimeF_0 = PinPointFallTime(FIFOvalue, chip, StartDly_F, alct_dly, num,alcttype)

        BeginTime_Min[chip] = StartDly_R*25 + 255*0.25
        for i in range(16):
            DelayTimeR_0[i] = StartDly_R*25 + TimeR_0[i]*0.25
            DelayTimeF_0[i] = StartDly_F*25 + TimeF_0[i]*0.25
            PulseWidth[i]   = DelayTimeF_0[i] - DelayTimeR_0[i]

            if (i==0):
                PulseWidth_Min = PulseWidth[i]
                PulseWidth_Max = PulseWidth[i]

            if (DelayTimeR_0[i] < BeginTime_Min[chip]):
                BeginTime_Min[chip] = DelayTimeR_0[i]

            if (PulseWidth[i] < PulseWidth_Min):
                PulseWidth_Min = PulseWidth[i]

            if (PulseWidth[i] > PulseWidth_Max):
                PulseWidth_Max = PulseWidth[i]
    else:
        ErrMeasDly = ErrMeasDly | 0x1
        return(0)

    #------------------------------------------------------------------------------

    alct_dly = 15
    AverageDelay_Time[chip] = 0
    SumDelay_Time = 0

    (FoundTimeBin, StartDly_R, StartDly_F) = FindStartDly(FIFOvalue, chip, alct_dly, num, alcttype)
    if FoundTimeBin:
        TimeR_15 = PinPointRiseTime(FIFOvalue, chip, StartDly_R, alct_dly, num, alcttype)
        for i in range(16):
            DelayTimeR_15[i]    = StartDly_R*25 + TimeR_15[i]*0.25
            Delay_Time[chip][i] = DelayTimeR_15[i] - DelayTimeR_0[i]
            SumDelay_Time       = SumDelay_Time + Delay_Time[chip][i]

        AverageDelay_Time[chip] = SumDelay_Time / 16
    else:
        ErrMeasDly = ErrMeasDly | 0x2

    if (PulseWidth_Min < MinWidth):
        ErrMeasDly = ErrMeasDly | 0x4

    if (PulseWidth_Max > MaxWidth):
        ErrMeasDly = ErrMeasDly | 0x8

    for i in range(16):
        DeltaBeginTime[chip][i] = DelayTimeR_0[i] - BeginTime_Min[chip]
        #if (DeltaBeginTime[chip][i] > MaxDeltaBeginTime) then
        #    ErrMeasDly |= 0x10
        # This was commented out in PASCAL.. for whatever reason

    return(ErrMeasDly)

#def PrepareDelayLinePatterns(dlys, image):
#    for i in range (0,4):
#        dlys[i][0].Pattern = common.FlipByte(image[1][i*2]) | (word(image[4][i*2]) << 8)
#        dlys[i][1].Pattern = common.FlipByte(image[1][i*2]) | (word(image[4][i*2]) << 8)
#        dlys[i][2].Pattern = common.FlipByte(image[1][i*2]) | (word(image[4][i*2]) << 8)
#        dlys[i][3].Pattern = common.FlipByte(image[1][i*2]) | (word(image[4][i*2]) << 8)
#        dlys[i][4].Pattern = common.FlipByte(image[1][i*2]) | (word(image[4][i*2]) << 8)
#        dlys[i][5].Pattern = common.FlipByte(image[1][i*2]) | (word(image[4][i*2]) << 8)


# Writes Pattern and Value to 6 Groups of Delay Chips
def Write6DelayLines(DelayPattern, DelayValue, mask, alcttype):
    alct.SetChain(alct.VIRTEX_CONTROL)
    parlen = alct.alct[alcttype].groups + 2

    # Reset Delays
    alct.WriteRegister(alct.DelayCtrlWrite, 0x1FF & (~(mask << 2)), parlen)
    alct.ReadRegister (alct.DelayCtrlRead, parlen)

    # Start JTAG data shift to write Delay Batterns
    jtag.WriteIR(alct.Wdly, alct.V_IR)
    jtag.StartDRShift()
    for i in range(6):
        jtag.ShiftData(common.FlipHalfByte(DelayValue[i]), 4, False)
        if i==5:
            jtag.ShiftData(DelayPattern[i], 16, True)
        else:
            jtag.ShiftData(DelayPattern[i], 16, False)
    jtag.ExitDRShift()

    # Reset Delays
    alct.WriteRegister(alct.DelayCtrlWrite, 0x1FF, parlen)

################################################################################
# Full scan of single delay ASIC
################################################################################
def ChipDelayScan(chip, alcttype):
    alct.SetChain(alct.VIRTEX_CONTROL)
    MinDelay            = 29
    MaxDelay            = 35
    num                 = 100       # number of words
    FIFOvalue           = 0xFFFF    # FIFO Value
    alct_dly            = 0
    StartDly_R          = 0
    StartDly_F          = 0
    TimeR_0             = [0]*16    # test board delays
    TimeF_0             = [0]*16    # test board delays
    TimeR_15            = [0]*16    # test board delays
    TimeF_15            = [0]*16    # test board delays
    PulseWidth_0        = [0]*16    # pulse widths
    PulseWidth_15       = [0]*16    # pulse widths
    DelayTimeR_0        = [0]*16    # pulse shifts
    DelayTimeF_0        = [0]*16    # pulse shifts
    DelayTimeR_15       = [0]*16    # pulse shifts
    DelayTimeF_15       = [0]*16    # pulse shifts
    DelayTimeF_50       = [0]*16    # pulse shifts
    Delay_Time          = [0]*16    # pulse shifts
    DeltaBeginTime      = [0]*16
    ErrorDeltaDelay     = 0

    print("==============================================================================")
    print('     Running Chip Delay Scan on Chip %i: '% chip)
    print('        * Ensure Clock Select Switch is Set to Position 2/3')
    print('        * Load test firmware')
    print('        * Connect special tester board to ALCT')
    print("==============================================================================\n")
    while True: 
        k = input("\n\t<cr> to continue when ready.")
        if not k: break

    # Pinpoint rise/fall times for ALCT delay of 0


    #------------------------------------------------------------------------------
    # Delay = 0
    #------------------------------------------------------------------------------
    alct_dly = 0
    print("\n\t-----------------------------------------------------------------------")
    print("\t Setting ALCT delay to 0")

    (FoundTimeBin, StartDly_R, StartDly_F) = FindStartDly(FIFOvalue, chip, alct_dly, num, alcttype)

    if FoundTimeBin:
        print('\t\t Found Start Delay Pulse on Chip #%i with alct delay of 0' % chip)
        print('\t\t StartDly Rise=%ins StartDly Fall=%ins' % (StartDly_R,StartDly_F))
        TimeR_0 = PinPointRiseTime(FIFOvalue, chip, StartDly_R, alct_dly, num, alcttype)
        TimeF_0 = PinPointFallTime(FIFOvalue, chip, StartDly_F, alct_dly, num, alcttype)
    else:
        print('\t\t ERROR: With alct_dly=0, Cannot find StartDly pulse on Chip: %i' % chip)

    MinDelayTimeR_0 = StartDly_R*25 + 255*0.25

    for i in range(16):
        if (FIFOvalue & (1 << i)) > 0:
            DelayTimeR_0[i]  = StartDly_R*25.0 + (TimeR_0[i])*0.25
            if MinDelayTimeR_0 > DelayTimeR_0[i]:
                MinDelayTimeR_0 = DelayTimeR_0[i]
    #------------------------------------------------------------------------------
    print('\n\t Rise times with ALCT_delay = 0 on Chip #%i = %.02f ns' % (chip, MinDelayTimeR_0))

    for i in range(16):
        DeltaBeginTime[i] = DelayTimeR_0[i] - MinDelayTimeR_0
        print('\t\t Ch #%2i = %.02f ns (deltaT=%.02f ns)' %  (i,DelayTimeR_0[i],DeltaBeginTime[i]))

    #------------------------------------------------------------------------------
    print('\n\t Fall times with ALCT delay 0 on Chip #%i' % chip)
    for i in range(16):
        if ((FIFOvalue & (1 << i))>0):
            DelayTimeF_0[i]  = (StartDly_F)*25 + TimeF_0[i]*0.25
            if DelayTimeF_0[i] < 0: DelayTimeF_0[i]=0
            print('\t\t Ch #%2i = %.02f ns' % (i,  DelayTimeF_0[i]))

    #------------------------------------------------------------------------------
    # Delay = 15
    #------------------------------------------------------------------------------

    #Pinpoint rise/fall times for ALCT delay of 15
    alct_dly = 15
    print("\n\t-----------------------------------------------------------------------")
    print("\n\t Setting ALCT delay to 15")
    (FoundTimeBin, StartDly_R, StartDly_F) = FindStartDly(FIFOvalue, chip, alct_dly, num,alcttype)
    if FoundTimeBin:
        print('\t\t Found Delay Pulse on Chip #%i with ALCT Delay=15' % chip)
        print('\t\t StartDly_rise=%i StartDly_fall=%i' % (StartDly_R,StartDly_F))

        TimeR_15 = PinPointRiseTime(FIFOvalue, chip, StartDly_R, alct_dly, num, alcttype)
        TimeF_15 = PinPointFallTime(FIFOvalue, chip, StartDly_F, alct_dly, num, alcttype)
    else:
        print('\t\t With alct_dly=15, Cannot find StartDly pulse on Chip: %i' % chip)

    #------------------------------------------------------------------------------
    print('\n\t Rise Times with ALCT delay=15 on Chip #%i' % chip)
    for i in range(16):
        if (FIFOvalue & (1 << i)) > 0:
            DelayTimeR_15[i]  = StartDly_R*25 + TimeR_15[i]*0.25
            print('\t\t Ch #%2i = %.02f ns' % (i,  DelayTimeR_15[i]))

    #------------------------------------------------------------------------------
    print('\n\t Fall Times with ALCT delay=15 on Chip #%i' % chip)
    for i in range(16):
        if (FIFOvalue & (1 << i)) > 0:
            DelayTimeF_15[i]  = StartDly_F*25 + TimeF_15[i]*0.25
            print('\t\t Ch #%2i = %.02f ns' % (i,  DelayTimeF_15[i]))

    #------------------------------------------------------------------------------
    print('\n\t Pulse widths with ALCT delay=15 on Chip #%i' % chip)
    for i in range(16):
        PulseWidth_0[i]  = DelayTimeF_0[i] - DelayTimeR_0[i]
        if (PulseWidth_0[i]<0): PulseWidth_0[i]=0
        print('\t\t Ch #%2i = %.02f ns' % (i,  PulseWidth_0[i]))

    #------------------------------------------------------------------------------
    # Take the Difference Between Rise and Fall (the width!)
    #------------------------------------------------------------------------------
    print("\n\t-----------------------------------------------------------------------")
    print('\t Pulse shifts (difference between 0 and 15) on Chip #%i' % chip)
    for i in range(16):
        Delay_Time[i]  = DelayTimeR_15[i] - DelayTimeR_0[i]
        print('\t\t Ch #%2i = %.02fns' % (i,  Delay_Time[i]))
        if ((Delay_Time[i] < MinDelay) or (Delay_Time[i] > MaxDelay)):
            ErrorDeltaDelay = Delay_Time[i]

#-------------------------------------------------------------------------------
# Automatic Check of ALL Delay ASIC delays
#-------------------------------------------------------------------------------
def TestboardDelaysCheck(alcttype):
    NUM_AFEB = alct.alct[alcttype].groups * 6
    #ch, i, j, k, l, ErrMeasDly, count: integer
    #MinDelay, MaxDelay, MaxDeltaDelay, MaxDeltaBegin: single
    #DeltaDelay, PulseWidth: array[0..15] of Currency
    #BeginTime_Min, AverageDelay_Time, DeltaDelay_Max, ErrorDeltaDelay: MeasDly
    #DeltaBegin_Max: MeasDly
    #DeltaBeginTime, Delay_Time: MeasDlyChan
    #ErrDelayTest: boolean
    #BoardNum: integer
    #PathString, PinErrors: string//Zach
    #RegMaskDone: array[0..41] of word

    alct.SetChain(alct.VIRTEX_CONTROL)
    ErrDelayTest    = False
    MaxDeltaBegin   = 2
    MaxDeltaDelay   = 2
    MinDelay        = 25
    MaxDelay        = 35
    ErrMeasDly      = 0

    # These are initializing 16 entry arrays of zeroes
    TimeR_0             = [0]*16    # test board delays
    TimeF_0             = [0]*16    # test board delays
    TimeR_15            = [0]*16    # test board delays
    TimeF_15            = [0]*16    # test board delays
    PulseWidth_0        = [0]*16    # pulse widths
    PulseWidth_15       = [0]*16    # pulse widths
    DelayTimeR_0        = [0]*16    # pulse shifts
    DelayTimeF_0        = [0]*16    # pulse shifts
    DelayTimeR_15       = [0]*16    # pulse shifts
    DelayTimeF_15       = [0]*16    # pulse shifts
    DelayTimeR_50       = [0]*16    # pulse shifts
    DelayTimeF_50       = [0]*16    # pulse shifts
    Delay_Time          = [0]*16    # pulse shifts

    # This is initializing a NUM_AFEB sized array of zeroes
    ErrorDeltaDelay     = [0] * NUM_AFEB
    BeginTime_Min       = [0] * NUM_AFEB
    AverageDelay_Time   = [0] * NUM_AFEB
    BeginTime_Min       = [0] * NUM_AFEB
    RegMaskDone         = [0] * NUM_AFEB
    DeltaBegin_Max      = [0] * NUM_AFEB
    DeltaDelay_Max      = [0] * NUM_AFEB
    DeltaDelay          = [0] * NUM_AFEB
    DeltaBegin_Min      = [0] * NUM_AFEB
    PulseWidth          = [0] * 16

    # Two dimensional arrays, 16xNUM_AFEB, filled with zeroes
    DeltaBeginTime      = [[0 for i in range(16)] for j in range(NUM_AFEB)]
    Delay_Time          = [[0 for i in range(16)] for j in range(NUM_AFEB)]

    print    ("")
    print    ("================================================================================")
    print    ('Running Chip Delay Scan on Full Board')
    print    ('\t* Ensure Clock Select Switch is Set to Position 2/3')
    print    ('\t* Load test firmware')
    print    ('\t* Connect delays test board to ALCT')
    print    ("================================================================================")
    k = input("        <cr> to continue when ready.")

    print('\nRunning Delays Test on ALCT Board')
    logging.info ("\n Delay ASICs Delay Test:")

    for chip in range(NUM_AFEB):
        count=0
        ErrMeasDly = MeasureDelay(chip, PulseWidth, BeginTime_Min, DeltaBeginTime, Delay_Time, AverageDelay_Time, RegMaskDone[chip], alcttype)
        DeltaBegin_Max[chip] = 0
        DeltaDelay_Max[chip] = 0

        for i in range(16):
            if (DeltaBeginTime[chip][i] > DeltaBegin_Max[chip]):
                DeltaBegin_Max[chip] = DeltaBeginTime[chip][i]

            DeltaDelay[i] = abs(Delay_Time[chip][i] - AverageDelay_Time[chip])

            if (DeltaDelay[i] > DeltaDelay_Max[chip]):
                DeltaDelay_Max[chip] = DeltaDelay[i]

        if (DeltaBegin_Max[chip] > MaxDeltaBegin):
            ErrMeasDly |= 0x10

        if (DeltaDelay_Max[chip] > MaxDeltaDelay):
            ErrMeasDly |= 0x20


        # Mark Test as Failed
        if (ErrMeasDly != 0):
            ErrDelayTest = True

        # Produce some output about what failed
        # Error Measure Delay is a Simple Bitmask of Error Types: 
        # 0x01 = 000001 => Time Bin @ dly=0  Not Found
        # 0x02 = 000010 => Time Bin @ dly=15 Not Found
        # 0x04 = 000100 => Pulse Width too Small
        # 0x08 = 001000 => Pulse Width too Large
        # 0x10 = 010000 => Delta Begin Time Too Large
        # 0x20 = 100000 => Delta Delay Time Too Large
        #------------------------------------------------------------------------------
        if (ErrMeasDly & 0x1): 
            print       ('\t FAIL: Cannot find StartDly_0 on Chip #%2i' % chip)
            logging.info('\t FAIL: Cannot find StartDly_0 on Chip #%2i' % chip)
            ErrDelayTest+=1
            if (RegMaskDone[chip]==0):
                print       ('\t All Pins Failed')
                logging.info('\t All Pins Failed')
            else:
                PinErrors  ='   Pin(s): '
                for j in range(16):
                    if ((RegMaskDone[chip] & (1 << j))==0):
                        if (count==0):
                            PinErrors = PinErrors + str(j)
                        else:
                            PinErrors  = PinErrors + ', ' + str(j)
                        count  = count+1
                PinErrors  = PinErrors + ' bad'
                print(PinErrors)
        #------------------------------------------------------------------------------
        if (ErrMeasDly & 0x2):
            print        ('\t FAIL: Cannot find StartDly_15 on Chip: %2i' % chip)
            logging.info ('\t FAIL: Cannot find StartDly_15 on Chip: %2i' % chip)
            ErrDelayTest+=1
        #------------------------------------------------------------------------------
        if (ErrMeasDly & 0x4): 
            for l in range(16):
                if (PulseWidth[l] < 30):
                    print        ('\t FAIL: Chip=%2i Pin=%2i Width of Pulse=%.02f (less than 30 ns): ' % (chip, l, PulseWidth[l]))
                    logging.info ('\t FAIL: Chip=%2i Pin=%2i Width of Pulse=%.02f (less than 30 ns): ' % (chip, l, PulseWidth[l]))
                    ErrDelayTest+=1
        #------------------------------------------------------------------------------
        if (ErrMeasDly & 0x8): 
            for l in range(16):
                if (PulseWidth[l] > 45):
                    print        ('\t FAIL: Chip=%2i Pin=%2i Width of Pulse=%.02f (greater than 45 ns): ' % (chip, l, PulseWidth[l]))
                    logging.info ('\t FAIL: Chip=%2i Pin=%2i Width of Pulse=%.02f (greater than 45 ns): ' % (chip, l, PulseWidth[l]))
                    ErrDelayTest+=1
        #------------------------------------------------------------------------------
        if (ErrMeasDly & 0x10): 
            print        ('\t FAIL: Chip=%i DeltaBeginTime=%.02fns (max=%.02fns)' % (chip, DeltaBegin_Max[chip], MaxDeltaBegin))
            logging.info ('\t FAIL: Chip=%i DeltaBeginTime=%.02fns (max=%.02fns)' % (chip, DeltaBegin_Max[chip], MaxDeltaBegin))
            ErrDelayTest+=1
        #------------------------------------------------------------------------------
        if (ErrMeasDly & 0x20): 
                if i==5:
                    print        ('\t FAIL: Chip=%2i DeltaDelay=%.02fns (max=%.02fns)' % (chip, DeltaDelay_Max[chip], MaxDeltaDelay))
                    logging.info ('\t FAIL: Chip=%2i DeltaDelay=%.02fns (max=%.02fns)' % (chip, DeltaDelay_Max[chip], MaxDeltaDelay))
                    ErrDelayTest+=1
                else: 
                    print        ('\t WTF!?')
        #------------------------------------------------------------------------------

        if (AverageDelay_Time[chip] < MinDelay) or (AverageDelay_Time[chip] > MaxDelay) :
            ErrorDeltaDelay[chip] = AverageDelay_Time[chip]
            if (AverageDelay_Time[chip] < MinDelay):
                print        ('\t FAIL: Chip %2i Average Delay=%.2fns is less than %.02f' % (chip,AverageDelay_Time[chip],MinDelay))
                logging.info ('\t FAIL: Chip %2i Average Delay=%.2fns is less than %.02f' % (chip,AverageDelay_Time[chip],MinDelay))
                ErrDelayTest+=1
            elif (AverageDelay_Time[chip] > MaxDelay):
                print        ('\t FAIL: Chip %2i Average Delay=%.2fns is more than %.02f' % (chip,AverageDelay_Time[chip],MaxDelay))
                logging.info ('\t FAIL: Chip %2i Average Delay=%.2fns is more than %.02f' % (chip,AverageDelay_Time[chip],MaxDelay))
                ErrDelayTest+=1
            else: 
                print        ('\t WTF!?')
        else:
            print        ('\t Chip %2i Average Delay=%.2fns (ref=%.02f)' % (chip,AverageDelay_Time[chip],(MaxDelay+MinDelay)/2.0))
            logging.info ('\t Chip %2i Average Delay=%.2fns (ref=%.02f)' % (chip,AverageDelay_Time[chip],(MaxDelay+MinDelay)/2.0))

    if (ErrDelayTest==0):
        print('\t ===> PASSED: Delays Test without Error')
    else:
        print('\t ===> FAILED: Delays Test with %i Errors' % ErrDelayTest)

    return (ErrDelayTest)

#-------------------------------------------------------------------------------
# procedure TForm1.Button15Click(Sender: TObject);
# set
#-------------------------------------------------------------------------------
def SetStandby(channel,cbStandby): 
    alct.SetChain(alct.SLOW_CTL)
    slowcontrol.SetStandbyForChan(channel,cbStandby)

def ResetTestPulseChannel(channel, cbLoop, cbStandby, alcttype):
    TouchFIFO(channel);
    alct.SetChain(alct.SLOW_CTL);

    # Setting Thresholds to 200
    for j in range (alct.alct[alcttype].chips):
        slowcontrol.SetThreshold(j, 200);

    slowcontrol.SetTestPulseWireGroupMask (0x7F)
    slowcontrol.SetTestPulseStripLayerMask(0x3F)
    slowcontrol.SetStandbyReg(0)
    slowcontrol.SetTestPulsePower(0)
    slowcontrol.SetTestPulsePowerAmp(255)
    slowcontrol.SetTestPulsePower(1)

def TestPulseLoopTest(alcttype): 
    slowcontrol.SetTestPulsePower(1)       # Turn on Test Pulse Generator
    slowcontrol.SetTestPulsePowerAmp(208)  # Set amplitude to approximately 1V
    cbLoop    = True
    cbStandby = False
    ChannelLoopTest(cbLoop,cbStandby,alcttype)

def StandbyLoopTest(alcttype): 
    #------------------------------------------------------------------------
    while True: 
        print ("Make sure to connect a shunt across TP1_28 and TP1_29!!!")
        k = input("\t<cr> to continue")
        if not k: 
            break

    cbLoop    = True
    cbStandby = True
    ChannelLoopTest(cbLoop,cbStandby,alcttype)

def ChannelLoopTest(cbLoop,cbStandby,alcttype): 
    NUM_AFEB = alct.alct[alcttype].chips

    alct.SetChain(alct.SLOW_CTL);

    # Set Test Pulse Power On
    slowcontrol.SetTestPulsePower(1)
    # Set Test Pulse Amplitude
    slowcontrol.SetTestPulsePowerAmp(255)


    # Chain Loop
    SetStandby(0,cbStandby)

    for chip in range(NUM_AFEB): 
        for Pass in range (10): 
            if Pass==0: 
                print('    Input Channel #%2i is selected' % chip)


            # Turn on ALL Groups
            if (Pass <= 4):
                slowcontrol.SetTestPulseWireGroupMask(0x7F)

            # Turn off ALL Groups Except the one we want. 
            else: 
                # Group 0   AFEBs 00,01,02, 12,13,14
                # Group 1   AFEBs 03,04,05, 15,16,17
                # Group 2   AFEBs 06,07,08, 18,19,20
                # Group 3   AFEBs 09,10,11, 21,22,23
                # Group 4-6 Not implemented on ALCT2001-384
                if chip < (NUM_AFEB//2): 
                    group = chip // 3
                else:
                    group = (chip-NUM_AFEB//2) // 3;

                write = (~(1 << group)) & 0x7F
                slowcontrol.SetTestPulseWireGroupMask(write)
                read = slowcontrol.ReadTestPulseWireGroupMask()

                if (read != write):
                    print('ERROR: Test Stopped -> Could not set Test Pulse Wire Group Mask')
                    #ConfigureTestPulseChannel(chip,cbLoop,cbStandby,alcttype)
                    #break

            #-------------------------------------------------------------------
            if (Pass == 9): 
                if cbLoop:
                    slowcontrol.SetStandbyForChan(chip, False);

            #-------------------------------------------------------------------
            slowcontrol.SetStandbyForChan (chip, False)
            slowcontrol.SetStandbyForChan (chip, True)
            slowcontrol.SetThreshold      (chip, (Pass % 2)*255)
            TouchFIFO         (chip);

            ResetTestPulseChannel(chip,cbLoop,cbStandby,alcttype)

def TouchFIFO (chip):
    alct.SetChain(alct.VIRTEX_CONTROL);

    # Write to FIFO
    jtag.WriteIR  (0x1A,                                     alct.V_IR)
    jtag.WriteDR ((1 & 0x1FFF) | ((chip & 0x3F) << 13),      19)
    jtag.WriteIR  (0x18,                                     alct.V_IR)
    jtag.WriteDR  (0x5555,                                   16  )
    jtag.WriteIR  (0x18,                                     alct.V_IR)
    jtag.WriteDR  (0xAAAA,                                   16  )

    # Read from FIFO
    jtag.WriteIR  (0x1A,                                         alct.V_IR)
    jtag.WriteDR ((0x1 & 0x1FFF) | (( chip & 0x3F) << 13),       19)
    jtag.WriteIR  (0x19,                                         alct.V_IR)
    jtag.ReadDR   (0x00,                                         16)
    jtag.WriteIR  (0x19,                                         alct.V_IR)
    jtag.ReadDR   (0x00,                                         16)

def TestPulseSelfCheck(alcttype):
    Errs = 0
    alct.SetChain(alct.SLOW_CTL)

    logging.info("\nTest Pulse Semi-Automatic Self Test")

    print("    * Connect LEMO output J3 (near power connector) to oscilloscope")
    print("      and configure scope to triggering from it ")
    print("    * Connect LEMO output on the bottom of large testing board to")
    print("      another channel of the oscilloscope. ")
    print("")
    print("    * Verify that, as the LEMO output from the tester board ")
    print("      switches between inputs, a pulse is generated at each input")
    print("      and is of consistent amplitude")
    while True: 
        k = input("\n\t <cr> to continue when ready.")
        if not k: break
    print("")

    #--------------------------------------------------------------------------
    while (True): 
        TestPulseLoopTest(alcttype)
        k=input("\n    Did all channels pass the test? \n\t <p> to pass, <f> to fail, <r> to repeat the scan: ")
        if k=="p":
            logging.info("\t PASSED: User failed board on Test Pulse Loopback Test")
            errs = 0
            break
        elif k=="f":
            s=input("\n Please record which channels failed the test: ")
            logging.info("\t FAILED: User failed board on Test Pulse Loopback Test")
            logging.info("\t         Failure indicated on channels %s" % s)
            errs = 1
            break
        elif k=="r":
            continue 
        else: 
            print("WTF!?")
            continue

    return (errs)


def StandbySelfCheck(alcttype):
    Errs = 0
    alct.SetChain(alct.SLOW_CTL)

    logging.info("\nAFEB Standby Semi-Automatic Self Test")
    print("    * Place a shunt across Test Points 28 and 29. ")
    print("    * Keep Tester Board attached.")
    print("")
    print("    * Verify that as the board is cycling through channels, the ")
    print("      red LED labeled D14 is not blinking. Blinking indicates that ")
    print("      the board failed to go into standby mode (that's bad). ")
    while True: 
        k = input("\n\t <cr> to continue when ready.")
        if not k: break
    print("")
    #--------------------------------------------------------------------------
    while (True): 
        TestPulseLoopTest(alcttype)
        k=input("\n    Did all channels pass the test? \n\t <p> to pass, <f> to fail, <r> to repeat the scan: ")
        if k=="p":
            logging.info("\t FAILED: User failed board on Test Pulse Loopback Test")
            done = True
            errs = 1
            break
        elif k=="f":
            s=input("\n    Please record which channels failed the test: ")
            logging.info("\t FAILED: User failed board on Test Pulse Loopback Test")
            logging.info("\t         Failure indicated on channels %s" % s)
            done = True
            errs = 0
            break
        elif k=="r":
            break 
        else: 
            print("WTF!?")
            continue

    if done: 
        while True: 
            k=input("    Make sure to remove Shunt from TP 28/29! <y> to confirm: ")
            if k=="y": 
                return (errs)
            if k=="s": 
                return (1)

#------------------------------------------------------------------------------
# Subtest Menu
#------------------------------------------------------------------------------

def SubtestMenu(alcttype):
    chip=0
    global parlen
    parlen = alct.alct[alcttype].groups + 2
    while True:
        common.ClearScreen()
        print("\n===============================================================================")
        print(  " Delay Chips Delay Test (Tester Board) Submenu")
        print(  "===============================================================================\n")
        print("\t 1 Check Entire Board")
        print("\t 2 Check Single Chip")
        print("\t 3 Scan Test Pulse Loopback")
        print("\t 4 Scan Standby Loopback")
        print("")
        print("\t ? Test Information")

        k=input("\nChoose Test or <cr> to return to Main Menu: ")
        if not k: break
        if k=="1":
            common.ClearScreen()
            print("")
            TestboardDelaysCheck(alcttype)
        if k=="2":
            k=input("\nChoose Chip to Scan (<cr> for chip=%i):" % chip)
            if k:
                chip = int(k,10)
            common.ClearScreen()
            print("")
            ChipDelayScan(chip, alcttype)
        if k=="3": 
            common.ClearScreen()
            print("")
            TestPulseSelfCheck(alcttype)
        if k=="4": 
            common.ClearScreen()
            print("")
            StandbySelfCheck(alcttype)

        if k=="?":
            common.ClearScreen()
            print(SubTestInfo())

        k=input("\n<cr> to return to menu: ")


def SubTestInfo():
    info = """ 
    This test verifies the functionality of the delay ASICs, which each provide 16
    channels of programmable delay to the digital signals that are sent from the AFEBs. 

    The test will verify two things: 
    1) Simple connectivity of the 16 channels back to the FPGA. But this is also
    achieved more easily through the single cable test..  
    2) Verify correct delays!  

    The latter portion of the test is the much more important one: the delay ASICs
    were found to have very large chip-to-chip variation. To accommodate for this,
    the chips were binned into several classes, based on the averaged delays of the
    16 individual channels. Each board is populated with delay ASICs from a single
    time bin, and all boards of the same type (288 vs. 384 vs. 672) are also
    populated with chips of the same time bins, and the design of the board types
    is adjusted (by changing the values of some resistors) to account for this
    difference. 

    These tests will verify first that the average delay of any board, when set to a
    prescribed value, is within an acceptable range.         

    Besides of course the chip-to-chip variation, however, there is also
    channel-to-channel variation within a single chip, so it must also be checked
    that the differences between channels is not too large. 
    """
    return (info)
