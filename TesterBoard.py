from ALCT import *
from JTAGUtils   import *
import os

def TestboardDelaysCheck(alcttype): 
    NUM_AFEB = alct[alcttype].groups * alct[alcttype].chips
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

    SetChain(arJTAGChains[3])
    ErrDelayTest    = False
    MaxDeltaBegin   = 2
    MaxDeltaDelay   = 2
    MinDelay        = 25
    MaxDelay        = 35
    ErrMeasDly      = 0

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
    DeltaBeginTime      = [[0 for i in range(16)] for j in range(NUM_AFEB)]
    Delay_Time          = [[0 for i in range(16)] for j in range(NUM_AFEB)]

    print('Make Sure Large Tester Board is Connected')
    print('Make Sure Correct Firmware is Loaded')

    print('\nRunning Delays Test on ALCT Board')

    for chip in range(NUM_AFEB): 
        print("\t Measuring Delays for AFEB #%i" % chip)
        count=0
        MeasureDelay(chip, PulseWidth, BeginTime_Min, DeltaBeginTime, Delay_Time, AverageDelay_Time, ErrMeasDly, RegMaskDone, alcttype)
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

def ChipDelayScan(chip, alcttype): 
    SetChain(arJTAGChains[3])
    MinDelay        = 29 
    MaxDelay        = 35
    num             = 100       # number of words
    value           = 0xFFFF    # FIFO Value
    alct_dly        = 0
    StartDly_R      = 0
    StartDly_F      = 0

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

    print('Running Chip Delay Scan on Chip %i' % chip)

    # Pinpoint rise/fall times for ALCT delay of 0
    alct_dly = 0
    if not FindStartDly(StartDly_R, StartDly_F, value, chip, alct_dly, num, alcttype): 
        print('\t ERROR: With alct_dly=0, Cannot find StartDly pulse on Chip: %i' % chip)
    else: 
        print('\t Found Start Delay Pulse on Chip #%i with alct delay of 0' % chip)
        print('\t StartDly_R=%i StartDly_F=%i' % (StartDly_R,StartDly_F))

        PinPointRiseTime(TimeR_0, value, chip, StartDly_R, alct_dly, num, alcttype)
        PinPointFallTime(TimeF_0, value, chip, StartDly_F-1, alct_dly, num, alcttype)

    MinDelayTimeR_0 = StartDly_R*25 + 255*0.25

    for i in range(16): 
        if (value & (1 << i)) > 0: 
            DelayTimeR_0[i]  = StartDly_R*25 + TimeR_0[i]*0.25
            if MinDelayTimeR_0 > DelayTimeR_0[i]: 
                MinDelayTimeR_0 = DelayTimeR_0[i]
    print('Rise times with ALCT_delay = 0 on Chip #%i = %.02f ns' % (chip, MinDelayTimeR_0))

    for i in range(16): 
        DeltaBeginTime[i] = DelayTimeR_0[i] - MinDelayTimeR_0
        print('\t chn #%02i DeltaBeginTime=%.02f ns DelayTime0=%.02f ns DelayTime50=%.02f ns)' %  (i,DeltaBeginTime[i],DelayTimeR_0[i],DelayTimeR_50[i]))

    print('Fall times with ALCT delay 0 on Chip #%i' % chip)
    for i in range(16): 
        if ((value & (1 << i))>0): 
            DelayTimeF_0[i]  = (StartDly_F-1)*25 + TimeF_0[i]*0.25
            if DelayTimeF_0[i] < 0: DelayTimeF_0[i]=0
            print('\t chn #%02i = %.02f ns' % (i,  DelayTimeF_0[i]))

    #Pinpoint rise/fall times for ALCT delay of 15
    alct_dly = 15
    if not FindStartDly(StartDly_R, StartDly_F, value, chip, alct_dly, num,alcttype): 
        print('With alct_dly=15, Cannot find StartDly pulse on Chip: %i' % chip)
    else: 
        print('Found Delay Pulse on Chip #%i with ALCT Delay=15' % chip)
        print('StartDly_rise=%i StartDly_fall=%i' % (StartDly_R,StartDly_F))

        PinPointRiseTime(TimeR_15, value, chip, StartDly_R, alct_dly, num, alcttype)
        PinPointFallTime(TimeF_15, value, chip, StartDly_F, alct_dly, num, alcttype)

    print('Rise Times with ALCT delay=15 on Chip #%i' % chip)
    for i in range(16): 
        if (value & (1 << i)) > 0: 
            DelayTimeR_15[i]  = StartDly_R*25 + TimeR_15[i]*0.25
            print('\t chn #%02i = %.02f ns' % (i,  DelayTimeR_15[i]))

    print('Fall Times with ALCT delay=15 on Chip #%i' % chip)
    for i in range(16): 
        if (value & (1 << i)) > 0: 
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

def SetDelayTest(fifoval, fifochan, startdelay, alctdelay, testboarddelay, alcttype):
    startdelay=2
    alctdelay=0
    testboarddelay=0

    SetFIFOChannel(fifochan, startdelay)
    SetFIFOValue(fifoval)
    SetTestBoardDelay(testboarddelay)
    SetALCTBoardDelay(fifochan, alctdelay, alcttype)

def PinPointRiseTime(TimeR, value, ch, StartDly_R, alct_dly, num, alcttype): 
    RegisterMaskDone = 0
    tb_dly = 0

    SetDelayTest(value, ch, StartDly_R, alct_dly, tb_dly, alcttype)

    FirstChn = False
    for j in range(26): 
        tb_dly = 10*j
        SetTestBoardDelay(tb_dly)
        ReadFIFOfast(num,cntrs)

        for i in range(16):
            if (cntrs[i] > 0) and ((value & (1 << i))>0) :
                FirstChn = True

            if (FirstChn) :
                tb_dly = 10*(j-1)
                break

    for dly in range(tb_dly,256):
        SetTestBoardDelay(dly)
        ReadFIFOfast(num,cntrs)

        for i in range (16):
            if(cntrs[i]>(num/2)) and ((value & (1 << i))>0) and ((RegisterMaskDone & (1 << i))==0) :
                TimeR[i] = dly
                RegisterMaskDone = RegisterMaskDone | (1 << i)
        if (RegisterMaskDone == Value):
            break

def PinPointRiseTime50(TimeR, TimeR_50, value, ch, StartDly_R, alct_dly, num, alcttype): 
    SetDelayTest(value, ch, StartDly_R, alct_dly, tb_dly, alcttype)

    FirstChn = False
    for j in range (26):
        tb_dly = 10*j
        SetTestBoardDelay(tb_dly)
        ReadFIFOfast(num,cntrs)

        for i in range(16): 
            if (cntrs[i] > 0) and ((value & (1 << i))>0): 
                FirstChn = True

        if(FirstChn): 
            tb_dly = 10*(j-1)
            break

    for dly in range(tb_dly,256):
        SetTestBoardDelay(dly)
        ReadFIFOfast(num,cntrs)

        for i in range(16):
            if cntrs[i]>(num/2) and ((value & (1 << i))>0) and (RegisterMaskDone & (1 << i))==0:
                TimeR[i]    = dly
                tmp2[i]     = dly  
                cnt2[i]     = cntrs[i]
                TimeR_50[i] = tmp1[i] + ((tmp2[i]-tmp1[i])*(num/2 - cnt1[i]) / (cnt2[i]-cnt1[i]))
                RegisterMaskDone = RegisterMaskDone | (1 << i)
            tmp1[i] = dly  
            cnt1[i] = cntrs[i]

    if(RegisterMaskDone == Value): 
        return(0)

def PinPointFallTime(TimeF, value, ch, StartDly_F, alct_dly, num, alcttype): 
    SetDelayTest(value, ch, StartDly_F, alct_dly, tb_dly, alcttype)
    FirstChn = False

    for j in range(26):
        tb_dly = 10*j
        SetTestBoardDelay(tb_dly)
        ReadFIFOfast(num,cntrs)

        for i in range(16):
            if(cntrs[i] > 0) and ((value & (1 >> i))>0):
                FirstChn = True

        if(FirstChn): 
            tb_dly = 10*(j-1)
            break

    for tb_dly in range (256): 
        SetTestBoardDelay(tb_dly)
        ReadFIFOfast(num,cntrs)

        for i in range(16):
            if cntrs[i]<(num/2) and ((value & (1 << i))>0) and ((RegisterMaskDone & (1 << i))==0):
                TimeF[i] = tb_dly
                RegisterMaskDone = RegisterMaskDone | (1 << i)

        if(RegisterMaskDone == Value): 
            break

def FindStartDly(StartDly_R, StartDly_F, value, ch, alct_dly, num, alcttype): 
    RegMaskDoneR    = 0
    RegMaskDoneF    = 0
    MaxChannelsCntr = 0
    FoundTimeBin    = False
    FirstCnhR       = False
    AllChnR         = False
    FirstChnF       = False
    AllChnF         = False
    StartDly_R      = 5
    StartDly_F      = 5
    StartDly        = 5

    cntrs           = [0x00]*16 # "array of byte"
    tb_dly = 0

    SetDelayTest(value, ch, StartDly, alct_dly, tb_dly, alcttype)

    for StartDly in range (5,16):
        # Access board
        SetFIFOChannel(ch, StartDly)
        ReadFIFOfast(num,cntrs)

        # Check counters and increment
        ChannelsCntr = 0  
        MaskDoneR    = 0

        for i in range(16):
            if (cntrs[i] > (num/2)) and ((value & (1 << i))>0):
                ChannelsCntr += 1
                MaskDoneR = MaskDoneR | (1 << i)

        # Check if time bin is found
        if (ChannelsCntr > 0):
            FirstCnhR = True
        if (MaskDoneR == value):
            AllChnR = True

        if (not FirstCnhR):
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
                if (cntrs[i] < (num/2)) and ((value & (1 << i))>0) : 
                    MaskDoneF = MaskDoneF | (1 << i)

                RegMaskDoneF = MaskDoneF
                if (MaskDoneF == value):
                    AllChnF = True

            if (AllChnR and AllChnF):
                FoundTimeBin = True
                break

    if (not FirstCnhR):
        StartDly_R = 5

    result = FoundTimeBin
    return(result)

def FindStartDlyPin(StartDly_R, StartDly_F, value, ch, alct_dly, num, RegMaskDone, alcttype):
    RegMaskDoneR    = 0
    RegMaskDoneF    = 0
    MaxChannelsCntr = 0
    FoundTimeBin    = False
    FirstCnhR       = False    
    AllChnR         = False
    FirstChnF       = False    
    AllChnF         = False
    StartDly_R      = 5       
    StartDly_F      = 5
    StartDly        = 5
    tb_dly          = 0
    cntrs           = [0x00]*16 # "array of byte"
    PulseWidth_min  = 0

    SetDelayTest(value, ch, StartDly, alct_dly, tb_dly,alcttype)

    for StartDly in range(5,16): 
        #Access board
        SetFIFOChannel(ch, StartDly )
        ReadFIFOfast(num,cntrs)

        #Check counters and increment
        ChannelsCntr = 0  
        MaskDoneR = 0

        for i in range (16): 
            if (cntrs[i] > (num/2)) and ((value & (1 << i))>0): 
                ChannelsCntr+=1
                MaskDoneR = MaskDoneR | (1 << i)

            #Check if time bin is found
            if (ChannelsCntr > 0): 
                FirstCnhR = True
            if (MaskDoneR == value): 
                AllChnR = True

            if (not FirstCnhR): 
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
                if (cntrs[i] < (num/2)) and ((value & (1 << i))>0): 
                    MaskDoneF = MaskDoneF | (1 << i)

            RegMaskDoneF = MaskDoneF
            if (MaskDoneF == value): 
                AllChnF = True

        if (AllChnR and AllChnF): 
            FoundTimeBin = True
            break

    if (not FirstCnhR): 
        StartDly_R = 5

    RegMaskDone[ch] = RegMaskDoneR and RegMaskDoneF
    return (FoundTimeBin)

def MeasureDelay(ch, PulseWidth, BeginTime_Min, DeltaBeginTime, Delay_Time, AverageDelay_Time, ErrMeasDly, RegMaskDone, alcttype):
    MinWidth       = 30 
    MaxWidth       = 45
    value          = 0xFFFF
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

    if FindStartDlyPin(StartDly_R, StartDly_F, value, ch, alct_dly, num, RegMaskDone,alcttype): 
        PinPointRiseTime(TimeR_0, value, ch, StartDly_R, alct_dly, num,alcttype)
        PinPointFallTime(TimeF_0, value, ch, StartDly_F, alct_dly, num,alcttype)

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

    if FindStartDly(StartDly_R, StartDly_F, value, ch, alct_dly, num, alcttype): 
        PinPointRiseTime(TimeR_15, value, ch, StartDly_R, alct_dly, num)
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

################################################################################
# Test Board FIFO Functions
################################################################################

def SetFIFOChannel(ch,startdly):
    WriteIR(WrAddF.val, V_IR)
    WriteDR( ch | startdly << 6,WrAddF.len)

def SetFIFOMode(mode):
    WriteIR(WrParamF.val, V_IR)
    WriteDR((0x8 | mode) & 0xF, WrParamF.len)

def SetFIFOReset(): 
    WriteIR(WrParamF.val, V_IR)
    WriteDR(8,WrParamF.len)
    WriteIR(WrParamF.val, V_IR)
    WriteDR(FIFO_RESET,WrParamF.len)
    WriteIR(WrParamF.val, V_IR)
    WriteDR(8,WrParamF.len)

def SetFIFOWrite(): 
    WriteIR(WrParamF.val, V_IR)
    WriteDR(FIFO_WRITE,WrParamF.len)

def SetFIFORead(): 
    WriteIR(WrParamF.val, V_IR)
    WriteDR(FIFO_READ,WrParamF.len)

def SetFIFOReadWrite(): 
    WriteIR(WrParamF.val, V_IR)
    WriteDR(FIFO_WRITE | FIFO_READ,WrParamF.len)

def FIFOClock(): 
    WriteIR(WrFIFO.val, V_IR)
    WriteDR(0x1,WrFIFO.len)

def ReadFIFOCounters(): 
    WriteIR(RdCntReg.val, V_IR)
    result = ReadDR(0x0,RdCntReg.len)
    return(result)

def SetFIFOValue(val):
    WriteIR(WrDatF.val, V_IR)
    WriteDR(val,WrDatF.len)

def SetTestBoardDelay(delay):
    WriteIR(WrParamF.val, V_IR)
    WriteDR(FIFO_RESET,WrParamF.len)

    WriteIR(WrDlyF.val, V_IR)
    WriteDR(FlipByte((255-delay) & 0xFF) ,WrDlyF.len)

    WriteIR(WrParamF.val, V_IR)
    WriteDR(8,WrParamF.len)

def SetALCTBoardDelay(ch, delay, alcttype):
    DelayValue   = [0] * MAX_DELAY_CHIPS_IN_GROUP
    DelayPattern = [0] * MAX_DELAY_CHIPS_IN_GROUP
    DelayValue[ch % MAX_DELAY_CHIPS_IN_GROUP] = delay
    Write6DelayLines(DelayPattern, DelayValue, 1 << (ch // MAX_DELAY_CHIPS_IN_GROUP), alcttype)

def SetTestBoardFIFO(fifoval, fifochan, numwords, startdelay, alctdelay, testboarddelay, alcttype):
    numwords=1
    startdelay=2
    alctdelay=0
    testboarddelay=0

    SetFIFOReset
    SetFIFOChannel(fifochan, startdelay )
    SetFIFOValue(fifoval)
    SetTestBoardDelay(testboarddelay)
    SetALCTBoardDelay(fifochan, alctdelay, alcttype)
    SetFIFOWrite
    for i in range(1,numwords+1):
        FIFOClock

def ReadFIFOValue():
    WriteIR(RdDataReg.val, V_IR)
    result = ReadDR(0,RdDataReg.len)
    return(result)

def ALCTEnableInput(): 
    WriteIR(WrParamDly.val, V_IR)
    WriteDR(0x1FD,parlen)
    WriteIR(RdParamDly.val, V_IR)
    result = ReadDR(0, parlen)
    return(result)

def ALCTDisableInput():
    WriteIR(WrParamDly.val, V_IR)
    WriteDR(0x1FF,parlen)
    WriteIR(RdParamDly.val, V_IR)
    result = ReadDR(0, parlen)
    return(result)

def ReadFIFO(vals, numwords, cntrs):
    SetFIFOReset()
    SetFIFOWrite()
    FIFOClock()
    SetFIFOReadWrite()
    ALCTEnableInput()

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

def ReadFIFOfast(numwords, cntrs):
    SetFIFOReset()
    SetFIFOWrite()
    FIFOClock()
    SetFIFOReadWrite()
    ALCTEnableInput()
    WriteIR(WrFIFO.val,V_IR)        # FIFOClock
    for i in range(numwords):
        WriteDR(0x1,WrFIFO.len)     # FIFOClock

    cntstr=hex(ReadFIFOCounters())  # Convert int to string
    cntstr = cntstr[2:]             # Cut off '0x'
    cntstr = cntstr.zfill(32)       # Pad String with Zeroes
    cntstr = cntstr[::-1]           # Reverse String

    for i in range (16):
        tmp = cntstr[:2]            # pick of first two hex digits
        num = int(tmp,16)           # convert to int 
        cntstr = cntstr[2:]         # truncate string
        cntrs[15-i] = num           # fill cntrs array

def PrepareDelayLinePatterns(dlys, image): 
    for i in range (0,4): 
        dlys[i][0].Pattern = FlipByte(image[1][i*2]) | (word(image[4][i*2]) << 8)
        dlys[i][1].Pattern = FlipByte(image[1][i*2]) | (word(image[4][i*2]) << 8)
        dlys[i][2].Pattern = FlipByte(image[1][i*2]) | (word(image[4][i*2]) << 8)
        dlys[i][3].Pattern = FlipByte(image[1][i*2]) | (word(image[4][i*2]) << 8)
        dlys[i][4].Pattern = FlipByte(image[1][i*2]) | (word(image[4][i*2]) << 8)
        dlys[i][5].Pattern = FlipByte(image[1][i*2]) | (word(image[4][i*2]) << 8)

def Write6DelayLines(DelayPattern, DelayValue, mask, alcttype): 
# def Write6DelayLines(DelayPattern, DelayValue, mask, readback, ReadValue, ReadPattern):   # overloaded function
# This function should be combined with SetDelayLines
    parlen = alct[alcttype].groups + 2
    WriteIR(ParamRegWrite, V_IR)
    WriteDR(0x1FF & (~(mask << 2)), parlen)

    WriteIR(ParamRegRead, V_IR)
    ReadDR(0x0, parlen)

    WriteIR(Wdly, V_IR)
    StartDRShift

    for i in range(6):
        value   = ShiftData(FlipHalfByte(DelayValue[i]), 4, False)
        if i==5: 
            pattern = ShiftData(DelayPattern[i], 16, True)
        else:                   
            pattern = ShiftData(DelayPattern[i], 16, False)

        # deal with overload
        #if readback==True: 
        #    if ((option is bool) and (option is True)):
        #        DelayValue[i]   = value
        #        DelayPattern[i] = pattern

        #if (ReadValue and ReadPattern): 
        #    ReadValue[i]   = shiftdata(fliphalfbyte(dlys[i].value), 4, False)
        #    if i==5: 
        #        ReadPattern[i] = shiftdata(dlys[i].pattern, 16, True)
        #    else: 
        #        ReadPattern[i] = shiftdata(dlys[i].pattern, 16, False)

    ExitDRShift 
    WriteIR(ParamRegWrite, V_IR)
    WriteDR(0x1FF, parlen)

def SubtestMenu(alcttype): 
    chip=0
    global parlen
    parlen = alct[alcttype].groups + 2
    while True: 
        os.system('cls')
        print("\n===============================")
        print(  " Delay Chips Delay Test Submenu")
        print(  "===============================\n")
        print("\t 1 Check Entire Board")
        print("\t 2 Check Single Chip")

        k=input("\nChoose Test or <cr> to return to Main Menu: ")
        if not k: break
        if k=="1":
            os.system('cls')
            print("")
            TestboardDelaysCheck(alcttype)
        if k=="2": 
            k=input("\nChoose Chip to Scan (<cr> for chip=%i):" % chip)
            if k:
                chip = int(k,10)
            os.system('cls')
            print("")
            ChipDelayScan(chip, alcttype)

        k=input("\n<cr> to return to menu: ")

