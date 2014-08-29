#!/usr/bin/env python3

################################################################################
# Functions for testing the Slow Control Circuits
################################################################################

#-------------------------------------------------------------------------------
import jtaglib as jtag
import common
from common import MutableNamedTuple
import alct
#-------------------------------------------------------------------------------
import logging
logging.getLogger()
#-------------------------------------------------------------------------------
import time
import sys
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
# Slow Control JTAG Instruction OP-Codes
#-------------------------------------------------------------------------------


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

#-------------------------------------------------------------------------------
# Threshold Read/Write Stuff
#-------------------------------------------------------------------------------

ADC_REF = 1.225 # ADC Reference Voltage
ThreshToler = 4 # Threshold Tolerance (discrepancy is ok within +- ThreshToler)

arADCChannel = [ 1, 0, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0, 10,
                 9, 8,  7, 6, 5, 4, 3, 2, 1, 0, 0, 1, 2,  3,
                 4, 5,  6, 7, 8, 0, 1, 2, 3, 4, 5, 6, 7,  8 ]

arADCChip    = [ 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0,
                 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 3, 3, 3,
                 3, 3, 3, 3, 3, 4, 4, 4, 4, 4, 4, 4, 4, 4 ]

mapGroupMask = [ 0, 0, 0, 1, 1, 1, 2, 2, 2, 3, 3, 3, 0, 0,
                 0, 1, 1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 4, 5,
                 5, 5, 6, 6, 6, 4, 4, 4, 5, 5, 5, 6, 6, 6 ]

#-------------------------------------------------------------------------------
# Container for ADC Voltage Measurement
#-------------------------------------------------------------------------------
arVoltages = [ MutableNamedTuple() for i in range(4)]

arVoltages[0].ref       = '1.8v'
arVoltages[0].refval    = 1.8
arVoltages[0].coef      = 0.005878
arVoltages[0].toler     = 0.1

arVoltages[1].ref       = '3.3v'
arVoltages[1].refval    = 3.3
arVoltages[1].coef      = 0.005878
arVoltages[1].toler     = 0.2

arVoltages[2].ref       = '5.5v1'
arVoltages[2].refval    = 5.65
arVoltages[2].coef      = 0.005878
arVoltages[2].toler     = 0.2

arVoltages[3].ref       = '5.5v2'
arVoltages[3].refval    = 5.65
arVoltages[3].coef      = 0.005878
arVoltages[3].toler     = 0.2

#-------------------------------------------------------------------------------
# Container for ADC Current Measurement
#-------------------------------------------------------------------------------
arCurrents = [ MutableNamedTuple() for i in range(4)]

arCurrents[0].ref       = '1.8v'
arCurrents[0].ref288    = 0.667
arCurrents[0].ref384    = 0.667 # double check this
arCurrents[0].ref672    = 0.667 # double check this
arCurrents[0].coef      = 0.002987
arCurrents[0].toler     = 0.1

arCurrents[1].ref       = '3.3v'
arCurrents[1].ref288    = 1.20
arCurrents[1].ref384    = 1.20 # double check this
arCurrents[1].ref672    = 1.20 # double check this
arCurrents[1].coef      = 0.002987
arCurrents[1].toler     = 0.2

arCurrents[2].ref       = '5.5v1'
arCurrents[2].ref288    = 0.15
arCurrents[2].ref384    = 0.15 # double check this
arCurrents[2].ref672    = 0.15 # double check this
arCurrents[2].coef      = 0.002987
arCurrents[2].toler     = 0.10

arCurrents[3].ref       = '5.5v2'
arCurrents[3].ref288    = 0.10
arCurrents[3].ref384    = 0.10  # double check this
arCurrents[3].ref672    = 0.10  # double check this
arCurrents[3].coef      = 0.002987
arCurrents[3].toler     = 0.10

#-------------------------------------------------------------------------------
# Container for ADC Temperature Measurement
#-------------------------------------------------------------------------------
arTemperature           = MutableNamedTuple()

arTemperature.ref       = 'On Board Temperature'
arTemperature.refval    = 25.0
arTemperature.coef      = 0.1197
arTemperature.toler     = 5.0
#------------------------------------------------------------------------------
# Slow Control Control
#------------------------------------------------------------------------------
def WriteRegister(reg, value): 
    length = RegSz[reg]             # length of register
    mask   = 2**(length)-1          # Bitmask of 1s to mask the register
    jtag.WriteIR(reg, alct.SC_IR)             
    return(jtag.WriteDR(value & mask,length))

def ReadRegister(reg): 
    jtag.WriteIR(reg, alct.SC_IR)
    result = jtag.ReadDR(0x0,RegSz[reg])
    return (result)



#------------------------------------------------------------------------------
# Slow-Control Control Functions
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
# Sets standby register. Logic 0 shuts down the AFEB power regulator for the
# selected boards. Register bits are mapped one-to-one with AFEB cards

def SetStandbyReg(value):
    alct.SetChain(alct.SLOW_CTL)
    return (WriteRegister(WSbr,value))

def ReadStandbyReg():
    alct.SetChain(alct.SLOW_CTL)
    return (ReadRegister(RSbr)) 

def SetStandbyForChan(chan, onoff):
    if (chan >= 0) and (chan < 42):
        value = ReadGroupStandbyReg(chan // 6) & 0x3F
        value = (value ^ (((value >> (chan % 6)) & 0x1 ) << (chan % 6) )) | (int(onoff) << (chan % 6))
        SetGroupStandbyReg(chan // 6, value)

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
    alct.SetChain(alct.SLOW_CTL)
    wgroups = 7
    data    = ReadStandbyReg()
    if (group >=0) and (group < wgroups):
        return((data >> (group*6)) & 0x3F)
    else:
        print("Problem with Reading Group Standby Reg")

#------------------------------------------------------------------------------

# Logic 0 shuts down test pulse generator, Logic 1 turns it on
def SetTestPulsePower(sendval):
    return(WriteRegister(WTpd,sendval))

def ReadTestPulsePower():
    return (ReadRegister(RTpd))

# This 8-bit DAC controls the amplitude of the Analog Test Pulse sent to the
# AFEBs. 1 LSB = 1.225V/256 = 4.7mV, and V(n)=1.225V*n/256, where n=0..255 
def SetTestPulsePowerAmp(value):
    #temp = 0
    #for i in range(0,len-1):
    #    temp = temp | (((value >> i) & 0x1) << (7-i))
    WriteRegister(WTp,value)

# Stores the bits tp_group[] to specify which groups are enabled for the Analog
# Test Pulse, which is initiated either by an external TTl signal or by a command
# to the Virte Chip. Individual AFEBs cannot be selected to receive the test
# pulse, but instead are arranged in groups of 6
def SetTestPulseWireGroupMask(value):
    WriteRegister(WTpg,value)

def ReadTestPulseWireGroupMask():
    return(ReadRegister(RTpg))


# Stores the bits tp_strip[] to specify which CSC anode strips are enabled for
# the analog test pulse. The register bits are mapped one-to-one with the
# pulse-strips. 

def SetTestPulseStripLayerMask(value):
    WriteRegister(WTps,value)

def ReadTestPulseStripLayerMask():
    WriteRegister(RTps,value)

#------------------------------------------------------------------------------

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

    jtag.WriteIR(0xFF & (0x8+(realch // 12)), alct.SC_IR)
    jtag.WriteDR(data & 0xFFF, DRlength)

# Returns AFEB Threshold on channel ch
# Returns value in ADC Counts (0-1023)
def ReadThreshold(ch):
    alct.SetChain(alct.SLOW_CTL)
    DRLength = 11
    result = 0
    adr = 0

    channel = 0xFF & arADCChannel[ch]
    chip    = 0xFF & (0x10 + arADCChip[ch])


    for i in range(4):
        adr = 0xFFF & (adr | (((channel >> i) & 0x1) << (3-i)))

    time.sleep(0.01)     #sleep 10 ms

    jtag.WriteIR(chip, alct.SC_IR)
    jtag.WriteDR(adr,  DRLength)

    #time.sleep(0.1)     #sleep 10 ms

    jtag.WriteIR(chip, alct.SC_IR)
    read = jtag.ReadDR(adr,DRLength)

    result=common.FlipDR(read,DRLength)

    return(result)

def ReadAllThresholds(alcttype):
    NUM_AFEB = alct.alct[alcttype].chips
    print("\n%s> Read All Thresholds" % common.Now())
    for j in range (NUM_AFEB):
        thresh = ReadThreshold(j)
        print("\t  AFEB #%02i:  Threshold=%.3fV (ADC=0x%03X)" % (j, (ADC_REF/1023)*thresh, thresh))

def WriteAllThresholds(thresh,alcttype): 
    NUM_AFEB = alct.alct[alcttype].chips
    print("\n%s> Write All Thresholds to %i" % (common.Now(), thresh))
    for i in range(NUM_AFEB):
        SetThreshold(i, thresh);
    print("\t  All thresholds set to %i" % thresh)

#------------------------------------------------------------------------------
# Read ALCT board 12 bit voltage monitoring
# Returns value in ADC counts (0-1023)
def ReadVoltageADC(chan):
    alct.SetChain(alct.SLOW_CTL)
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
        jtag.WriteIR(0x12, alct.SC_IR)
        read = jtag.ReadDR(adr, DRlength)

    # Flip Bits (change endianess)
    return(common.FlipDR(read,DRlength))

# Read ALCT board 12 bit current monitoring
# Returns value in ADC counts (0-1023)
def ReadCurrentADC(chan):
    alct.SetChain(alct.SLOW_CTL)
    DRlength = 11
    adr = 0

    for i in range(4):
        adr = adr | ((((chan+2) >> i) & 0x1) << (3-i))

    for i in range(0,3):
        jtag.WriteIR(0x12, alct.SC_IR)
        read = jtag.ReadDR(adr, DRlength)

    return (common.FlipDR(read,DRlength))

# Read on board temperature sensor
# Returns value in ADC counts (0-1023)
def ReadTemperatureADC():
    DRlength = 11
    for i in range(3):
        jtag.WriteIR(0x12, alct.SC_IR)
        read = jtag.ReadDR(0x5, DRlength)

    return (common.FlipDR(read,DRlength))

# Read on board temperature sensor
# Returns value in degrees C
def ReadTemperature():
    return (ReadTemperatureADC()*arTemperature.coef-50)

#------------------------------------------------------------------------------
# Slow-Control Test Functions
#------------------------------------------------------------------------------

# Checks All board Thresholds
# Optional depth argument allows for a quick scan
# Only the modulo of the depth will be checked
# e.g. depth=1 checks all thresholds
#      depth=17 will check 0,17,34,...etc
def CheckThresholds(first, last, depth=1):
    print("Checking AFEB Thresholds")
    ErrMatrix = [0]*(42)

    Errs=0
    if (first==last): last+=1
    for afeb in range(first, last):
        afebErrs = 0
        print("\t Testing AFEB #%2i" % afeb)
        for thresh in range(256):
            if thresh%depth == 0:
                write=thresh
                SetThreshold(afeb,write)
                read = ReadThreshold(afeb)/4.0
                if abs(write - read) > ThreshToler:
                    print("\t\t ERROR: Write=%3i Read=%3.0f" % (write,read) )
                    afebErrs +=1
        Errs+=afebErrs
        ErrMatrix[afeb]=afebErrs

    logging.info ("\t Summary: ")
    for afeb in range(first, last):
        if (ErrMatrix[afeb] > 0): 
            logging.info("\t\t FAIL: AFEB #%2i with %i Errors" % (afeb, ErrMatrix[afeb]))
        else:
            logging.info("\t\t PASS: AFEB #%2i" %(afeb))

    if Errs==0:
        print        ('\t\t PASS: Thresholds Linearity Test')
        logging.info ('\t\t PASS: Thresholds Linearity Test')
        return(0)
    else:
        print        ('\t\t FAIL: Thresholds Test with %i Total Errors' % Errs)
        logging.info ('\t\t FAIL: Thresholds Test with %i Total Errors' % Errs)
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
    sendval = 1
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
    for i in range(alct.alct[alcttype].pwrchans):
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
    for i in range(alct.alct[alcttype].pwrchans):
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
        print        ('\t PASS: Currents Check')
        logging.info ("\t FAIL: Currents Check")
        return(0)
    else:
        print        ('\t FAIL: Current Test with %i Errors' % Errs)
        logging.info ('\t FAIL: Current Test with %i Errors' % Errs)
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

# Runs an automatic self-test of Slow Control Functions
# Should have _Normal_ ALCT Firmware Installed for Test
# Other firmwares will work but have different current/voltage requirements
def SelfTest(alcttype):
    Errs = 0
    alct.SetChain(alct.SLOW_CTL)

    print("\nSlow Control Self Test\n")
    print("Make sure NORMAL firmware is loaded (alct{288,384,672}.mcs)")
    print("Make sure Tester Board is Disconnected")
    print("Make sure Clock Source jumper is set to position 1/2")
    while True: 
        k = input("\t <cr> to continue")
        if not k: break

    logging.info("\nSlow Control Self Test:")

    #--------------------------------------------------------------------------
    fail = CheckVoltages(alcttype)
    if (fail): 
        Errs += fail
        logging.info("\t FAIL: Voltages Check")
    else: 
        logging.info("\t PASS: Voltages Check")

    #-Check Currents-----------------------------------------------------------
    fail = CheckCurrents(alcttype)
    Errs += fail

    #-Check On-board Temperature-----------------------------------------------
    fail = CheckTemperature()
    if (fail):
        Errs += fail
        logging.info("\t FAIL: Temperature Check")
    else: 
        logging.info("\t PASS: Temperature Check")

    #--------------------------------------------------------------------------
    fail = CheckThresholds(0,alct.alct[alcttype].groups*6,17)
    if (fail):
        Errs += fail

    #--------------------------------------------------------------------------
    fail = CheckStandbyRegister()
    if (fail):
        Errs += fail
        logging.info("\t FAIL: Standby Register Check with %i Errors" % fail)
    else: 
        logging.info("\t PASS: Standby Register Check")

    #--------------------------------------------------------------------------
    fail = CheckTestPulsePowerDown()
    if (fail):
        Errs += fail
        logging.info("\t FAIL: Test Pulse Power Down with %i Errors" % fail)
    else: 
        logging.info("\t PASS: Test Pulse Power Down")
        
    #--------------------------------------------------------------------------
    fail = CheckTestPulsePowerUp()
    if (fail):
        Errs += fail
        logging.info("\t FAIL: Test Pulse Power Up with %i Errors" % fail)
    else:                    
        logging.info("\t PASS: Test Pulse Power Up")

    #--------------------------------------------------------------------------
    fail = CheckTestPulseWireGroupMask()
    if (fail):
        Errs += fail
        logging.info("\t FAIL: Test Pulse Wire Group Mask Failed with %i Errors" % fail)
    else: 
        logging.info("\t PASS: Test Pulse Wire Group Mask")

    #After finishing tests, turn off AFEBS to reduce power
    SetStandbyReg(0) #Turn Off All AFEBs

    if Errs>0:
        print('\nSlow Control Self Test Failed with %i Errors' % Errs)
    else:
        print('\nSlow Control Self Test Passed Without Errors')

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
        print("\t 1 Thresholds Linearity Test")
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
            while True: 
                k=input("\nEnter channel to test (0-23), or <q> for a quick scan, or <cr> for a Full Scan (slow)")
                if (not k): 
                    CheckThresholds(0,alct.alct[alcttype].chips,1)
                    break
                elif (k=="q"): 
                    CheckThresholds(0,alct.alct[alcttype].chips,17)
                    break
                elif (int(k) >=0 and int(k) < 24): 
                    CheckThresholds(int(k),int(k),1)
                    break
                else: 
                    print("Invalid choice!")
        if test==2:
            CheckVoltages(alcttype)
        if test==3:
            CheckCurrents(alcttype)
        if test==4:
            CheckTemperature()

        k=input("\n<cr> to return to menu: ")


#Read virtex id codes:
#Program Script;
#Begin
#// === Set Virtex Programming Chain
#	SetChain(2);
#
#// Read Virtex ID Code
#	WriteIR('09FFFF',21);
#	ReadDR('0',32);
#
#// Read EPROM #1 ID Code
#	WriteIR('1FFFFE',21);
#	ReadDR('0',32);
#
#// Read EPROM #2 ID Code 
#	WriteIR('1FFEFF',21); 
#	ReadDR('0',32); 
#
#// === Set Slow Control Control Chain
#	SetChain(1);
#
#// Read Slow Control Spartan User ID Code
#	WriteIR('0',6);
#	ReadDR('0',40);
#End.


