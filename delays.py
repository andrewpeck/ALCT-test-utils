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

    alct.WriteRegister(0x11, 0x4001, 16)       # Enable Patterns from DelayChips into 384 bits ALCT Register
    jtag.WriteIR      (0x10, alct.V_IR)        # Send 384 bits ALCT Register to PC via JTAG
    DR = jtag.ReadDR  (0x0,Wires) & (2**384 -1) # Mask off 384 bits, just-in-case

    stringDR = format(DR, '096X')   # Convert to Hexdecimal string
    stringDR = stringDR[::-1]       # Invert the String

    for i in range(alct.alct[alcttype].groups):
        for j in range(6):
            num = int(stringDR[0:4],16)     # extract the first four hex digits 
            stringDR = stringDR[4:]         # cut off first 4 hex digits since we are done with them

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

def WalkingBit(bit,alcttype):
    ngroups = alct.alct[alcttype].groups
    SendPtrns  = [[0 for j in range(6)] for i in range(ngroups)]
    ReadPtrns  = [[0 for j in range(6)] for i in range(ngroups)]
    SendValues = [[0 for j in range(6)] for i in range(ngroups)]
    
    Wires = alct.alct[alcttype].channels
    Errs        = 0
    ErrOnePass  = 0
    fStop       = False
    fStopOnError= True

    if bit==1: 
        print('    Walking 1 Test')
    elif bit==0: 
        print('    Walking 0 Test')
    else: 
        raise Exception("Invalid test selected")
        

    alct.SetChain(alct.VIRTEX_CONTROL)

    for bit in range(Wires):
        alct.WriteRegister(0x11,0x4000,16)

        for i in range(alct.alct[alcttype].groups):
            for j in range(6):
                if bit==1: 
                    SendValues[i][j]    = 0
                    SendPtrns [i][j]    = 0 or ((bit // 16) == ((i*6)+j)) << (bit % 16)
                    ReadPtrns [i][j]    = 0
                if bit==0:
                    SendValues[i][j] = 0x0000
                    SendPtrns [i][j] = 0xFFFF & (~(((bit//16)==((i*6)+j)) << (bit%16)))

        SetDelayLines(0x7F, SendPtrns, SendValues, alcttype)
        ReadPtrns = ReadPatterns(alcttype)

        ErrOnePass = CheckPatterns(SendPtrns, ReadPtrns,alcttype)
        Errs = Errs + ErrOnePass
        if (ErrOnePass > 0):
            print("\t Error on bit %3i (Chip #%2i Channel %2i)" % (bit+1, bit//16 + 1, bit%16 + 1 ))
        #PrintPatterns(alcttype, SendPtrns, ReadPtrns)

    # Fini
    if (Errs == 0): 
        if bit==1:
            print       ('\t ====> PASSED: Walking 1 Test' % Errs)
            logging.info('\t ====> PASSED: Walking 1 Test' % Errs)
        if bit==0:
            print       ('\t ====> PASSED: Walking 0 Test' % Errs)
            logging.info('\t ====> PASSED: Walking 0 Test' % Errs)
        beeper.passed()
    else: 
        if bit==1:
            print       ('\t ====> FAILED: Walking 1 Test Finished with %i Errors ' % Errs)
            logging.info('\t ====> FAILED: Walking 1 Test Finished with %i Errors ' % Errs)
        if bit==0:
            print       ('\t ====> FAILED: Walking 0 Test Finished with %i Errors ' % Errs)
            logging.info('\t ====> FAILED: Walking 0 Test Finished with %i Errors ' % Errs)
        beeper.failed()
    return (Errs)

# Sends a walking 1 pattern through the delay ASICs
def Walking1(alcttype):
    return(WalkingBit(1,alcttype)

# Sends a walking 1 pattern through the delay ASICs
def Walking0(alcttype):
    return(WalkingBit(0,alcttype)

def FillingBit(alcttype):
    ngroups = alct.alct[alcttype].groups
    SendPtrns  = [[0 for j in range(6)] for i in range(ngroups)]
    SendValues = [[0 for j in range(6)] for i in range(ngroups)]

    Wires = alct.alct[alcttype].channels
    Errs       = 0
    ErrOnePass = 0
    fStop      = False

    if bit==1:   
        print       ('    Filling 1s Test')
    elif bit==0: 
        print       ('    Filling 0s Test')
    else: 
        raise Exception("Invalid Test Selected")

    alct.SetChain(alct.VIRTEX_CONTROL)

    for i in range(alct.alct[alcttype].groups):
        for j in range(6):
            if bit==1: 
                SendValues[i][j] = 0x0000
                SendPtrns [i][j] = 0x0000
            if bit==0: 
                SendValues[i][j] = 0x0000
                SendPtrns [i][j] = 0xFFFF

    SetDelayLines(0xF,SendPtrns,SendValues,alcttype)

    for bit in range (Wires):
        alct.WriteRegister(0x11,0x4000,0x16)

        for i in range(alct.alct[alcttype].groups):
            for j in range(6):
                if bit==1: 
                    SendValues[i][j] = 0
                    SendPtrns [i][j] = SendPtrns[i][j] | (((bit//16) == ((i*6)+j)) << (bit % 16))
                if bit==0: 
                    SendValues[i][j] = 0x0000
                    SendPtrns [i][j] = SendPtrns[i][j] & (~(((bit // 16) == ((i*6)+j)) << (bit % 16)))

        SetDelayLines(0xF, SendPtrns, SendValues, alcttype)
        ReadPtrns = ReadPatterns(alcttype)

        ErrOnePass = CheckPatterns(SendPtrns, ReadPtrns,alcttype)
        Errs       = Errs + ErrOnePass
        if (ErrOnePass > 0):
            print("\t Error on bit %3i (Possible Problem with Chip #%2i Channel %2i" % (bit+1, bit//16 + 1, bit%16 + 1 ))
    # Fini
    if (Errs==0):
        if bit==1: 
            print       ('\t ====> PASSED: Filling by 1s Test' % Errs)
            logging.info('\t ====> PASSED: Filling by 1s Test' % Errs)
        if bit==0:
            print        ('\t ====> PASSED: Filling by 0s Test' % Errs)
            logging.info ('\t ====> PASSED: Filling by 0s Test' % Errs)
        beeper.passed()
    else: 
        if bit==1:
            print       ('\t ====> FAILED: Filling by 1s Test Finished with %i Errors ' % Errs)
            logging.info('\t ====> FAILED: Filling by 1s Test Finished with %i Errors ' % Errs)
        if bit==0:
            print        ('\t ====> FAILED: Filling by 0s Test Finished with %i Errors ' % Errs)
            logging.info ('\t ====> FAILED: Filling by 0s Test Finished with %i Errors ' % Errs)
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
def Shifting5andA(alcttype, npasses=25):
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
        for j in range(6): 
            read = read + format(ReadPtrns[i][j],'04X')
            send = send + format(SendPtrns[i][j],'04X')

        if ErrOnePass > 0:
            print("        Pass %2i of %2i" % (p+1, npasses))
            print("           Error: Write=%s Read=%s " % (send, read))
        else: 
            if debug: 
                print ("    Pass %2i of %2i" % (p+1, npasses))
                print("\t ====> PASSED") 

    # Reset Delay Chips (returns Current to normal values
    for i in range(alct.alct[alcttype].groups):
        for j in range(6):
            SendValues [i][j] = 0x0000
            SendPtrns  [i][j] = 0x0000
    SetDelayLines(0xF, SendPtrns, SendValues, alcttype)

    # Fini
    if (Errs == 0): 
        print        ('\t ====> PASSED: Shifting 5 and A Test' % Errs)
        logging.info ('\t ====> PASSED: Shifting 5 and A Test' % Errs)
        beeper.passed()
    else: 
        print        ('\t ====> FAILED: Shifting 5 and A Test Finished with %i Errors ' % Errs)
        logging.info ('\t ====> FAILED: Shifting 5 and A Test Finished with %i Errors ' % Errs)
        beeper.failed()

    return (Errs)

# Sends random patterns into delay ASICs
def RandomData(alcttype, npasses=50):
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
        for j in range(6): 
            read = read + format(ReadPtrns[i][j],'04X')
            send = send + format(SendPtrns[i][j],'04X')

        # If error, print pattern
        if ErrOnePass > 0:
            print("        Pass %2i of %2i" % (p+1, npasses))
            print("           Error: Write=%s Read=%s " % (send, read))
        else: 
            if debug: 
                print ("    Pass %i of %i" % (p+1, npasses))
                print("\t ====> PASSED") 


    # Reset Delay Chips (returns Current to normal values
    for i in range(alct.alct[alcttype].groups):
        for j in range(6):
            SendValues[i][j] = 0x0000
            SendPtrns [i][j] = 0x0000

    SetDelayLines(0xF, SendPtrns, SendValues, alcttype)

    # Fini
    if (Errs==0): 
        print        ('\t ====> PASSED: Random Data Test' % Errs)
        logging.info ('\t ====> PASSED: Random Data Test' % Errs)
        beeper.passed()
    else: 
        print        ('\t ====> FAILED: Random Data Test Finished with %i Errors ' % Errs)
        logging.info ('\t ====> FAILED: Random Data Test Finished with %i Errors ' % Errs)
        beeper.failed()
    return (Errs)

#def GeneratePattern():
#    begin
#    case FTestType of
#        0..3:    pass  = Wires
#        4:       pass  = FNumOfPasses*2
#        5:      pass  = FNumOfPasses
#    Errs = 0
#    #FTestForm.PrSt.Max  = pass
#    #FTestForm.PrSt.Position  = 0
#    fStop = False
#    FTestForm.Log.Lines.Add(TimeToStr(Now())+ '> === ' + TestNames[FTestType] + '===')
#    FTestForm.sbBar.SimpleText  = TestNames[FTestType]
#
#    alct.SetChain(VRTX_CH)
#
#    # reset delay lines
#    for i in range(alct.alct[alcttype].groups):
#        for j in range(6):
#            SendValues[i][j] = 0
#            if FTestType = 3 :
#                SendPtrns[i][j]     = 0xFFFF
#            else :
#                SendPtrns[i][j]     = 0x0000
#
#    SetDelayLines(0x7F, SendPtrns, SendValues, alcttype)
#
#    for p in range(pass):
#        #FTestForm.PrSt.Position  = p+1
#        if FTestType = 4 then
#            FTestForm.lbPrSt.Caption  = 'Pass #' + IntToStr((p div 2) + 1) + ' of ' +IntToStr(pass div 2)
#        else
#            FTestForm.lbPrSt.Caption  = 'Pass #' + IntToStr(p+1) + ' of ' +IntToStr(pass)
#
#        case FTestType of
#    0..3:  if not (FTestForm.FindComponent('DG'+IntToStr(p div (alct.alct[alcttype].chips * ALCTBoard.delaylines))) as TCheckBox).Checked then
#            continue
#
#    alct.WriteRegister(0x11,0x4000,0x16)
#
#        for i = 0 to alct.alct[alcttype].groups - 1 do
#        begin
#                for j =0 to alct.alct[alcttype].chips - 1 do
#                begin
#                    SendValues[i][j]  = 0
#                    case FTestType of
#                      0: SendPtrns[i][j]      = 0 or (Integer ((p div 16) = ((i*6)+j)) shl (p mod 16))
#                      1: SendPtrns[i][j]      = $FFFF and (not(Integer ((p div 16) = ((i*6)+j)) shl (p mod 16)))
#                      2: SendPtrns[i][j]      = SendPtrns[i][j] or ((Integer ((p div 16) = ((i*6)+j)) shl (p mod 16)))
#                      3: SendPtrns[i][j]      = SendPtrns[i][j] and (not(Integer ((p div 16) = ((i*6)+j)) shl (p mod 16)))
#                      4: begin
#                if Boolean ((p+1) mod 2) then
#                                  SendPtrns[i][j]  = $5555
#                              else
#                                  SendPtrns[i][j]  = $AAAA
#               end
#                      5: SendPtrns[i][j]  = Random($FFFF)
#                    else
#                        SendPtrns[i][j]  = 0
#                    end
#                    ReadPtrns[i][j]      = 0
#                end
#            end
#
#            FTestForm.SetDelayLines($7f, SendPtrns, SendValues)
#
#            if FTestForm.ReadPatterns(ReadPtrns) = Wires then
#            begin
#                ErrOnePass  = FTestForm.CheckPatterns(SendPtrns, ReadPtrns)
#                Errs  = Errs + ErrOnePass
#        sentstr  = ''
#        readstr  = ''
#                for gr = 0 to alct.alct[alcttype].groups - 1 do
#                    for ch =0 to alct.alct[alcttype].chips - 1 do
#          begin
#            sentstr  = IntToHex(SendPtrns[gr][ch], 4) + ' ' +sentstr
#                        readstr  = IntToHex(ReadPtrns[gr][ch], 4) + ' ' +readstr
#          end
#        status  = readstr
#        FTestForm.sbBar.SimpleText  = status
#
#                if ErrOnePass > 0 then
#                begin
#                    FTestForm.Log.Lines.Add('Pass: #' + IntToStr(p+1) + ' with ' + IntToStr(ErrOnePass) + ' Errors ')
#//          FTestForm.Log.Lines.Add('Possibly problem with Chip #' + IntToStr(p div 16 + 1) + ' Channel #' + IntToStr(p mod 16 + 1))
#          FTestForm.Log.Lines.Add('->Sent: '+sentstr)
#          FTestForm.Log.Lines.Add('<-Read: '+readstr)
#          if fStopOnError then
#          begin
#            //FTestForm.Log.Lines.Add('->Sent: '+sentstr)
#            //FTestForm.Log.Lines.Add('<-Read: '+readstr)
#            if not fRepeatLast then
#              begin
#                fStop  = True
#                for gr = 0 to alct.alct[alcttype].groups - 1 do
#                begin
#                  for ch =0 to alct.alct[alcttype].chips - 1 do
#                  begin
#{                    if ReadPtrns[gr][ch] <> SendPtrns[gr][ch] then
#                    begin
#                      FTestForm.Log.Lines.Add('    Group #'+ IntToStr(gr+1) + ':-> Chip #' + IntToStr(ch+1) + ' Read 0x'+IntToHex(ReadPtrns[gr][ch], 4) + ' Expected 0x' + IntToHex(SendPtrns[gr][ch], 4))
#                      jtag.WriteIR('0A', alct.V_IR)
#                      jtag.WriteDR(IntToHex((gr*6+ch) div 2,4),16)
#
#                      jtag.WriteIR('11', alct.V_IR)
#                      jtag.WriteDR('4000',16)
#
#                      jtag.WriteIR('11', alct.V_IR)
#                      if Boolean (ch mod 2) then
#                        jtag.WriteDR('4000',16)
#                      else
#                        jtag.WriteDR('2000',16)
#
#                      for bit  = 0 to 15 do
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
#                FTestForm.sbBar.SimpleText  = 'Stopped due to errors on pass #' + IntToStr(p+1)
#              end
#              else
#              begin
#            end
#        end
#      end
#            end
#            else
#            begin
#                fStop  = true
#                FTestForm.Log.Lines.Add('Pass #' + IntToStr((p div 2) +1 ) + ': Reading Failure ')
#            end
#            if Terminated or fStop then Exit
#        end
#     FTestForm.Log.Lines.EndUpdate
#
#        if old <> VRTX_CH then
#        begin
#            FTestForm.Chains.ItemIndex  = old
#            FTestForm.SetChainClick(self)
#        end
#          FTestForm.Log.Lines.Add(TimeToStr(Now())+ '> === ' + TestNames[FTestType] + ' Test Finished with ' + IntToStr(Errs) + ' Errors' + '===')
#        FTestForm.sbBar.SimpleText  = TestNames[FTestType] + ' Test Finished with ' + IntToStr(Errs) + ' Errors'
#        FTestForm.Update
#    end
#    end

#def SetDelaysChips(value,pattern,alcttype):

#def SetDelayChips(alcttype):
#
#    SendPtrns  = np.ndarray(shape=(alct.alct[alcttype].groups,6),dtype=np.int)
#    ReadPtrns  = np.ndarray(shape=(alct.alct[alcttype].groups,6),dtype=np.int)
#    SendValues = np.ndarray(shape=(alct.alct[alcttype].groups,6),dtype=np.int)
#
#    Wires          = alct.alct[alcttype].channels
#    Errs           = 0
#    ErrOnePass     = 0
#    fStop          = False
#    fOddConnector  = False
#    cbPinMapOnRead = True
#    cbFlipDelay    = False
#    fReadback      = True
#
#    for i in range(alct.alct[alcttype].groups):
#        for j in range(6):
#            SendValues[i][j] = 0
#            SendPtrns [i][j] = 0
#            ReadPtrns [i][j] = 0
#
#    alct.WriteRegister(0x11,0x4000,0x16)
#
#    for i in range(alct.alct[alcttype].groups):
#        for j in range(6):
#            SendValues[i][j] = 0x0000
#            SendPtrns[i][j]  = 0x0001
#            ReadPtrns [i][j] = 0x0000
#
#    #SetDelayLines(0xF, SendPtrns, SendValues, alcttype)
#    ReadPtrns = ReadPatterns(alcttype)
#
#    #PrintPatterns(alcttype, SendPtrns, ReadPtrns):
#
#    #pattern=[0x1111,0x2222,0x3333,0x4444,0x5555,0x6666]
#    #value=[ 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
#
#    #print('> === Setting Delays and Patterns ===')
#    #alct.SetChain(VRTX_CH)
#    #parlen = alct.alct[alcttype].groups + 2
#    #cs = 0
#
#    ## Load Patterns, Chip Select Bitmask
#    #for i in range (alct.alct[alcttype].groups):
#    #    #for j in range(6):
#    #        #arDelays[i][j].Value    = value[j]
#    #        #arDelays[i][j]  = pattern[j]
#    #    cs = cs | (1 << i)
#    #    #ReadPtrns.Enabled = True
#
#
#    #if fOddConnector:
#    #    jtag.WriteIR(0x11, alct.V_IR)
#    #    jtag.WriteDR(0xa000, 16)
#    #else:
#    #    jtag.WriteIR(0x11, alct.V_IR)
#    #    jtag.WriteDR(0x4000, 16)
#
#    #dr  = 0x1FF & (~(cs << 2))
#    #jtag.WriteIR(0xFF  & alct.DelayCtrlWrite  , V_IR)
#    #jtag.WriteDR(0xFFF & dr              , parlen)
#
#    #jtag.WriteIR(0xFF  & alct.DelayCtrlRead   , V_IR)
#    #jtag.ReadDR (0x0                     , parlen)
#
#    #jtag.WriteIR(0xFF  & alct.Wdly            , V_IR)
#
#    #print('Writing Values to ALCT')
#    #jtag.StartDRShift()
#    #
#    #for i in range(6):
#    #    DlyVal      =  value[i]
#    #    DlyPtrn     =  pattern[i]
#    #    DlyPtrnTmp  =  DlyPtrn
#
#    #    #print("<- Chip #%i: Delay=%02X Pattern=%04X" % ((i+1), DlyVal, DlyPtrn))
#    #    #      === Pin Remapping ===
#    #    if not (cbPinMapOnRead==True):
#    #        DlyPtrnTmp = 0
#    #        if (i%2)==1:
#    #            for j in range(8):
#    #                DlyPtrnTmp = DlyPtrnTmp | (((DlyPtrn >> j) & 0x01) << (7 -j))
#    #            DlyPtrnTmp = DlyPtrnTmp | (DlyPtrn & 0xFF00)
#    #        else:
#    #            for j in range(8):
#    #                DlyPtrnTmp = DlyPtrnTmp | (((DlyPtrn >> (j+8)) & 0x01) << (15 -j))
#    #            DlyPtrnTmp = DlyPtrnTmp | (DlyPtrn & 0x00ff)
#
#    #    if cbFlipDelay==True:
#    #        DlyValTmp = 0xF & jtag.ShiftData(FlipHalfByte(DlyVal), 4, False)
#    #    else:
#    #        DlyValTmp = 0xF & jtag.ShiftData(DlyVal, 4, False)
#
#    #    DlyPtrnTmp  = jtag.ShiftData(DlyPtrnTmp, 16, 5)
#    #    #DlyPtrnTmp  = jtag.ShiftData(0xFFFF & DlyPtrnTmp, 16, i=5)
#
#    #    if fReadback:
#    #        DlyVal  = DlyValTmp
#    #        DlyPtrn = DlyPtrnTmp
#    #        print("<- Chip #%i: Delay=%02X Pattern=%04X" % ((i+1), DlyVal, DlyPtrn))
#    #jtag.ExitDRShift()
#
#    #jtag.WriteIR(alct.DelayCtrlWrite, V_IR)
#    #jtag.WriteDR(0x1FF, parlen)
#
#    #jtag.WriteIR(alct.DelayCtrlRead, V_IR)
#    #jtag.ReadDR(0x0, parlen)
#
#    #jtag.WriteIR(0x11, alct.V_IR)
#    #jtag.WriteDR(0x0001, 16)
#
#    #print('> === Delay Chip Patterns are set  ===')

def SubtestMenu(alcttype):
    while True:
        common.ClearScreen()
        print("\n===============================================================================")
        print(  " Delay Chips Test Submenu")
        print(  "===============================================================================\n")
        print("\t 0 Run All Tests")
        print("\t 1 Walking 1 Test")
        print("\t 2 Walking 0 Test")
        print("\t 3 Filling 1 Test")
        print("\t 4 Filling 0 Test")
        print("\t 5 Shifting 5 and A Test")
        print("\t 6 Random Data Test")

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
