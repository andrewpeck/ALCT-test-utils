from ALCT import *

from time import sleep
from common import Now
from common import Day
from common import Printer

import random
import sys
import os

#DelayGroup = [ MutableNamedTuple() for i in range(MAX_DELAY_CHIPS_IN_GROUP)]
#ALCTDelays = [MutableNamedTuple() for i in range(MAX_DELAY_GROUPS)]
#arDelays  = [[ MutableNamedTuple() for i in range(MAX_DELAY_GROUPS)] for j in range(NUM_OF_DELAY_CHIPS_IN_GROUP)]
#SendPtrns  = [[ MutableNamedTuple() for i in range(MAX_DELAY_GROUPS)] for j in range(NUM_OF_DELAY_CHIPS_IN_GROUP)]
#ReadPtrns  = [[ MutableNamedTuple() for i in range(MAX_DELAY_GROUPS)] for j in range(NUM_OF_DELAY_CHIPS_IN_GROUP)]

def SetDelayLines(cs, patterns, delays, alcttype): 
    SetChain(VIRTEX_CONTROL)
    PinMapOnRead = True
    parlen = alct[alcttype].groups + 2
    for group in range (alct[alcttype].groups): 
        if ((cs & 0x7F) & (0x1 << group)) > 0:  
            dr = 0x1FF & (~((cs & (0x1 << group)) << 2) )
            #log dr = 0x1fb
            #dr = 0x1FF

            WriteIR(DelayCtrlWrite, V_IR)
            WriteDR(dr, parlen)

            WriteIR(Wdly, V_IR)
            StartDRShift()

            for j in range(6): 
                DlyVal      =  delays[group][j]
                DlyPtrn     =  patterns[group][j]

                #=== Pin Remapping ===
                if not PinMapOnRead: 
                    DlyPtrn=PinRemap(group,j,patterns[group][group])

                DlyValTmp   = ShiftData(DlyVal, 4, False)
                if j==5: 
                    DlyPtrnTmp  = ShiftData(DlyPtrn, 16, True)
                else: 
                    DlyPtrnTmp  = ShiftData(DlyPtrn, 16, False)

            ExitDRShift()

            WriteIR(DelayCtrlWrite, V_IR)
            WriteDR(0x1FF, parlen)

def ReadPatterns(pattern,alcttype):

    SendPtrns =[[0 for j in range(6)] for i in range(alct[alcttype].groups)]
    ReadPtrns =[[0 for j in range(6)] for i in range(alct[alcttype].groups)]
    SendValues=[[0 for j in range(6)] for i in range(alct[alcttype].groups)]
    ReadValues=[[0 for j in range(6)] for i in range(alct[alcttype].groups)]

    SetChain(VIRTEX_CONTROL)
    Wires = (alct[alcttype].channels)

    DR = 0
    PinMapOnRead = True

    WriteIR(0x11,   V_IR)
    WriteDR(0x4001, 16)         # Enable Patterns from DelayChips into 384 bits ALCT Register

    WriteIR(0x10,   V_IR)       # Send 384 bits ALCT Register to PC via JTAG
    DR = ReadDR(DR,Wires)
    DR=DR & 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF

    stringDR = hex(DR)
    stringDR = stringDR[2:]
    stringDR = stringDR.zfill(96)
    stringDR = stringDR[::-1]
    #print(stringDR)

    for i in range(alct[alcttype].groups): 
        for j in range(NUM_OF_DELAY_CHIPS_IN_GROUP): 
            tmp = stringDR[0:4]
            num = int(tmp,16)        # set num= first 4 hex digits
            stringDR = stringDR[4:]         # cut off first 4 hex digits

            pattern[i][j] = (num) & 0xFFFF
            if PinMapOnRead: 
                pattern[i][j]=PinRemap(i,j,pattern[i][j])

            stringPat = hex(pattern[i][j])
            stringPat = stringPat[2:]
            stringPat = stringPat.zfill(4)
            stringPat = stringPat[::-1]
            pattern[i][j]=int(stringPat,16)

    #for i in range(alct[alcttype].groups): 
    #    for j in range(NUM_OF_DELAY_CHIPS_IN_GROUP): 
    #        num = int(stringDR[0:4],16)        # set num= first 4 hex digits
    #        stringDR = stringDR[4:]         # cut off first 4 hex digits
    #        pattern[i][j] = (num) & 0xFFFF
    #        if PinMapOnRead: 
    #            pattern[i][j]=PinRemap(i,j,pattern[i][j])

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

def CheckPatterns(SendPtrns, ReadPtrns,alcttype): 
    Errs = 0
    for i in range(alct[alcttype].groups): 
        for j in range(6): 
            #if ReadPtrns[i][j]== SendPtrns[i][j]: 
            for bit in range (16): 
                if ((ReadPtrns[i][j] >> bit) & 0x1) != ((SendPtrns[i][j] >> bit) & 0x1):
                    Errs = Errs + 1
    return(Errs)

def Walking1(alcttype): 
    SendPtrns =[[0 for j in range(NUM_OF_DELAY_CHIPS_IN_GROUP)] for i in range(alct[alcttype].groups)]
    ReadPtrns =[[0 for j in range(NUM_OF_DELAY_CHIPS_IN_GROUP)] for i in range(alct[alcttype].groups)]
    SendValues=[[0 for j in range(NUM_OF_DELAY_CHIPS_IN_GROUP)] for i in range(alct[alcttype].groups)]
    ReadValues=[[0 for j in range(NUM_OF_DELAY_CHIPS_IN_GROUP)] for i in range(alct[alcttype].groups)]
    Wires = alct[alcttype].channels
    Errs        = 0
    ErrOnePass  = 0
    fStop       = False
    fStopOnError= True

    print('Walking 1 Test')

    SetChain(VIRTEX_CONTROL)

    for bit in range(Wires): 
        output = "\t Checking bit %i of %i" % (bit, Wires)
        Printer(output)

        WriteIR(0x11,   V_IR)
        WriteDR(0x4000, 16)

        for i in range(alct[alcttype].groups): 
            for j in range(NUM_OF_DELAY_CHIPS_IN_GROUP): 
                SendValues[i][j]    = 0
                SendPtrns [i][j]    = 0 or ((bit // 16) == ((i*6)+j)) << (bit % 16)
                ReadValues[i][j]    = 0
                ReadPtrns [i][j]    = 0

        SetDelayLines(0x7F, SendPtrns, SendValues, alcttype)
        ReadPatterns(ReadPtrns,alcttype)

        ErrOnePass = CheckPatterns(SendPtrns, ReadPtrns,alcttype)
        Errs = Errs + ErrOnePass
        if (ErrOnePass > 0): 
            print("\n\t Test found %i errors!" % (ErrOnePass))
            print("\t Possibly problem with Chip #%i Channel %i" % (bit//16+1, bit+1))
        #PrintPatterns(alcttype, SendPtrns, ReadPtrns) 

    # Fini 
    print('\n\t ===> Walking 1 Test Finished with %i Errors ' % Errs)

def PrintPatterns(alcttype, SendPtrns, ReadPtrns): 
    sentstr = ''
    readstr = ''
    output  = ''
    for i in range(alct[alcttype].groups): 
        for j in range(NUM_OF_DELAY_CHIPS_IN_GROUP): 
            sentstr = ("%04X" % SendPtrns[i][j]) + ' ' + sentstr
            readstr = ("%04X" % ReadPtrns[i][j]) + ' ' + readstr
    output += ('\n\t ->Sent: %s' % sentstr)
    output += ('\n\t <-Read: %s' % readstr)
    print(output)

def Walking0(alcttype):
    SendPtrns =[[0 for j in range(NUM_OF_DELAY_CHIPS_IN_GROUP)] for i in range(alct[alcttype].groups)]
    ReadPtrns =[[0 for j in range(NUM_OF_DELAY_CHIPS_IN_GROUP)] for i in range(alct[alcttype].groups)]
    SendValues=[[0 for j in range(NUM_OF_DELAY_CHIPS_IN_GROUP)] for i in range(alct[alcttype].groups)]
    ReadValues=[[0 for j in range(NUM_OF_DELAY_CHIPS_IN_GROUP)] for i in range(alct[alcttype].groups)]
    Wires = alct[alcttype].channels
    Errs        = 0
    ErrOnePass  = 0
    fStop       = False

    print('Walking 0 Test')

    SetChain(VIRTEX_CONTROL)

    for bit in range (Wires): 
        output = "\t Checking bit %i of %i" % (bit+1, Wires)
        Printer(output)

        WriteIR(0x11,   V_IR)
        WriteDR(0x4000, 16)

        for i in range (alct[alcttype].groups): 
            for j in range(NUM_OF_DELAY_CHIPS_IN_GROUP): 
                    SendValues[i][j] = 0
                    SendPtrns [i][j] = 0xFFFF & (~(((bit//16)==((i*6)+j)) << (bit%16)))
                    ReadValues[i][j] = 0
                    ReadPtrns [i][j] = 0

        SetDelayLines(0x7F, SendPtrns, SendValues, alcttype)
        ReadPatterns(ReadPtrns,alcttype)
        #PrintPatterns(alcttype, SendPtrns, ReadPtrns)

        ErrOnePass  = CheckPatterns(SendPtrns, ReadPtrns,alcttype)
        Errs        = Errs + ErrOnePass
        if ErrOnePass > 0: 
            print("\n\t Test found %i errors!" % (ErrOnePass))
            print("\t Possibly problem with Chip #%i Channel %i" % ((bit//16)+1, bit+1))

    # Fini 
    print('\n\t ===> Walking 0 Test Finished with %i Errors ' % Errs)

def Filling1(alcttype): 
    SendPtrns =[[0 for j in range(NUM_OF_DELAY_CHIPS_IN_GROUP)] for i in range(alct[alcttype].groups)]
    ReadPtrns =[[0 for j in range(NUM_OF_DELAY_CHIPS_IN_GROUP)] for i in range(alct[alcttype].groups)]
    SendValues=[[0 for j in range(NUM_OF_DELAY_CHIPS_IN_GROUP)] for i in range(alct[alcttype].groups)]
    ReadValues=[[0 for j in range(NUM_OF_DELAY_CHIPS_IN_GROUP)] for i in range(alct[alcttype].groups)]
    Wires = alct[alcttype].channels
    Errs       = 0
    ErrOnePass = 0
    fStop      = False
    print('Filling 1s Test')

    SetChain(VIRTEX_CONTROL)

    for i in range(NUM_OF_DELAY_GROUPS): 
        for j in range(NUM_OF_DELAY_CHIPS_IN_GROUP): 
            SendValues[i][j] = 0
            SendPtrns [i][j] = 0
            ReadValues[i][j] = 0
            ReadPtrns [i][j] = 0

    SetDelayLines(0xF,SendPtrns,SendValues,alcttype)

    for bit in range (Wires): 
        WriteIR(0x11    , V_IR)
        WriteDR(0x4000  , 16)

        output = "\tChecking bit %i of %i" % (bit, Wires)
        Printer(output)

        for i in range(NUM_OF_DELAY_GROUPS): 
            for j in range(NUM_OF_DELAY_CHIPS_IN_GROUP): 
                SendValues[i][j] = 0
                SendPtrns [i][j] = SendPtrns[i][j] | (((bit//16) == ((i*6)+j)) << (bit % 16))
                ReadValues[i][j] = 0
                ReadPtrns [i][j] = 0

        SetDelayLines(0xF, SendPtrns, SendValues, alcttype)
        ReadPatterns(ReadPtrns,alcttype)

        ErrOnePass = CheckPatterns(SendPtrns, ReadPtrns,alcttype)
        Errs       = Errs + ErrOnePass
        if ErrOnePass > 0: 
            print("\n\t Test found %i errors!" % (ErrOnePass))
            print("\t Possibly problem with Chip #%i Channel %i" % (bit//16+1, bit+1))
    # Fini 
    print('\n\t ===> Filling by 1s Test Finished with %i Errors ' % Errs)

def Filling0(alcttype): 
    SendPtrns =[[0 for j in range(NUM_OF_DELAY_CHIPS_IN_GROUP)] for i in range(alct[alcttype].groups)]
    ReadPtrns =[[0 for j in range(NUM_OF_DELAY_CHIPS_IN_GROUP)] for i in range(alct[alcttype].groups)]
    SendValues=[[0 for j in range(NUM_OF_DELAY_CHIPS_IN_GROUP)] for i in range(alct[alcttype].groups)]
    ReadValues=[[0 for j in range(NUM_OF_DELAY_CHIPS_IN_GROUP)] for i in range(alct[alcttype].groups)]
    Wires = alct[alcttype].channels
    Errs       = 0
    ErrOnePass = 0
    fStop      = True

    print('Filling 0s Test')
    SetChain(VIRTEX_CONTROL)

    for i in range(NUM_OF_DELAY_GROUPS): 
        for j in range(NUM_OF_DELAY_CHIPS_IN_GROUP): 
            SendValues[i][j] = 0x0000
            SendPtrns [i][j] = 0xFFFF
            ReadValues[i][j] = 0x0000
            ReadPtrns [i][j] = 0x0000

    SetDelayLines(0xF, SendPtrns, SendValues, alcttype)

    for bit in range(Wires): 
        output = "\t Checking bit %i of %i" % (bit+1, Wires)
        Printer(output)

        WriteIR(0x11, V_IR)
        WriteDR(0x4000, 16)

        for i in range(NUM_OF_DELAY_GROUPS): 
            for j in range(NUM_OF_DELAY_CHIPS_IN_GROUP): 
                SendValues[i][j] = 0x0000
                SendPtrns [i][j] = SendPtrns[i][j] & (~(((bit // 16) == ((i*6)+j)) << (bit % 16)))
                ReadValues[i][j] = 0x0000
                ReadPtrns [i][j] = 0x0000

        SetDelayLines(0xF, SendPtrns, SendValues, alcttype)
        ReadPatterns(ReadPtrns,alcttype)

        ErrOnePass = CheckPatterns(SendPtrns, ReadPtrns,alcttype)
        Errs       = Errs + ErrOnePass
        if ErrOnePass > 0: 
            print("\n\t Test found %i errors!" % (ErrOnePass))
            print("\t Possibly problem with Chip #%i Channel %i" % (bit//16+1, bit+1))

    # Fini 
    print('\n\t ===> Filling by 0s Test Finished with %i Errors ' % Errs)

def Shifting5andA(alcttype):
    SendPtrns =[[0 for j in range(NUM_OF_DELAY_CHIPS_IN_GROUP)] for i in range(alct[alcttype].groups)]
    ReadPtrns =[[0 for j in range(NUM_OF_DELAY_CHIPS_IN_GROUP)] for i in range(alct[alcttype].groups)]
    SendValues=[[0 for j in range(NUM_OF_DELAY_CHIPS_IN_GROUP)] for i in range(alct[alcttype].groups)]
    ReadValues=[[0 for j in range(NUM_OF_DELAY_CHIPS_IN_GROUP)] for i in range(alct[alcttype].groups)]
    Wires = (alct[alcttype].channels)
    npasses = 25
    Errs = 0
    ErrOnePass = 0
    fStop = False

    print('Shifting 5 and A Test')

    SetChain(VIRTEX_CONTROL)
    for p in range(npasses): 
        time.sleep(.2) # DO NOT TAKE THIS SLEEP OUT 

        output = "\tPass %i of %i" % (p+1, npasses)
        Printer(output)

        WriteIR(0x11    , V_IR)
        WriteDR(0x4000  , 16)

        for i in range(NUM_OF_DELAY_GROUPS): 
            for j in range(NUM_OF_DELAY_CHIPS_IN_GROUP): 
                SendValues[i][j] 		= 0
                if ((p+1) % 2)==1: 
                    SendPtrns[i][j] = 0x5555
                else: 
                    SendPtrns[i][j] = 0xAAAA

                ReadValues[i][j] 		= 0
                ReadPtrns[i][j]         = 0

            SetDelayLines(0xF, SendPtrns, SendValues, alcttype)
            ReadPatterns(ReadPtrns,alcttype)
            ErrOnePass      = CheckPatterns(SendPtrns, ReadPtrns,alcttype)
            Errs            = Errs + ErrOnePass
            if ErrOnePass > 0:
                print("\n\t Test found %i errors!" % (ErrOnePass))
                print("\t Possibly problem with Chip #%i Channel %i" % (bit//16+1, bit+1))


    # Reset Delay Chips (returns Current to normal values
    for i in range(NUM_OF_DELAY_GROUPS): 
        for j in range(NUM_OF_DELAY_CHIPS_IN_GROUP): 
            SendValues[i][j] = 0x0000
            SendPtrns [i][j] = 0x0000
            ReadValues[i][j] = 0x0000
            ReadPtrns [i][j] = 0x0000

    SetDelayLines(0xF, SendPtrns, SendValues, alcttype)
    # Fini 
    print('\n\t ===> Shifting 5 and A Test Finished with %i Errors ' % Errs)

def RandomData(alcttype):
    SendPtrns =[[0 for j in range(NUM_OF_DELAY_CHIPS_IN_GROUP)] for i in range(alct[alcttype].groups)]
    ReadPtrns =[[0 for j in range(NUM_OF_DELAY_CHIPS_IN_GROUP)] for i in range(alct[alcttype].groups)]
    SendValues=[[0 for j in range(NUM_OF_DELAY_CHIPS_IN_GROUP)] for i in range(alct[alcttype].groups)]
    ReadValues=[[0 for j in range(NUM_OF_DELAY_CHIPS_IN_GROUP)] for i in range(alct[alcttype].groups)]
    Wires = alct[alcttype].channels
    npasses    = 50
    Errs       = 0
    ErrOnePass = 0
    fStop      = False

    print('Random Data Test')

    SetChain(VIRTEX_CONTROL)

    random.seed()

    for p in range(npasses): 
        time.sleep(0.1)
        output = "\t Pass %i of %i" % (p+1, npasses)
        Printer(output)

        WriteIR(0x11  , V_IR)
        WriteDR(0x4000, 16)

        for i in range(NUM_OF_DELAY_GROUPS): 
            for j in range(NUM_OF_DELAY_CHIPS_IN_GROUP): 
                SendValues[i][j] 	= 0
                SendPtrns[i][j]     = random.getrandbits(16)
                ReadValues[i][j] 	= 0
                ReadPtrns[i][j]     = 0

        SetDelayLines(0xF, SendPtrns, SendValues, alcttype)

        ReadPatterns(ReadPtrns,alcttype)
        ErrOnePass = CheckPatterns(SendPtrns, ReadPtrns,alcttype)
        Errs       = Errs + ErrOnePass
        if ErrOnePass > 0: 
            print("\n\t Test found %i errors!" % (ErrOnePass))
            print("\t Possibly problem with Chip #%i Channel %i" % (bit//16 + 1, bit+1))

    # Reset Delay Chips (returns Current to normal values
    for i in range(NUM_OF_DELAY_GROUPS): 
        for j in range(NUM_OF_DELAY_CHIPS_IN_GROUP): 
            SendValues[i][j] = 0x0000
            SendPtrns [i][j] = 0x0000
            ReadValues[i][j] = 0x0000
            ReadPtrns [i][j] = 0x0000

    SetDelayLines(0xF, SendPtrns, SendValues, alcttype)

    # Fini 
    print('\n\t ===> Random Data Test Finished with %i Errors ' % Errs)




#def GeneratePattern(): 
#    begin
#    case FTestType of
#        0..3:	pass := Wires
#        4:   	pass := FNumOfPasses*2
#        5:      pass := FNumOfPasses
#    Errs = 0
#    #FTestForm.PrSt.Max := pass
#    #FTestForm.PrSt.Position := 0
#    fStop = False
#    FTestForm.Log.Lines.Add(TimeToStr(Now())+ '> === ' + TestNames[FTestType] + '===')
#    FTestForm.sbBar.SimpleText := TestNames[FTestType]
#
#    SetChain(VRTX_CH)
#
#    # reset delay lines
#    for i in range(alct[alcttype].groups): 
#        for j in range(NUM_OF_DELAY_CHIPS_IN_GROUP): 
#            SendValues[i][j] = 0
#            if FTestType = 3 : 
#                SendPtrns[i][j] 	= 0xFFFF
#            else : 
#                SendPtrns[i][j] 	= 0x0000
#            ReadValues[i][j] 		    = 0
#            ReadPtrns[i][j] 	    = 0
#
#    SetDelayLines(0x7F, SendPtrns, SendValues, alcttype)
#
#    for p in range(pass): 
#        #FTestForm.PrSt.Position := p+1
#        if FTestType = 4 then
#            FTestForm.lbPrSt.Caption := 'Pass #' + IntToStr((p div 2) + 1) + ' of ' +IntToStr(pass div 2)
#        else
#            FTestForm.lbPrSt.Caption := 'Pass #' + IntToStr(p+1) + ' of ' +IntToStr(pass)
#
#        case FTestType of
#    0..3:  if not (FTestForm.FindComponent('DG'+IntToStr(p div (alct[alcttype].chips * ALCTBoard.delaylines))) as TCheckBox).Checked then
#            continue
#
#    WriteIR('11', V_IR)
#    WRiteDR('4000', 16)
#
#        for i:= 0 to alct[alcttype].groups - 1 do
#        begin
#				for j:=0 to NUM_OF_DELAY_CHIPS_IN_GROUP - 1 do
#				begin
#					SendValues[i][j] := 0
#					case FTestType of
#					  0: SendPtrns[i][j] 	:= 0 or (Integer ((p div 16) = ((i*6)+j)) shl (p mod 16))
#					  1: SendPtrns[i][j] 	:= $FFFF and (not(Integer ((p div 16) = ((i*6)+j)) shl (p mod 16)))
#					  2: SendPtrns[i][j] 	:= SendPtrns[i][j] or ((Integer ((p div 16) = ((i*6)+j)) shl (p mod 16)))
#					  3: SendPtrns[i][j] 	:= SendPtrns[i][j] and (not(Integer ((p div 16) = ((i*6)+j)) shl (p mod 16)))
#					  4: begin
#                if Boolean ((p+1) mod 2) then
#								  SendPtrns[i][j] := $5555
#							  else
#								  SendPtrns[i][j] := $AAAA
#               end
#					  5: SendPtrns[i][j] := Random($FFFF)
#					else
#						SendPtrns[i][j] := 0
#					end
#					ReadValues[i][j] 		:= 0
#					ReadPtrns[i][j] 	:= 0
#				end
#			end
#
#			FTestForm.SetDelayLines($7f, SendPtrns, SendValues)
#
#			if FTestForm.ReadPatterns(ReadPtrns) = Wires then
#			begin
#				ErrOnePass := FTestForm.CheckPatterns(SendPtrns, ReadPtrns)
#				Errs := Errs + ErrOnePass
#        sentstr := ''
#        readstr := ''
#				for gr:= 0 to alct[alcttype].groups - 1 do
#					for ch:=0 to NUM_OF_DELAY_CHIPS_IN_GROUP - 1 do
#          begin
#            sentstr := IntToHex(SendPtrns[gr][ch], 4) + ' ' +sentstr
#						readstr := IntToHex(ReadPtrns[gr][ch], 4) + ' ' +readstr
#          end
#        status := readstr
#        FTestForm.sbBar.SimpleText := status
#
#				if ErrOnePass > 0 then
#				begin
#					FTestForm.Log.Lines.Add('Pass: #' + IntToStr(p+1) + ' with ' + IntToStr(ErrOnePass) + ' Errors ')
#//          FTestForm.Log.Lines.Add('Possibly problem with Chip #' + IntToStr(p div 16 + 1) + ' Channel #' + IntToStr(p mod 16 + 1))
#          FTestForm.Log.Lines.Add('->Sent: '+sentstr)
#          FTestForm.Log.Lines.Add('<-Read: '+readstr)
#          if fStopOnError then
#          begin
#            //FTestForm.Log.Lines.Add('->Sent: '+sentstr)
#            //FTestForm.Log.Lines.Add('<-Read: '+readstr)
#            if not fRepeatLast then
#              begin
#                fStop := True
#                for gr:= 0 to alct[alcttype].groups - 1 do
#                begin
#                  for ch:=0 to NUM_OF_DELAY_CHIPS_IN_GROUP - 1 do
#                  begin
#{                    if ReadPtrns[gr][ch] <> SendPtrns[gr][ch] then
#                    begin
#                      FTestForm.Log.Lines.Add('    Group #'+ IntToStr(gr+1) + ':-> Chip #' + IntToStr(ch+1) + ' Read 0x'+IntToHex(ReadPtrns[gr][ch], 4) + ' Expected 0x' + IntToHex(SendPtrns[gr][ch], 4))
#                      WriteIR('0A', V_IR)
#                      WriteDR(IntToHex((gr*6+ch) div 2,4),16)
#
#                      WriteIR('11', V_IR)
#                      WriteDR('4000',16)
#
#                      WriteIR('11', V_IR)
#                      if Boolean (ch mod 2) then
#                        WriteDR('4000',16)
#                      else
#                        WriteDR('2000',16)
#
#                      for bit := 0 to 15 do
#                      begin
#                        if ((ReadPtrns[gr][ch] shr bit) and $1) <> ((SendPtrns[gr][ch] shr bit) and $1) then
#                        begin
#                          FTestForm.Log.Lines.Add('       Bit[' + IntToStr(bit) + '] is '+IntToStr((ReadPtrns[gr][ch] shr bit) and $1) + ' should be ' + IntToStr((SendPtrns[gr][ch] shr bit) and $1))
#                        end
#                      end
#                    end
#}
#                  end
#                end
#                FTestForm.Log.Lines.Add(TimeToStr(Now())+ '> === ' + 'Stopped due to errors on pass #' + IntToStr(p+1))
#                FTestForm.sbBar.SimpleText := 'Stopped due to errors on pass #' + IntToStr(p+1)
#              end
#              else
#              begin
#            end
#        end
#      end
#			end
#			else
#			begin
#				fStop := true
#                FTestForm.Log.Lines.Add('Pass #' + IntToStr((p div 2) +1 ) + ': Reading Failure ')
#			end
#			if Terminated or fStop then Exit
#		end
#     FTestForm.Log.Lines.EndUpdate
#
#		if old <> VRTX_CH then
#		begin
#			FTestForm.Chains.ItemIndex := old
#			FTestForm.SetChainClick(self)
#		end
#  		FTestForm.Log.Lines.Add(TimeToStr(Now())+ '> === ' + TestNames[FTestType] + ' Test Finished with ' + IntToStr(Errs) + ' Errors' + '===')
#        FTestForm.sbBar.SimpleText := TestNames[FTestType] + ' Test Finished with ' + IntToStr(Errs) + ' Errors'
#        FTestForm.Update
#	end
#    end

#def SetDelaysChips(value,pattern,alcttype): 
def SetDelayChips(alcttype): 
    SendPtrns =[[0 for j in range(NUM_OF_DELAY_CHIPS_IN_GROUP)] for i in range(alct[alcttype].groups)]
    ReadPtrns =[[0 for j in range(NUM_OF_DELAY_CHIPS_IN_GROUP)] for i in range(alct[alcttype].groups)]
    SendValues=[[0 for j in range(NUM_OF_DELAY_CHIPS_IN_GROUP)] for i in range(alct[alcttype].groups)]
    ReadValues=[[0 for j in range(NUM_OF_DELAY_CHIPS_IN_GROUP)] for i in range(alct[alcttype].groups)]

    Wires          = alct[alcttype].channels
    Errs           = 0
    ErrOnePass     = 0
    fStop          = False
    fOddConnector  = False 
    cbPinMapOnRead = True
    cbFlipDelay    = False
    fReadback      = True

    for i in range(NUM_OF_DELAY_GROUPS): 
        for j in range(NUM_OF_DELAY_CHIPS_IN_GROUP): 
            SendValues[i][j] = 0
            SendPtrns [i][j] = 0
            ReadValues[i][j] = 0
            ReadPtrns [i][j] = 0

    WriteIR(0x11    , V_IR)
    WriteDR(0x4000  , 16)

    for i in range(NUM_OF_DELAY_GROUPS): 
        for j in range(NUM_OF_DELAY_CHIPS_IN_GROUP): 
            SendValues[i][j] = 0
            #SendPtrns[i][j]     = random.getrandbits(16)
            SendPtrns[i][j]  = 0x0001
            ReadValues[i][j] = 0
            ReadPtrns [i][j] = 0

    #SetDelayLines(0xF, SendPtrns, SendValues, alcttype)
    ReadPatterns(ReadPtrns,alcttype)

    sentstr = ''
    readstr = ''
    for i in range(alct[alcttype].groups): 
        for j in range(NUM_OF_DELAY_CHIPS_IN_GROUP): 
            sentstr = ("%04X" % SendPtrns[i][j]) + ' ' + sentstr
            readstr = ("%04X" % ReadPtrns[i][j]) + ' ' + readstr

    print('\t ->Sent: %s' % sentstr)
    print('\n\t <-Read: %s' % readstr)

    #pattern=[0x1111,0x2222,0x3333,0x4444,0x5555,0x6666]
    #value=[ 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]

    #print('> === Setting Delays and Patterns ===')
    #SetChain(VRTX_CH)
    #parlen = alct[alcttype].groups + 2
    #cs = 0

    ## Load Patterns, Chip Select Bitmask
    #for i in range (alct[alcttype].groups): 
    #    #for j in range(6): 
    #        #arDelays[i][j].Value    = value[j]
    #        #arDelays[i][j]  = pattern[j] 
    #    cs = cs | (1 << i)
    #    #ReadPtrns.Enabled = True


    #if fOddConnector: 
    #    WriteIR(0x11, V_IR)
    #    WriteDR(0xa000, 16)
    #else: 
    #    WriteIR(0x11, V_IR)
    #    WriteDR(0x4000, 16)

    #dr  = 0x1FF & (~(cs << 2))
    #WriteIR(0xFF  & DelayCtrlWrite  , V_IR)
    #WriteDR(0xFFF & dr              , parlen)

    #WriteIR(0xFF  & DelayCtrlRead   , V_IR)
    #ReadDR (0x0                     , parlen)

    #WriteIR(0xFF  & Wdly            , V_IR)

    #print('Writing Values to ALCT')
    #StartDRShift()
    #
    #for i in range(6): 
    #    DlyVal      =  value[i]
    #    DlyPtrn     =  pattern[i]
    #    DlyPtrnTmp  =  DlyPtrn

    #    #print("<- Chip #%i: Delay=%02X Pattern=%04X" % ((i+1), DlyVal, DlyPtrn))
    #    #      === Pin Remapping ===
    #    if not (cbPinMapOnRead==True): 
    #        DlyPtrnTmp = 0
    #        if (i%2)==1: 
    #            for j in range(8): 
    #                DlyPtrnTmp = DlyPtrnTmp | (((DlyPtrn >> j) & 0x01) << (7 -j)) 
    #            DlyPtrnTmp = DlyPtrnTmp | (DlyPtrn & 0xFF00)
    #        else: 
    #            for j in range(8): 
    #                DlyPtrnTmp = DlyPtrnTmp | (((DlyPtrn >> (j+8)) & 0x01) << (15 -j))
    #            DlyPtrnTmp = DlyPtrnTmp | (DlyPtrn & 0x00ff)

    #    if cbFlipDelay==True: 
    #        DlyValTmp = 0xF & ShiftData(FlipHalfByte(DlyVal), 4, False)
    #    else: 
    #        DlyValTmp = 0xF & ShiftData(DlyVal, 4, False)

    #    DlyPtrnTmp  = ShiftData(DlyPtrnTmp, 16, 5)
    #    #DlyPtrnTmp  = ShiftData(0xFFFF & DlyPtrnTmp, 16, i=5)

    #    if fReadback: 
    #        DlyVal  = DlyValTmp
    #        DlyPtrn = DlyPtrnTmp
    #        print("<- Chip #%i: Delay=%02X Pattern=%04X" % ((i+1), DlyVal, DlyPtrn))
    #ExitDRShift()

    #WriteIR(DelayCtrlWrite, V_IR)
    #WriteDR(0x1FF, parlen)

    #WriteIR(DelayCtrlRead, V_IR)
    #ReadDR(0x0, parlen)

    #WriteIR(0x11, V_IR)
    #WriteDR(0x0001, 16)

    #print('> === Delay Chip Patterns are set  ===')
    
def SubtestMenu(alcttype): 
    while True: 
        os.system('cls')
        print("\n=========================")
        print(" Delay Chips Test Submenu")
        print("=========================\n")
        print("\t 0 Run All Tests")
        print("\t 1 Walking 1 Test")
        print("\t 2 Walking 0 Test")
        print("\t 3 Filling 1 Test")
        print("\t 4 Filling 0 Test")
        print("\t 5 Shifting 5 and A Test")
        print("\t 6 Random Data Test")

        k=input("\nChoose Test or <cr> to return to Main Menu: ")
        os.system('cls')
        print("")
        if not k: break

        if k=="0": 
            Walking1(alcttype)
            Walking0(alcttype)
            Filling1(alcttype)
            Filling0(alcttype)
            Shifting5andA(alcttype)
            RandomData(alcttype)
        if k=="1": Walking1(alcttype)
        if k=="2": Walking0(alcttype)
        if k=="3": Filling1(alcttype)
        if k=="4": Filling0(alcttype)
        if k=="5": Shifting5andA(alcttype)
        if k=="6": RandomData(alcttype)

        k=input("\n<cr> to return to menu: ")

