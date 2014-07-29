#!/usr/bin/env python3

################################################################################
# Tools for Verifying ASIC delays using the large external test board
################################################################################

import alct
import jtagutils as jtag
import os
import common

#-------------------------------------------------------------------------------
debug=False

#-------------------------------------------------------------------------------
# Register Locations / Sizes
#-------------------------------------------------------------------------------
#RdCntReg    = {'val': 0x02, 'length': 128}
#WrFIFO      = {'val': 0x0A, 'length': 1}
#WrDlyF      = {'val': 0x0B, 'length': 8}
#RdParamDly  = {'val': 0x15, 'length': 6}
#WrParamDly  = {'val': 0x16, 'length': 6}
#ALCTWdly    = {'val': 0x0D, 'length': 120}
#ALCTRdly    = {'val': 0x0E, 'length': 120}

#-------------------------------------------------------------------------------
# Automatic Check of Delay ASIC delays
#-------------------------------------------------------------------------------
def TestboardDelaysCheck(alcttype):
    NUM_AFEB = alct[alcttype].groups * 6
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

    alct.SetChain(alct.arJTAGChains[3])
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

    print('Make Sure Large Tester Board is Connected')
    print('Make Sure Test Firmware is Loaded')

    k = input("<cr> to continue when ready.")

    print('\nRunning Delays Test on ALCT Board')

    for chip in range(NUM_AFEB):
        print("\t Measuring Delays for AFEB #%i" % chip)
        count=0
        ErrMeasDly = MeasureDelay(chip, PulseWidth, BeginTime_Min, DeltaBeginTime, Delay_Time, AverageDelay_Time, RegMaskDone, alcttype)
        DeltaBegin_Max[chip] = 0
        DeltaDelay_Max[chip] = 0

        for i in range(16):
            if (DeltaBeginTime[chip][i] > DeltaBegin_Max[chip]):
                DeltaBegin_Max[chip] = DeltaBeginTime[chip][i]

            DeltaDelay[i] = abs(Delay_Time[chip][i] - AverageDelay_Time[chip])

            if (DeltaDelay[i] > DeltaDelay_Max[chip]):
                DeltaDelay_Max[chip] = DeltaDelay[i]

        if (DeltaBegin_Max[chip] > MaxDeltaBegin):
            ErrMeasDly = ErrMeasDly | 0x10
        if (DeltaDelay_Max[chip] > MaxDeltaDelay):
            ErrMeasDly = ErrMeasDly | 0x20

        if (ErrMeasDly != 0):
            ErrDelayTest = True
            for i in range(6):
                if (ErrMeasDly & (1 << i)) > 0:
                    k = i
                    #break
                    if k==0:
                        print('\t ERROR: Cannot find StartDly_0 on Chip #%i' % chip)
                        ErrDelayTest+=1
                        if (RegMaskDone[chip]==0):
                            print('All Pins Failed')
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

                    if k==1:
                        print('\t ERROR: Cannot find StartDly_15 on Chip: %i' % chip)
                        ErrDelayTest+=1
                    if k==2:
                        for l in range(16):
                            if (PulseWidth[l] < 30):
                                print('\t ERROR: Chip=%i Pin=%i Width of Pulse=%.02f (less than 30 ns): ' % (chip, l, PulseWidth[l]))
                                ErrDelayTest+=1
                    if k==3:
                        for l in range(16):
                            if (PulseWidth[l] > 45):
                                print('\t ERROR: Chip=%i Pin=%i Width of Pulse=%.02f (greater than 45 ns): ' % (chip, l, PulseWidth[l]))
                                ErrDelayTest+=1

                    if k==4:
                        print('\t ERROR: Chip=%i DeltaBeginTime=%.02f ns (max=%.02fns)' % (chip, DeltaBegin_Max[chip], MaxDeltaBegin))
                        ErrDelayTest+=1
                    if k==5:
                        print('\t ERROR: Chip=%i DeltaDelay=%.02fns (max=%.02fns)' % (chip, DeltaDelay_Max[chip], MaxDeltaDelay))
                        ErrDelayTest+=1

        if (AverageDelay_Time[chip] < MinDelay) or (AverageDelay_Time[chip] > MaxDelay) :
            ErrorDeltaDelay[chip] = AverageDelay_Time[chip]
            if (AverageDelay_Time[chip] < MinDelay):
                print('\t ERROR: Chip %02i Average Delay=%.2f ns is less than %.02f' % (chip,AverageDelay_Time[chip],MinDelay))
                ErrDelayTest+=1
            elif (AverageDelay_Time[chip] > MaxDelay):
                print('\t ERROR: Chip %02i Average Delay=%.2f ns is more than %.02f' % (chip,AverageDelay_Time[chip],MaxDelay))
                ErrDelayTest+=1
        else:
            print('\t Chip %i Average Delay=%.2f ns ref=%.02f' % (chip,AverageDelay_Time[chip],(MaxDelay+MinDelay)/2.0))

    if (ErrDelayTest==0):
        print('\t ===> Delays Test Passed without Error')
    else:
        print('\t ===> Delays Test Failed with %i Errors' % ErrDelayTest)

    #with DelaysChart do
    #    Title.Text.Clear
    #    Title.Text.Add('Test of Delays for ALCT # '+IntToStr(ch))
    #    RemoveAllSeries
    #    BottomAxis.Minimum  = 0
    #    BottomAxis.Maximum  = 20
    #    LeftAxis.Minimum  = 0
    #    LeftAxis.Maximum  = 50*(0.000000001)

    #    AddSeries(TBarSeries.Create(self))
    #    AddSeries(TLineSeries.Create(self))
    #    AddSeries(TBarSeries.Create(self))
    #    AddSeries(TLineSeries.Create(self))

    #    Series[0].Title  = 'Error Delay'
    #    Series[1].Title  = 'Min Delay'
    #    Series[2].Title  = 'DelayAverage'
    #    Series[3].Title  = 'Max Delay '

    #    for i =0 to NUM_AFEB-1 do
    #        Series[0].Add(ErrorDeltaDelay[i],'',clTeeColor)
    #        Series[1].AddXY(i, MinDelay,'',clTeeColor)
    #        Series[2].Add(AverageDelay_Time[i],'',clTeeColor)
    #        Series[3].AddXY(i, MaxDelay,'',clTeeColor)

################################################################################
# Full scan of single delay ASIC
################################################################################
def ChipDelayScan(chip, alcttype):
    alct.SetChain(alct.arJTAGChains[3])
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
    DelayTimeR_50       = [0]*16    # pulse shifts
    DelayTimeF_50       = [0]*16    # pulse shifts
    Delay_Time          = [0]*16    # pulse shifts
    DeltaBeginTime      = [0]*16
    ErrorDeltaDelay     = 0

    print('========================================')
    print('Running Chip Delay Scan on Chip %i'% chip)
    print('Ensure Clock Select Switch is Set to 2/3')
    print('Load test firmware')
    print('Connect delays test board to ALCT')
    print('========================================')
    k = input("<cr> to continue when ready.")

    # Pinpoint rise/fall times for ALCT delay of 0

    alct_dly = 0

    (FoundTimeBin, StartDly_R, StartDly_F) = FindStartDly(FIFOvalue, chip, alct_dly, num, alcttype)

    if FoundTimeBin:
        print('Found Start Delay Pulse on Chip #%i with alct delay of 0' % chip)
        print('\t StartDly_R=%i StartDly_F=%i' % (StartDly_R,StartDly_F))
        PinPointRiseTime(TimeR_0, FIFOvalue, chip, StartDly_R, alct_dly, num, alcttype)
        PinPointFallTime(TimeF_0, FIFOvalue, chip, StartDly_F, alct_dly, num, alcttype)
        print(TimeF_0)
    else:
        print('\t ERROR: With alct_dly=0, Cannot find StartDly pulse on Chip: %i' % chip)


    MinDelayTimeR_0 = StartDly_R*25 + 255*0.25

    for i in range(16):
        if (FIFOvalue & (1 << i)) > 0:
            DelayTimeR_0[i]  = StartDly_R*25 + TimeR_0[i]*0.25
            if MinDelayTimeR_0 > DelayTimeR_0[i]:
                MinDelayTimeR_0 = DelayTimeR_0[i]
    print('Rise times with ALCT_delay = 0 on Chip #%i = %.02f ns' % (chip, MinDelayTimeR_0))

    for i in range(16):
        DeltaBeginTime[i] = DelayTimeR_0[i] - MinDelayTimeR_0
        print('\t chn #%02i DeltaBeginTime=%.02f ns DelayTime0=%.02f ns DelayTime50=%.02f ns)' %  (i,DeltaBeginTime[i],DelayTimeR_0[i],DelayTimeR_50[i]))

    print('Fall times with ALCT delay 0 on Chip #%i' % chip)
    for i in range(16):
        if ((FIFOvalue & (1 << i))>0):
            DelayTimeF_0[i]  = (StartDly_F-1)*25 + TimeF_0[i]*0.25
            if DelayTimeF_0[i] < 0: DelayTimeF_0[i]=0
            print('\t chn #%02i = %.02f ns' % (i,  DelayTimeF_0[i]))

    #Pinpoint rise/fall times for ALCT delay of 15
    alct_dly = 15
    (FoundTimeBin, StartDly_R, StartDly_F) = FindStartDly(FIFOvalue, chip, alct_dly, num,alcttype)
    if FoundTimeBin:
        print('Found Delay Pulse on Chip #%i with ALCT Delay=15' % chip)
        print('\tStartDly_rise=%i StartDly_fall=%i' % (StartDly_R,StartDly_F))

        PinPointRiseTime(TimeR_15, FIFOvalue, chip, StartDly_R, alct_dly, num, alcttype)
        PinPointFallTime(TimeF_15, FIFOvalue, chip, StartDly_F, alct_dly, num, alcttype)
    else:
        print('With alct_dly=15, Cannot find StartDly pulse on Chip: %i' % chip)

    print('Rise Times with ALCT delay=15 on Chip #%i' % chip)
    for i in range(16):
        if (FIFOvalue & (1 << i)) > 0:
            DelayTimeR_15[i]  = StartDly_R*25 + TimeR_15[i]*0.25
            print('\t chn #%02i = %.02f ns' % (i,  DelayTimeR_15[i]))

    print('Fall Times with ALCT delay=15 on Chip #%i' % chip)
    for i in range(16):
        if (FIFOvalue & (1 << i)) > 0:
            DelayTimeF_15[i]  = StartDly_F*25 + TimeF_15[i]*0.25
            print('\t chn #%02i = %.02f ns' % (i,  DelayTimeF_15[i]))

    print('Pulse widths with ALCT delay=15 on Chip #%i' % chip)
    for i in range(16):
        PulseWidth_0[i]  = DelayTimeF_0[i] - DelayTimeR_0[i]
        if (PulseWidth_0[i]<0): PulseWidth_0[i]=0
        print('\t chn #%02i = %.02f ns' % (i,  PulseWidth_0[i]))

    print('Pulse shifts on Chip #%i' % chip)
    for i in range(16):
        Delay_Time[i]  = DelayTimeR_15[i] - DelayTimeR_0[i]
        print('\t chn #%02i = %.02f ns' % (i,  Delay_Time[i]))
        if ((Delay_Time[i] < MinDelay) or (Delay_Time[i] > MaxDelay)):
            ErrorDeltaDelay = Delay_Time[i]

    #with DelaysChart do
    #    BottomAxis.Minimum  = 0
    #    BottomAxis.Maximum  = 20
    #    LeftAxis.Minimum  = 0
    #    LeftAxis.Maximum  = 50*(0.000000001)

    #    PassCnt  =4
    #    AddSeries(TBarSeries.Create(self))
    #    AddSeries(TLineSeries.Create(self))
    #    AddSeries(TBarSeries.Create(self))
    #    AddSeries(TLineSeries.Create(self))

    #    Series[0].Title  = 'Error shifts'
    #    Series[1].Title  = 'Min shifts'
    #    Series[2].Title  = 'Max shifts'
    #    Series[3].Title  = 'Pulse shifts'

    #    for i =0 to 15 do
    #        Series[0].Add(ErrorDeltaDelay[i],'',clTeeColor)
    #        Series[1].AddXY(i, MinDelay,'',clTeeColor)
    #        Series[2].Add(Delay_Time[i],'',clTeeColor)
    #        Series[3].AddXY(i, MaxDelay,'',clTeeColor)



def SetDelayTest(fifoval, fifochan, startdelay=2, alctdelay=0x0000, testboarddelay=0, alcttype=0):
    #debug=True
    SetFIFOChannel(fifochan, startdelay)
    SetFIFOValue(fifoval)
    SetTestBoardDelay(testboarddelay)
    if debug: print('\t Writing delay=0x%04X to channel %i' %(alctdelay, fifochan))
    SetALCTBoardDelay(fifochan, alctdelay, alcttype)


def PinPointRiseTime(TimeR, FIFOvalue, ch, StartDly_R, alct_dly, num, alcttype):
    tb_dly              = 0
    RegisterMaskDone    = 0
    FirstChn            = False
    cntrs               = [0x00]*16 # "array of byte"

    SetDelayTest(FIFOvalue, ch, StartDly_R, alct_dly, tb_dly, alcttype)

    for j in range(26):
        tb_dly = 5*j
        SetTestBoardDelay(tb_dly)
        ReadFIFOfast(num,cntrs,alcttype)

        for i in range(16):
            if (cntrs[i] > 0) and (FIFOvalue & (1 << i))>0 :
                FirstChn = True

            if (FirstChn) :
                tb_dly = 10*(j-1)
                break

    for dly in range(tb_dly,256):
        SetTestBoardDelay(dly)
        ReadFIFOfast(num,cntrs, alcttype)

        for i in range (16):
            if (cntrs[i]>(num/2)) and ((FIFOvalue & (1 << i))>0) and ((RegisterMaskDone & (1 << i))==0):
                TimeR[i] = dly
                if debug: print(TimeR[i])
                if debug: print('%i %i' % (i, dly))
                RegisterMaskDone = RegisterMaskDone | (1 << i)
        if (RegisterMaskDone == FIFOvalue):
            break

#def PinPointRiseTime50(TimeR, TimeR_50, value, ch, StartDly_R, alct_dly, num, alcttype):
#    tb_dly      = 0
#    cntrs       = [0x00]*16 # "array of byte"
#    FirstChn    = False
#
#    SetDelayTest(value, ch, StartDly_R, alct_dly, tb_dly, alcttype)
#
#    for j in range (26):
#        tb_dly = 10*j
#        SetTestBoardDelay(tb_dly)
#        ReadFIFOfast(num,cntrs,alcttype)
#
#        for i in range(16):
#            if (cntrs[i] > 0) and ((value & (1 << i))>0):
#                FirstChn = True
#
#        if(FirstChn):
#            tb_dly = 10*(j-1)
#            break
#
#    for dly in range(tb_dly,256):
#        SetTestBoardDelay(dly)
#        ReadFIFOfast(num,cntrs,alcttype)
#
#        for i in range(16):
#            if (cntrs[i]>(num/2)) and ((FIFOvalue & (1 << i))>0) and ((RegisterMaskDone & (1 << i))==0):
#                TimeR[i]    = dly
#                tmp2[i]     = dly
#                cnt2[i]     = cntrs[i]
#                TimeR_50[i] = tmp1[i] + ((tmp2[i]-tmp1[i])*(num/2 - cnt1[i]) / (cnt2[i]-cnt1[i]))
#                RegisterMaskDone = RegisterMaskDone | (1 << i)
#            tmp1[i] = dly
#            cnt1[i] = cntrs[i]
#
#    if(RegisterMaskDone == FIFOvalue):
#        return(0)

def PinPointFallTime(TimeF, FIFOvalue, ch, StartDly_F, alct_dly, num, alcttype):
    tb_dly           = 0
    RegisterMaskDone = 0
    FirstChn         = False
    cntrs            = [0x00]*16 # "array of byte"

    SetDelayTest(FIFOvalue, ch, StartDly_F, alct_dly, tb_dly, alcttype)

    for j in range(26):
        tb_dly = 10*j
        SetTestBoardDelay(tb_dly)
        ReadFIFOfast(num,cntrs,alcttype)

        for i in range(16):
            if(cntrs[i] > 0) and ((FIFOvalue & (1 << i))>0):
                FirstChn = True

        if(FirstChn):
            tb_dly = 10*(j-1)
            break

    for tb_dly in range (256):
        SetTestBoardDelay(tb_dly)
        ReadFIFOfast(num,cntrs,alcttype)

        for i in range(16):
            if (cntrs[i]<(num/2)) and ((FIFOvalue & (1 << i))>0) and ((RegisterMaskDone & (1 << i))==0):
                TimeF[i] = tb_dly
                RegisterMaskDone = RegisterMaskDone | (1 << i)

        if(RegisterMaskDone == FIFOvalue):
            break

def FindStartDly(FIFOvalue, ch, alct_dly, num, alcttype):
    if debug: print('Find Start Dly')
    alct.SetChain(alct.arJTAGChains[3])
    FoundTimeBin    = False # Found time bin ?
    FirstChnR       = False # First Channel Rise
    AllChnR         = False # All Channels Rise
    FirstChnF       = False # First Channel Fall
    AllChnF         = False # All Channels Fall
    RegMaskDoneR    = 0
    RegMaskDoneF    = 0
    MaxChannelsCntr = 0
    StartDly_R      = 5     # Rise Start Delay
    StartDly_F      = 5     # Fall Start Delay
    StartDly        = 5
    tb_dly          = 0     # Test board delay
    cntrs           = [0x00]*16 # "array of byte"

    SetDelayTest(FIFOvalue, ch, StartDly, alct_dly, tb_dly, alcttype)

    for StartDly in range (5,16):

        # Access board
        SetFIFOChannel(ch, StartDly)
        ReadFIFOfast(num,cntrs,alcttype)

        ChannelsCntr = 0
        MaskDoneR    = 0

        # Fill Counters with FIFO Bitmask
        for i in range(16):
            if (cntrs[i] > (num/2)) and ((FIFOvalue & (1 << i))>0):
                ChannelsCntr += 1
                MaskDoneR = MaskDoneR | (1 << i)

        # Check if time bin is found
        if (ChannelsCntr > 0):
            FirstChnR = True
        if (MaskDoneR == FIFOvalue):
            AllChnR = True


        if (not FirstChnR):
            StartDly_R = StartDly
        else:
            if ((ChannelsCntr > 0) and (ChannelsCntr >= MaxChannelsCntr)):
                MaxChannelsCntr = ChannelsCntr
                StartDly_F      = StartDly
                RegMaskDoneR    = MaskDoneR
            else:
                FirstChnF = True

        if (FirstChnF):
            MaskDoneF = 0
            for i in range (16):
                #if (cntrs[i] < (num/2)) and ((FIFOvalue & (1 << i))>0) :
                MaskDoneF = MaskDoneF | (1 << i)
                RegMaskDoneF = MaskDoneF
                if (MaskDoneF == FIFOvalue):
                    AllChnF = True

            if (AllChnR and AllChnF):
                FoundTimeBin = True
                break

        if (not FirstChnR):
            StartDly_R = 5

    return(FoundTimeBin, StartDly_R, StartDly_F)

def FindStartDlyPin(FIFOvalue, ch, alct_dly, num, RegMaskDone, alcttype):
    RegMaskDoneR    = 0
    RegMaskDoneF    = 0
    MaxChannelsCntr = 0
    FoundTimeBin    = False
    FirstChnR       = False
    AllChnR         = False
    FirstChnF       = False
    AllChnF         = False
    StartDly_R      = 5
    StartDly_F      = 5
    StartDly        = 5
    tb_dly          = 0
    cntrs           = [0x00]*16 # "array of byte"
    PulseWidth_min  = 0

    SetDelayTest(FIFOvalue, ch, StartDly, alct_dly, tb_dly,alcttype)

    for StartDly in range(5,16):
        #Access board
        SetFIFOChannel(ch, StartDly )
        ReadFIFOfast(num,cntrs, alcttype)

        #Check counters and increment
        ChannelsCntr = 0
        MaskDoneR = 0

        for i in range (16):
            if (cntrs[i] > (num/2)) and ((FIFOvalue & (1 << i))>0):
                ChannelsCntr+=1
                MaskDoneR = MaskDoneR | (1 << i)

            #Check if time bin is found
            if (ChannelsCntr > 0):
                FirstChnR = True
            if (MaskDoneR == FIFOvalue):
                AllChnR = True

            if (not FirstChnR):
                StartDly_R = StartDly
            else:
                if ((ChannelsCntr > 0) and (ChannelsCntr >= MaxChannelsCntr)):
                    MaxChannelsCntr = ChannelsCntr
                    StartDly_F = StartDly
                    RegMaskDoneR = MaskDoneR
                else:
                    FirstChnF = True

        if (FirstChnF):
            MaskDoneF = 0
            for i in range(16):
                if (cntrs[i] < (num/2)) and ((FIFOvalue & (1 << i))>0):
                    MaskDoneF = MaskDoneF | (1 << i)

            RegMaskDoneF = MaskDoneF
            if (MaskDoneF == FIFOvalue):
                AllChnF = True

        if (AllChnR and AllChnF):
            FoundTimeBin = True
            break

    if (not FirstChnR):
        StartDly_R = 5

    RegMaskDone[ch] = RegMaskDoneR and RegMaskDoneF
    return(FoundTimeBin, StartDly_R, StartDly_F)

def MeasureDelay(ch, PulseWidth, BeginTime_Min, DeltaBeginTime, Delay_Time, AverageDelay_Time, RegMaskDone, alcttype):
    MinWidth       = 30
    MaxWidth       = 45
    FIFOvalue          = 0xFFFF
    num            = 100
    ErrMeasDly     = 0
    PulseWidth_min = 0

    # initialize arrays
    TimeR_0        = [0]*16
    TimeF_0        = [0]*16
    TimeR_15       = [0]*16
    DelayTimeR_0   = [0]*16
    DelayTimeF_0   = [0]*16
    DelayTimeR_15  = [0]*16

    # write zeroes to arrays from args
    for i in range(16):
        PulseWidth[i]           = 0
        DeltaBeginTime[ch][i]   = 0
        Delay_Time[ch][i]       = 0

    alct_dly        = 0
    StartDly_R      = 0
    StartDly_F      = 0

    (FoundTimeBin, StartDly_R, StartDly_F) = FindStartDlyPin(FIFOvalue, ch, alct_dly, num, RegMaskDone,alcttype)
    if FoundTimeBin:
        PinPointRiseTime(TimeR_0, FIFOvalue, ch, StartDly_R, alct_dly, num,alcttype)
        PinPointFallTime(TimeF_0, FIFOvalue, ch, StartDly_F, alct_dly, num,alcttype)

        BeginTime_Min[ch] = StartDly_R*25 + 255*0.25
        for i in range(16):
            DelayTimeR_0[i] = StartDly_R*25 + TimeR_0[i]*0.25
            DelayTimeF_0[i] = StartDly_F*25 + TimeF_0[i]*0.25
            PulseWidth[i]   = DelayTimeF_0[i] - DelayTimeR_0[i]

            if (i==0):
                PulseWidth_Min = PulseWidth[i]
                PulseWidth_Max = PulseWidth[i]

            if (DelayTimeR_0[i] < BeginTime_Min[ch]):
                BeginTime_Min[ch] = DelayTimeR_0[i]

            if (PulseWidth[i] < PulseWidth_Min):
                PulseWidth_Min = PulseWidth[i]

            if (PulseWidth[i] > PulseWidth_Max):
                PulseWidth_Max = PulseWidth[i]
    else:
        ErrMeasDly = ErrMeasDly | 0x1
        return(0)

    alct_dly = 15
    AverageDelay_Time[ch] = 0
    SumDelay_Time = 0

    (FoundTimeBin, StartDly_R, StartDly_F) = FindStartDly(FIFOvalue, ch, alct_dly, num, alcttype)
    if FoundTimeBin:
        PinPointRiseTime(TimeR_15, FIFOvalue, ch, StartDly_R, alct_dly, num)
        for i in range(16):
            DelayTimeR_15[i]    = StartDly_R*25 + TimeR_15[i]*0.25
            Delay_Time[ch][i]   = DelayTimeR_15[i] - DelayTimeR_0[i]
            SumDelay_Time       = SumDelay_Time + Delay_Time[ch][i]

        AverageDelay_Time[ch] = SumDelay_Time / 16
    else:
        ErrMeasDly = ErrMeasDly | 0x2

    if (PulseWidth_Min < MinWidth):
        ErrMeasDly = ErrMeasDly | 0x4

    if (PulseWidth_Max > MaxWidth):
        ErrMeasDly = ErrMeasDly | 0x8

    for i in range(16):
        DeltaBeginTime[ch][i] = DelayTimeR_0[i] - BeginTime_Min[ch]

    return(ErrMeasDly)

#------------------------------------------------------------------------------
# Register Definitions
#------------------------------------------------------------------------------

RdDataReg           = MutableNamedTuple()
RdDataReg.val       = 0x01
RdDataReg.length    = 16

RdCntReg            = MutableNamedTuple()
RdCntReg.val        = 0x02
RdCntReg.length     = 128

WrDatF 	            = MutableNamedTuple()
WrDatF.val          = 0x04
WrDatF.length       = 16

WrAddF 	            = MutableNamedTuple()
WrAddF.val          = 0x06
WrAddF.length       = 10

WrParamF            = MutableNamedTuple()
WrParamF.val        = 0x08
WrParamF.length     = 4

RdParamDly          = MutableNamedTuple()
RdParamDly.val      = 0x15
RdParamDly.length   = 6

# Change for Different Boards!!
WrParamDly          = MutableNamedTuple()
WrParamDly.val      = 0x16
WrParamDly.legnth   = 6

WrDlyF              = MutableNamedTuple()
WrDlyF.val          = 0x0B
WrDlyF.length       = 8

ALCTWdly            = MutableNamedTuple()
ALCTWdly.val        = 0x0D
ALCTWdly.length     = 120

ALCTRdly            = MutableNamedTuple()
ALCTRdly.val        = 0x0E
ALCTRdly.length     = 120

WrFIFO              = MutableNamedTuple()
WrFIFO.val          = 0x0A
WrFIFO.length       = 1

################################################################################
# Test Board FIFO Functions
################################################################################

def SetFIFOChannel(ch,startdly):
    jtag.WriteIR(WrAddF.val, V_IR)
    jtag.WriteDR( ch | startdly << 6, WrAddF.length)

def SetFIFOMode(mode):
    jtag.WriteIR(WrParamF.val, V_IR)
    jtag.WriteDR((0x8 | mode) & 0xF, WrParamF.length)

def SetFIFOReset():
    jtag.WriteIR(WrParamF.val, V_IR)
    jtag.WriteDR(8,WrParamF.length)
    jtag.WriteIR(WrParamF.val, V_IR)
    jtag.WriteDR(FIFO_RESET,WrParamF.length)
    jtag.WriteIR(WrParamF.val, V_IR)
    jtag.WriteDR(8,WrParamF.length)

def SetFIFOWrite():
    jtag.WriteIR(WrParamF.val, V_IR)
    jtag.WriteDR(FIFO_WRITE,WrParamF.length)

def SetFIFORead():
    jtag.WriteIR(WrParamF.val, V_IR)
    jtag.WriteDR(FIFO_READ,WrParamF.length)

def SetFIFOReadWrite():
    jtag.WriteIR(WrParamF.val, V_IR)
    jtag.WriteDR(FIFO_WRITE | FIFO_READ,WrParamF.length)

def FIFOClock():
    jtag.WriteIR(WrFIFO.val, V_IR)
    jtag.WriteDR(0x1,WrFIFO.length)

def ReadFIFOCounters():
    jtag.WriteIR(RdCntReg.val, V_IR)
    return(jtag.ReadDR(0x0,RdCntReg.length))

def SetFIFOValue(val):
    jtag.WriteIR(WrDatF.val, V_IR)
    jtag.WriteDR(val,WrDatF.length)

def SetTestBoardDelay(delay):
    jtag.WriteIR(WrParamF.val, V_IR)
    jtag.WriteDR(FIFO_RESET,WrParamF.length)

    jtag.WriteIR(WrDlyF.val, V_IR)
    jtag.WriteDR(0xFF & FlipByte((255-delay) & 0xFF), WrDlyF.length)

    jtag.WriteIR(WrParamF.val, V_IR)
    jtag.WriteDR(0x8,WrParamF.length)

def SetALCTBoardDelay(ch, delay, alcttype):
    #debug=True
    DelayValue   = [0x0] * 6 # 6 delay chips in group
    DelayPattern = [0x0] * 6 # 6 delay chips in group
    DelayValue[ch % 6] = delay
    if debug: print(DelayPattern)
    if debug: print(DelayValue)
    Write6DelayLines(DelayPattern, DelayValue, 1 << (ch // 6), alcttype)

def SetTestBoardFIFO(fifoval, fifochan, numwords, startdelay, alctdelay, testboarddelay, alcttype):
    numwords        = 1
    startdelay      = 2
    alctdelay       = 0
    testboarddelay  = 0

    SetFIFOReset()
    SetFIFOChannel(fifochan, startdelay)
    SetFIFOValue(fifoval)
    SetTestBoardDelay(testboarddelay)
    SetALCTBoardDelay(fifochan, alctdelay, alcttype)
    SetFIFOWrite
    for i in range(1,numwords+1):
        FIFOClock

def ReadFIFOValue():
    jtag.WriteIR(RdDataReg.val, V_IR)
    result = jtag.ReadDR(0,RdDataReg.length)
    return(result)

def ALCTEnableInput(alcttype):
    parlen = alct[alcttype].groups + 2
    jtag.WriteIR(WrParamDly.val, V_IR)
    jtag.WriteDR(0x1FD,parlen)
    jtag.WriteIR(RdParamDly.val, V_IR)
    result = jtag.ReadDR(0, parlen)
    return(result)

def ALCTDisableInput(alcttype):
    parlen = alct[alcttype].groups + 2
    jtag.WriteIR(WrParamDly.val, V_IR)
    jtag.WriteDR(0x1FF,parlen)
    jtag.WriteIR(RdParamDly.val, V_IR)
    result = jtag.ReadDR(0, parlen)
    return(result)

def ReadFIFO(vals, numwords, cntrs, alcttype):
    SetFIFOReset()
    SetFIFOWrite()
    FIFOClock()
    SetFIFOReadWrite()
    ALCTEnableInput(alcttype)

    for i in range(numwords):
        FIFOClock()                 # Clock FIFO
        vals[i] = ReadFIFOValue()   # Read Bit from FIFO

    cntstr=hex(ReadFIFOCounters())  # Convert int to string
    cntstr = cntstr[2:]             # Cut off '0x'
    cntstr = cntstr.zfill(32)       # Pad String with Zeroes
    cntstr = cntstr[::-1]           # Reverse String

    for i in range (16):
        tmp = cntstr[:2]            # pick of first two hex digits
        num = int(tmp,16)           # convert to int
        cntstr = cntstr[2:]         # truncate string
        cntrs[15-i] = num           # fill cntrs array

def ReadFIFOfast(numwords, cntrs, alcttype):
    SetFIFOReset()
    SetFIFOWrite()
    FIFOClock()
    SetFIFOReadWrite()
    ALCTEnableInput(alcttype)

    jtag.WriteIR(WrFIFO.val,V_IR)        # FIFOClock
    for i in range(numwords):
        jtag.WriteDR(0x1,WrFIFO.length)     # FIFOClock

    cntstr=hex(ReadFIFOCounters())  # Convert int to string
    cntstr = cntstr[2:]             # Cut off '0x'
    cntstr = cntstr.zfill(32)       # Pad String with Zeroes
    cntstr = cntstr[::-1]           # Reverse String

    for i in range (16):
        tmp = cntstr[:2]            # pick of first two hex digits
        num = int(tmp,16)           # convert to int
        cntstr = cntstr[2:]         # truncate string
        cntrs[15-i] = num           # fill cntrs array

#def PrepareDelayLinePatterns(dlys, image):
#    for i in range (0,4):
#        dlys[i][0].Pattern = FlipByte(image[1][i*2]) | (word(image[4][i*2]) << 8)
#        dlys[i][1].Pattern = FlipByte(image[1][i*2]) | (word(image[4][i*2]) << 8)
#        dlys[i][2].Pattern = FlipByte(image[1][i*2]) | (word(image[4][i*2]) << 8)
#        dlys[i][3].Pattern = FlipByte(image[1][i*2]) | (word(image[4][i*2]) << 8)
#        dlys[i][4].Pattern = FlipByte(image[1][i*2]) | (word(image[4][i*2]) << 8)
#        dlys[i][5].Pattern = FlipByte(image[1][i*2]) | (word(image[4][i*2]) << 8)


# Writes Pattern and Value to 6 Groups of Delay Chips
def Write6DelayLines(DelayPattern, DelayValue, mask, alcttype):
    alct.SetChain(VIRTEX_CONTROL)
    parlen = alct[alcttype].groups + 2

    jtag.WriteIR(DelayCtrlWrite, V_IR)
    jtag.WriteDR(0x1FF & (~(mask << 2)), parlen)

    jtag.WriteIR(DelayCtrlRead, V_IR)
    jtag.ReadDR(0x0, parlen)

    jtag.WriteIR(Wdly, V_IR)

    jtag.StartDRShift()

    for i in range(6):
        ShiftData(FlipHalfByte(DelayValue[i]), 4, False)
        if i==5:
            ShiftData(DelayPattern[i], 16, True)
        else:
            ShiftData(DelayPattern[i], 16, False)

    jtag.ExitDRShift()
    jtag.WriteIR(DelayCtrlWrite, V_IR)
    jtag.WriteDR(0x1FF, parlen)

#------------------------------------------------------------------------------
# Subtest Menu
#------------------------------------------------------------------------------

def SubtestMenu(alcttype):
    chip=0
    global parlen
    parlen = alct[alcttype].groups + 2
    while True:
        common.ClearScreen()
        print("\n================================================================================")
        print(  " Delay Chips Delay Test (Tester Board) Submenu")
        print(  "================================================================================\n")
        print("\t 1 Check Entire Board")
        print("\t 2 Check Single Chip")

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

        k=input("\n<cr> to return to menu: ")

