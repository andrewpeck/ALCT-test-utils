#!/usr/bin/env python3

################################################################################
# Functions for testing the Slow Control Circuits
################################################################################
import time

import jtaglib as jtag
import common
import alct

import sys

#-------------------------------------------------------------------------------
# Slow Control JTAG Instruction OP-Codes
#-------------------------------------------------------------------------------

FIFO_RESET = 0xC
FIFO_READ  = 0xA
FIFO_WRITE = 0x9


# | Binary  | Hex  | Oct | OpCode | Description             | Chip Select    | Register   | Length |
# |---------+------+-----+--------+-------------------------+----------------+------------+--------|
# | 000 000 | 0x00 |  00 | RdID   | Read   ID Register      | None           | Bypass     |     40 |
# | 000 001 | 0x01 |  01 | WThrs  | Reset  Threshold DAC    | /thr_reset     | Bypass     |      1 |
# | 000 010 | 0x02 |  02 | DRst   | Reset  Delay ASIC       | /dly_reset     | Bypass     |      1 |
# | 000 100 | 0x03 |  03 | WTp    | Write  Test Pulse DAC   | /cs_test_pulse | Serial Bus |      8 |
# | 001 000 | 0x08 |  10 | WThr0  | Write  Threshold DAC0   | /cs_write_thr0 | Serial Bus |     12 |
# | 001 001 | 0x09 |  11 | WThr1  | Write  Threshold DAC1   | /cs_write_thr1 | Serial Bus |     12 |
# | 001 010 | 0x0A |  12 | WThr2  | Write  Threshold DAC2   | /cs_write_thr2 | Serial Bus |     12 |
# | 001 011 | 0x0B |  13 | WThr3  | Write  Threshold DAC3   | /cs_write_thr3 | Serial Bus |     12 |
# | 010 000 | 0x10 |  20 | RThr0  | Read   Threshold ADC0   | /cs_read_thr0  | Serial Bus |     11 |
# | 010 001 | 0x11 |  21 | RThr1  | Read   Threshold ADC1   | /cs_read_thr1  | Serial Bus |     11 |
# | 010 010 | 0x12 |  22 | RThr2  | Read   (shared)  ADC2   | /cs_read_thr2  | Serial Bus |     11 |
# | 010 011 | 0x13 |  23 | RThr3  | Read   Threshold ADC3   | /cs_read_thr3  | Serial Bus |     11 |
# | 010 100 | 0x14 |  24 | RThr4  | Read   Threshold ADC4   | /cs_read_thr4  | Serial Bus |     11 |
# | 011 000 | 0x18 |  30 | WDly0  | Write  Delay ASIC Grp 0 | /cs_write_dly0 | Serial Bus |     24 |
# | 011 001 | 0x19 |  31 | WDly1  | Write  Delay ASIC Grp 1 | /cs_write_dly1 | Serial Bus |     24 |
# | 011 010 | 0x1A |  32 | WDly2  | Write  Delay ASIC Grp 2 | /cs_write_dly2 | Serial Bus |     24 |
# | 011 011 | 0x1B |  33 | WDly3  | Write  Delay ASIC Grp 3 | /cs_write_dly3 | Serial Bus |     24 |
# | 011 100 | 0x1C |  34 | WDly4  | Write  Delay ASIC Grp 4 | /cs_write_dly4 | Serial Bus |     24 |
# | 011 101 | 0x1D |  35 | WDly5  | Write  Delay ASIC Grp 5 | /cs_write_dly5 | Serial Bus |     24 |
# | 011 110 | 0x1E |  36 | WDly6  | Write  Delay ASIC Grp 6 | /cs_write_dly6 | Serial Bus |     24 |
# | 100 000 | 0x20 |  40 | WTpg   | Write  Test PulseGroup  | None           | tp_group[] |      7 |
# | 100 001 | 0x21 |  41 | RTpg   | Read   Test PulseGroup  | None           | tp_group[] |      7 |
# | 100 010 | 0x22 |  42 | WTps   | Write  Test PulseStrip  | None           | tp_strip[] |      6 |
# | 100 011 | 0x23 |  43 | RTps   | Read   Test PulseStrip  | None           | tp_strip[] |      6 |
# | 100 100 | 0x24 |  44 | WSbr   | Write  Standby Register | None           | /standby[] |     42 |
# | 100 101 | 0x25 |  45 | RSbr   | Read   Standby Register | None           | /standby[] |     42 |
# | 100 110 | 0x26 |  46 | WTpd   | Write  TP Power Down    | None           | /tp_pd[]   |      1 |
# | 100 111 | 0x27 |  47 | RTpd   | Read   TP Power Down    | None           | /tp_pd[]   |      1 |
# | 111 111 | 0x3F |  77 | Bypass | Bypass Scan             | None           | Bypass     |      1 |
# |---------+-----+-----+--------+-------------------------+----------------+------------+--------|

RegSz = {
   0x00:  40, 
   0x01:   1, 
   0x02:   1, 
   0x03:   8, 
   0x08:  12, 
   0x09:  12, 
   0x0A:  12, 
   0x0B:  12, 
   0x10:  11, 
   0x11:  11, 
   0x12:  11, 
   0x13:  11, 
   0x14:  11, 
   0x18:  24, 
   0x19:  24, 
   0x1A:  24, 
   0x1B:  24, 
   0x1C:  24, 
   0x1D:  24, 
   0x1E:  24, 
   0x20:   7, 
   0x21:   7, 
   0x22:   6, 
   0x23:   6, 
   0x24:  42, 
   0x25:  42, 
   0x26:   1, 
   0x27:   1, 
   0x3F:   1
} 

RdID   =  0x00  # Read ID Register
WThrs  =  0x01  # Reset Threshold DAC
DRst   =  0x02  # Reset Delay ASIC
WTp    =  0x03  # Write Test Pulse DAC
WThr0  =  0x08  # Write Threshold DAC 0
WThr1  =  0x09  # Write Threshold DAC 1
WThr2  =  0x0A  # Write Threshold DAC 2
WThr3  =  0x0B  # Write Threshold DAC 3
RThr0  =  0x10  # Read Threshold DAC 0
RThr1  =  0x11  # Read Threshold DAC 1
RThr2  =  0x12  # Read Threshold DAC 2
RThr3  =  0x13  # Read Threshold DAC 3
RThr4  =  0x14  # Read Threshold DAC 4
WDly0  =  0x18  # Write Delay ASIC Group 0
WDly1  =  0x19  # Write Delay ASIC Group 1
WDly2  =  0x1A  # Write Delay ASIC Group 2
WDly3  =  0x1B  # Write Delay ASIC Group 3
WDly4  =  0x1C  # Write Delay ASIC Group 4
WDly5  =  0x1D  # Write Delay ASIC Group 5
WDly6  =  0x1E  # Write Delay ASIC Group 6
WTpg   =  0x20  # Write Test Pulse Group
RTpg   =  0x21  # Read Test Pulse Group
WTps   =  0x22  # Write Test Pulse Strip
RTps   =  0x23  # Read Test Pulse Strip
WSbr   =  0x24  # Write Standby Register
RSbr   =  0x25  # Read Standby Register
WTpd   =  0x26  # Write Test Pulse Power Down
RTpd   =  0x27  # Read Test Pulse Power Down
Bypass =  0x3F  # Bypass Scan

#------------------------------------------------------------------------------
# Slow Control Control
#------------------------------------------------------------------------------
def WriteRegister(reg, value): 
    length = RegSz[reg]             # length of register
    mask   = 2**(length)-1          # Bitmask of 1s to mask the register
    jtag.WriteIR(reg, SC_IR)             
    return(jtag.WriteDR(value & mask,length))

def ReadRegister(reg): 
    jtag.WriteIR(reg, SC_IR)
    result = jtag.ReadDR(0x0,RegSz[reg])
    return (result)



#------------------------------------------------------------------------------
# Slow Control Functions
#------------------------------------------------------------------------------

# Set Standby Register for a Particular Group
def SetGroupStandbyReg(group, value):
    wgroups = 7
    data = ReadStandbyReg()
    if (group >=0) and (group < wgroups):
        res = data
        res = (res ^ ((res >> (group*6) & (0x3f)) << (6*group))) | ((value & 0x3F) << (group*6))
        SetStandbyReg(res & 0xFFFFFFFFFFFF)


# Read Standby Register for a Particular Group
def ReadGroupStandbyReg(group):
    alct.SetChain(SLOW_CTL)
    wgroups = 7
    data    = ReadStandbyReg()
    if (group >=0) and (group < wgroups):
        return((data >> (group*6)) & 0x3F)
    else:
        print("Problem with Read Group Standby Reg")

def SetStandbyReg(value):
    alct.SetChain(SLOW_CTL)
    return (WriteRegister(WSbr,value))

def ReadStandbyReg():
    alct.SetChain(SLOW_CTL)
    return (ReadRegister(RSbr)) 

def SetStandbyForChan(chan, onoff):
    if (chan >= 0) and (chan < 42):
        value = ReadGroupStandbyReg(chan // 6) & 0x3F
        value = (value ^ (((value >> (chan % 6)) & 0x1 ) << (chan % 6) )) | (int(onoff) << (chan % 6))
        SetGroupStandbyReg(chan % 6, value)

def SetTestPulsePower(sendval):
    return(WriteRegister(WTpd,sendval))

def ReadTestPulsePower():
    return (ReadRegister(RTpd))

def SetTestPulsePowerAmp(value):
    temp = 0
    # WHAT THE FUCK IS THIS FOR
    for i in range(0,len-1):
        temp = temp | (((value >> i) & 0x1) << (7-i))
    WriteRegister(WTp,temp)

def SetTestPulseWireGroupMask(value):
    WriteRegister(WTpg,value)

def ReadTestPulseWireGroupMask():
    return(ReadRegister(RTpg))

def SetTestPulseStripLayerMask(value):
    WriteRegister(WTps,value)

def ReadTestPulseStripLayerMask():
    WriteRegister(RTps,value)

# Set AFEB Threshold (value from 0-255)
# Sets threshold in ADC counts
def SetThreshold(ch, value):
    alct.SetChain(0x0)
    DRlength  = 12
    data    = 0
    realch  = ch
    if (ch >= 33):
        realch = ch+3
    time.sleep(0.01)     #sleep 10 ms
    value = value & 0xFF
    value = value | (( realch % 12) << 8)

    for i in range(DRlength):
        data = data | (((value >> i)  & 0x1) << (11-i))

    jtag.WriteIR(0xFF & (0x8+(realch // 12)), SC_IR)
    jtag.WriteDR(data & 0xFFF, DRlength)

# Returns AFEB Threshold on channel ch
# Returns value in ADC Counts (0-1023)
def ReadThreshold(ch):
    alct.SetChain(SLOW_CTL)
    DRLength = 11
    result = 0
    adr = 0

    channel = 0xFF & arADCChannel[ch]
    chip    = 0xFF & (0x10 + arADCChip[ch])


    for i in range(4):
        adr = 0xFFF & (adr | (((channel >> i) & 0x1) << (3-i)))

    time.sleep(0.01)     #sleep 10 ms

    jtag.WriteIR(chip, SC_IR)
    jtag.WriteDR(adr,  DRLength)

    #time.sleep(0.1)     #sleep 10 ms

    jtag.WriteIR(chip, SC_IR)
    read = jtag.ReadDR(adr,DRLength)

    result=common.FlipDR(read,DRLength)

    return(result)

# Read ALCT board 12 bit voltage monitoring
# Returns value in ADC counts (0-1023)
def ReadVoltageADC(chan):
    alct.SetChain(SLOW_CTL)
    DRlength = 11
    result = 0
    adr = 0

    # Clever thing that generates the address based on the channel
    for i in range(4):
        adr = adr | ((((chan+6) >> i) & 0x1) << (3-i))

    # Bitmask 
    adr = adr & 0xFFF

    # Poll ADC
    for i in range(3):
        jtag.WriteIR(0x12, SC_IR)
        read = jtag.ReadDR(adr, DRlength)

    # Flip Bits (change endianess)
    return(common.FlipDR(read,DRlength))

# Read ALCT board 12 bit current monitoring
# Returns value in ADC counts (0-1023)
def ReadCurrentADC(chan):
    alct.SetChain(SLOW_CTL)
    DRlength = 11
    adr = 0

    for i in range(4):
        adr = adr | ((((chan+2) >> i) & 0x1) << (3-i))

    for i in range(0,3):
        jtag.WriteIR(0x12, SC_IR)
        read = jtag.ReadDR(adr, DRlength)

    return (common.FlipDR(read,DRlength))

# Read on board temperature sensor
# Returns value in ADC counts (0-1023)
def ReadTemperatureADC():
    DRlength = 11
    for i in range(3):
        jtag.WriteIR(0x12, SC_IR)
        read = jtag.ReadDR(0x5, DRlength)

    return (common.FlipDR(read,DRlength))

# Read on board temperature sensor
# Returns value in degrees C
def ReadTemperature():
    return (ReadTemperatureADC()*arTemperature.coef-50)

# Checks All board Thresholds
# Optional depth argument allows for a quick scan
# Only the modulo of the depth will be checked
# e.g. depth=1 checks all thresholds
#      depth=17 will check 0,17,34,...etc
def CheckThresholds(NUM_AFEBS,depth=1):
    print("Checking AFEB Thresholds")
    Errs=0
    for afeb in range(NUM_AFEBS):
        if afeb !=0: print("")
        for thresh in range(256):
            if thresh%depth == 0:
                write=thresh
                SetThreshold(afeb,write)
                read = ReadThreshold(afeb)/4.0
                output=("\t AFEB #%02i: Write=%03i Read=%03.0f" % (afeb,write,read) )
                common.Printer(output)
                if abs(write - read) > ThreshToler:
                    print("\nERROR in AFEB #%02i: Write=%03i Read=%03.0f" % (afeb,write,read) )
                    Errs +=1

    if Errs==0:
        print('\n\t ====> Passed')
        return(0)
    else:
        print('\t ====> Failed Thresholds Quick Test with %i Errors' % Errs)
        return(Errs)

# Checks ALCT-AFEB standby register
def CheckStandbyRegister():
    print("Checking Standby Register")
    Errs = 0
    for i in range(7):
        sendval = 0x30 | (i & 0x0f)
        SetGroupStandbyReg(i, sendval)
        readval = ReadGroupStandbyReg(i)
        if readval != sendval:
            Errs = Errs+1
            print('Error: Standby Register for Wire Group #%i send=%02X read=%02X' % ((i+1),sendval,readval))

    if Errs==0:
        print('\t ====> Passed')
        return(0)
    else:
        print('\t ====> Failed Standby Register Test with %i Errors' % Errs)
        return(Errs)

# Checks Test Pulse Down register
def CheckTestPulsePowerDown():
    print('Checking Test Pulse Power Down')
    Errs = 0
    sendval = 0
    SetTestPulsePower(sendval)
    readval = ReadTestPulsePower()
    if readval != sendval:
        print('\t Error: Test Pulse Power Down send=%02X read=%02X' % (sendval,readval))
        Errs+=1

    if Errs==0:
        print('\t ====> Passed')
        return(0)
    else:
        print('\t ====> Failed Test Pulse Power Down Test with %i Errors' % Errs)
        return(Errs)

# Checks Test Pulse Up register
def CheckTestPulsePowerUp():
    print('Checking Test Pulse Power Up')
    Errs = 0
    sendval = 0
    SetTestPulsePower(sendval)
    readval = ReadTestPulsePower()
    if readval != sendval:
        print('Error: Test Pulse Power Up send=%02X read=%02X' % (sendval,readval))
        Errs += 1

    if Errs==0:
        print('\t ====> Passed')
        return(0)
    else:
        print('\t ====> Failed Test Pulse Power Up Test with %i Errors' % Errs)
        return(Errs)

def CheckTestPulseWireGroupMask():
    print('Checking Test Pulse Wire Group Mask')
    Errs = 0
    sendval = 0
    for sendval in range (0x7F+1):
        SetTestPulseWireGroupMask(sendval)
        readval = ReadTestPulseWireGroupMask()
        if readval != sendval:
            print('\t Error: Test Pulse Wire Group Mask send=%02X read=%02X' % (sendval,readval))
            Errs += 1
    if Errs==0:
        print('\t ====> Passed')
        return(0)
    else:
        print('\t ====> Failed Test Pulse Wire Group Mask Test with %i Errors' % Errs)
        return(Errs)

def CheckTestPulseStripLayerMask():
    print('Checking Test Pulse Strip Layer Mask')
    Errs = 0
    for sendval in range(0x3F+1):
        SetTestPulseWireGroupMask(sendval)
        readval = ReadTestPulseWireGroupMask()
        if readval != sendval:
            print('\t Error: Test Pulse Strip Layer Mask send=%02X read=%02X' % (sendval,readval))
            Errs += 1
    if Errs==0:
        print('\t ====> Passed')
        return(0)
    else:
        print('\t ====> Failed Test Pulse Wire Group Mask Test with %i Errors' % Errs)
        return(Errs)

# Automatically checks all voltages for a given alct type
def CheckVoltages(alcttype):
    print('Checking Voltages')
    Errs=0
    for i in range(alct[alcttype].pwrchans):
        readval = ReadVoltageADC(i)
        voltage = readval * arVoltages[i].coef
        toler   = arVoltages[i].toler
        ref     = arVoltages[i].refval

        if abs(voltage-ref) > toler:
            Errs+=1
            print("\t Fail", end='')
        else:
            print("\t Pass ", end='')

        print("\t %s \tread=%.03f expect=%.03f +- %0.03f" % (arVoltages[i].ref, voltage, ref, toler))

    if Errs==0:
        print('\t ====> Passed')
        return(0)
    else:
        print('\t ====> Failed Voltage Test with %i Errors' % Errs)
        return(Errs)

# Automatically checks all currents for a given alct type
def CheckCurrents(alcttype):
    print('Checking Currents')
    Errs=0
    for i in range(alct[alcttype].pwrchans):
        readval = ReadCurrentADC(i)
        current = readval * arCurrents[i].coef
        toler   = arCurrents[i].toler

        if alcttype==0:  # ALCT 288
            ref = arCurrents[i].ref288
        if alcttype==1:  # ALCT 384
            ref = arCurrents[i].ref384
        if alcttype==2:  # ALCT 672
            ref = arCurrents[i].ref672

        if abs(current-ref) > toler:
            Errs+=1
            print("\t Fail", end='')
        else:
            print("\t Pass ", end='')

        print("\t %s \tread=%.03f expect=%.03f +- %0.03f" % (arCurrents[i].ref, readval*arCurrents[i].coef, ref, arCurrents[i].toler))

    if Errs==0:
        print('\t ====> Passed')
        return(0)
    else:
        print('\t ====> Failed Current Test with %i Errors' % Errs)
        return(Errs)

# Checks temperature against reference (should be close to ambient)
def CheckTemperature():
    print('Checking Temperature')
    Errs=0
    readval = ReadTemperatureADC()
    temp = (readval * arTemperature.coef)-50
    if not (abs(temp-arTemperature.refval) < arTemperature.toler):
        Errs+=1
        print("\t Fail ", end='')
    else:
        print("\t Pass ", end='')
    print("Temperature read=%.03f expect=%.03f +- %0.03f" % (temp, arTemperature.refval, arTemperature.toler))

    if Errs==0:
        print('\t ====> Passed')
        return(0)
    else:
        print('\t ====> Failed')
        return(Errs)

def ReadAllThresholds():
    NUM_AFEB=24
    print("\n%s> Read All Thresholds" % common.Now())
    for j in range (NUM_AFEB):
        thresh = ReadThreshold(j)
        print("\t  AFEB #%02i:  Threshold=%.3fV (ADC=0x%03X)" % (j, (ADC_REF/1023)*thresh, thresh))

def WriteAllThresholds(thresh):
    print("\n%s> Write All Thresholds to %i" % (common.Now(), thresh))
    for i in range(NUM_AFEB):
        SetThreshold(i, thresh);
    print("\t  All thresholds set to %i" % thresh)

# Runs an automatic self-test of Slow Control Functions
# Should have _Normal_ ALCT Firmware Installed for Test
# Other firmwares will work but have different current/voltage requirements
def SelfTest(alcttype):
    Errs = 0
    alct.SetChain(SLOW_CTL)

    print("\n%s> Start Slow Control Self Test\n" % common.Now())
    logFile.write("\n%s> Start Slow Control Self Test\n" % common.Now())

    #--------------------------------------------------------------------------
    fail = CheckVoltages(alcttype)
    if (fail): 
        Errs += fail
        logFile.write("Fail: Voltages Check")
    else: 
        logFile.write("Pass: Voltages Check")

    #--------------------------------------------------------------------------
    fail = CheckCurrents(alcttype)
    if (fail):
        Errs += fail
        logFile.write("Fail: Currents Check")
    else: 
        logFile.write("Pass: Currents Check")

    #--------------------------------------------------------------------------
    fail = CheckTemperature()
    if (fail):
        Errs += fail
        logFile.write("Fail: Temperature Check")
    else: 
        logFile.write("Pass: Temperature Check")

    #--------------------------------------------------------------------------
    fail = CheckThresholds(alct[alcttype].groups*6,17)
    if (fail):
        Errs += fail
        logFile.write("Fail: Thresholds Check with %i Errors" % Fail)
    else: 
        logFile.write("Pass: Thresholds Check")

    #--------------------------------------------------------------------------
    fail = CheckStandbyRegister()
    if (fail):
        Errs += fail
        logFile.write("Fail: Standby Register Check with %i Errors" % Fail)
    else: 
        logFile.write("Pass: Standby Register Check")

    #--------------------------------------------------------------------------
    fail = CheckTestPulsePowerDown()
    if (fail):
        Errs += fail
        logFile.write("Fail: Test Pulse Power Down with %i Errors" % Fail)
    else: 
        logFile.write("Pass: Test Pulse Power Down")
        
    #--------------------------------------------------------------------------
    fail = CheckTestPulsePowerUp()
    if (fail):
        Errs += fail
        logFile.write("Fail: Test Pulse Power Up with %i Errors" % Fail)
    else: 
        logFile.write("Pass: Test Pulse Power Up")

    #--------------------------------------------------------------------------
    fail = CheckTestPulseWireGroupMask()
    if (fail):
        Errs += fail
        logFile.write("Fail: Test Pulse Wire Group Mask Failed with %i Errors" % Fail)
    else: 
        logFile.write("Pass: Test Pulse Wire Group Mask")

    #After finishing tests, turn off AFEBS to reduce power
    SetStandbyReg(0) #Turn Off All AFEBs

    if Errs>0:
        print('\nSlow Control Self Test Failed with %i Failed Subtests' % Errs)
    else:
        print('\nSlow Control Self Test Finished Without Errors')

    k=input("\n<cr> to return to menu: ")
    if not k: 
        return (Errs)

#------------------------------------------------------------------------------
# Subtest Menu
#------------------------------------------------------------------------------

def SubtestMenu(alcttype):
    channel=0
    while True:
        common.ClearScreen()
        print("\n================================================================================")
        print(  " Slow Control Test Submenu")
        print(  "================================================================================\n")
        print("\t 0 Slow Control Automatic Self Test")
        print("\t 1 Thresholds Linearity Full Scan")
        print("\t 2 Read Voltages")
        print("\t 3 Read Currents")
        print("\t 4 Read Temperature")

        k=input("\nChoose Test or <cr> to return to Main Menu: ")
        if not k: break
        test = int(k,10)
        common.ClearScreen()
        print("")

        if test==0:
            SelfTest(alcttype)
        if test==1:
            CheckThresholds(alct[alcttype].groups*alct[alcttype].chips,1)
        if test==2:
            CheckVoltages(alcttype)
        if test==3:
            CheckCurrents(alcttype)
        if test==4:
            CheckTemperature()

        k=input("\n<cr> to return to menu: ")
