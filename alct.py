#!/usr/bin/env python3

# ------------------------------------------------------------------------------
# ALCT.py
# Generic Tools for ALCT I/O, Register Definitions, Baseboard Properties
# ------------------------------------------------------------------------------

import jtaglib as jtag
import time
import sys
from common import MutableNamedTuple

# ------------------------------------------------------------------------------

VIRTEX600       = 0x00 # Mezzanine Detection Virtex 600 Code
VIRTEX1000      = 0x01 # Mezzanine Detection Virtex 1000 Code
UNKNOWN         = 0xFF # Mezzanine Detection Unknown ID Code

# ------------------------------------------------------------------------------
# Mezzanine Control Addresses
# ------------------------------------------------------------------------------

IDRead          = 0x00 # ID Read Address
HCMaskRead      = 0x01
HCMaskWrite     = 0x02
RdTrig          = 0x03
WrTrig          = 0x04
RdCfg           = 0x06 # read control register
WrCfg           = 0x07 # write control register
Wdly            = 0x0D # write delay lines. cs_dly bits in Par
Rdly            = 0x0E # read  delay lines. cs_dly bits in Par
CollMaskRead    = 0x13
CollMaskWrite   = 0x14
ParamRegRead    = 0x15
DelayCtrlRead   = 0x15
ParamRegWrite   = 0x16
DelayCtrlWrite  = 0x16
InputEnable     = 0x17
InputDisable    = 0x18
YRwrite         = 0x19
OSread          = 0x1A
SNRead          = 0x1B
SNwrite0        = 0x1C
SNwrite1        = 0x1D
SNreset         = 0x1E
Bypass          = 0x1F

#-------------------------------------------------------------------------------
# Array of the Sizes of Virtex Register Locations
# Used by WriteRegister and ReadRegister
#-------------------------------------------------------------------------------

RegSz = {
    0x00:  40,  # IDRead        // read ID register
    0x01: 384,  # HCMaskRead    // Read Hot Channel Mask  (LENGTH=288,384,672)
    0x02: 384,  # HCMaskWrite   // Write Hot Channel Mask (LENGTH=288,384,672)
    0x03:   2,  # RdTrig        // Read Trigger Register
    0x04:   2,  # WrTrig        // Write Trigger Register
    0x06:  69,  # RdCfg         // read control register
    0x07:  69,  # WrCfg         // write control register
    0x0D: 120,  # Wdly          // write delay lines. cs_dly bits in Par
    0x0E: 120,  # Rdly          // read  delay lines. cs_dly bits in Par
    0x10:  31,  # YRread        // Extended Config Register Read
    0x13: 224,  # CollMaskRead  // Read Collision Mask Register (LENGTH=112,168,224,336,392)
    0x14: 224,  # CollMaskWrite // Write Collision Mask Register (LENGTH=112,168,224,336,392)
    0x15:   6,  # DelayCtrlRead  // Delay line control register read (LENGTH=5,5,6,9,9)
    0x16:   6,  # DelayCtrlWrite // Delay line control register write (LENGTH=5,5,6,9,9)
    0x17:   0,  # InputEnable   // JTAG instruction to Enable Input Register Clock (for debugging)
    0x18:   0,  # InputDisable  // JTAG Instruction to Disable input Register Clock (for debugging)
    0x19:  31,  # YRwrite       // Extended Config Register Write
    0x1A:  49,  # OSread        // Output FIFO read (for debugging via JTAG) LENGTH=49,49,49,51,51
    0x1B:   1,  # SNread        //
    0x1F:   1}  # Bypass        // Bypass Register

#-------------------------------------------------------------------------------
# ID Masks and ID Codes
#-------------------------------------------------------------------------------

SC_EPROM_ID        = 0X0005024093
SC_EPROM_ID_MASK   = 0X01FFFFFFFF

SC_FPGA_ID         = 0X0000838126
SC_FPGA_ID_MASK    = 0X01FFFFFFFF

V_EPROM1_ID_MASK   = 0X003FFFFFFF
V_EPROM1_ID        = 0X000A04C126
V_EPROM1_ID2       = 0X000A06C126

V_EPROM2_ID_MASK   = 0X003FFFFFFF
V_EPROM2_ID        = 0X0005026093
V_EPROM2_ID2       = 0X0005036093

V1000E_ID          = 0X000290024C
V1000E_ID_MASK     = 0X003FFFFFFF

V600E_ID           = 0X0001460126
V600E_ID_MASK      = 0X000FFFFFFF

SC_IR_SIZE         = 11
SC_ID_DR_SIZE      = 33
V1000_IR_SIZE      = 21
V600_IR_SIZE       = 13
V_ID_DR_SIZE       = 34

CTRL_SC_FPGA_ID    = 0x09072001B8
CTRL_SC_ID_DR_SIZE = 40

USER_V_FPGA_ID     = 0x0925200207
USER_V_ID_DR_SIZE  = 40

#-------------------------------------------------------------------------------
# Board Parameters (unused)
#-------------------------------------------------------------------------------

#MAX_DELAY_GROUPS            = 7
#MAX_DELAY_CHIPS_IN_GROUP    = 6
#MAX_NUM_AFEB                = 42


#-------------------------------------------------------------------------------
# ALCTTYPE Definitions
#-------------------------------------------------------------------------------
ALCT288 = 0 # ALCT 288 Channels
ALCT384 = 1 # ALCT 384 Channels
ALCT672 = 2 # ALCT 672 Channels


#-------------------------------------------------------------------------------
# Power Supply Enumeration
#-------------------------------------------------------------------------------
V18_PWR_SPLY   = 0        # Power Supply 1.8V
V33_PWR_SPLY   = 1        # Power Supply 3.3V
V55_1_PWR_SPLY = 2        # Power Supply 5.5V (1)
V55_2_PWR_SPLY = 3        # Power Supply 5.5V (2)

#-------------------------------------------------------------------------------
# Array of Tuples to hold Properties of Different Board Types
#-------------------------------------------------------------------------------
alct = [ MutableNamedTuple() for i in range(3)]

#ALCT288 = 0
alct[0].name          = 'ALCT288'   # Name
alct[0].channels      = 288         # Number of channels on board
alct[0].groups        = 3           # Number of Delay Chip Groups
alct[0].chips         = 18           # Number of Delay Chips per Group
alct[0].delaylines    = 16          # Number of Channels Per Delay Chip
alct[0].pwrchans      = 3           # Number of Power Inputs

#ALCT288 = 1
alct[1].name          = 'ALCT384'
alct[1].channels      = 384
alct[1].groups        = 4
alct[1].chips         = 24
alct[1].delaylines    = 16
alct[1].pwrchans      = 4

#ALCT288 = 2
alct[2].name          = 'ALCT672'
alct[2].channels      = 672
alct[2].groups        = 7
alct[2].chips         = 42
alct[2].delaylines    = 16
alct[2].pwrchans      = 4

#-------------------------------------------------------------------------------
# CHAMBER Definitions
# Unused at the moment... consider to remove..
#-------------------------------------------------------------------------------
ME1_1 = 0 # ME1/1
ME1_2 = 1 # ME1/2
ME1_3 = 2 # ME1/3
ME2_1 = 3 # ME2/1
ME2_2 = 4 # ME2/2
ME3_1 = 5 # ME3/1
ME3_2 = 6 # ME3/2
ME4_1 = 7 # ME4/1
ME4_2 = 8 # ME4/2

#-------------------------------------------------------------------------------
# Array of Tuples to hold properties of Different Chamber Types
# Unused at the moment... consider to remove..
#-------------------------------------------------------------------------------
chamb_table = [ MutableNamedTuple() for i in range(9)]

chamb_table[0].name         = 'ME1/1'
chamb_table[0].chmbtype     = ME1_1
chamb_table[0].alct         = ALCT288
chamb_table[0].wires        = 288
chamb_table[0].afebs_on551  = 18
chamb_table[0].afebs_on552  = 0

chamb_table[1].name         = 'ME1/2'
chamb_table[1].chmbtype     = ME1_2
chamb_table[1].alct         = ALCT384
chamb_table[1].wires        = 384
chamb_table[1].afebs_on551  = 12
chamb_table[1].afebs_on552  = 12

chamb_table[2].name         = 'ME1/3'
chamb_table[2].chmbtype     = ME1_3
chamb_table[2].alct         = ALCT288
chamb_table[2].wires        = 192
chamb_table[2].afebs_on551  = 12
chamb_table[2].afebs_on552  = 0

chamb_table[3].name         = 'ME2/1'
chamb_table[3].chmbtype     = ME2_1
chamb_table[3].alct         = ALCT672
chamb_table[3].wires        = 672
chamb_table[3].afebs_on551  = 18
chamb_table[3].afebs_on552  = 24

chamb_table[4].name         = 'ME2/2'
chamb_table[4].chmbtype     = ME2_2
chamb_table[4].alct         = ALCT384
chamb_table[4].wires        = 384
chamb_table[4].afebs_on551  = 12
chamb_table[4].afebs_on552  = 12

chamb_table[5].name         = 'ME3/1'
chamb_table[5].chmbtype     = ME3_1
chamb_table[5].alct         = ALCT672
chamb_table[5].wires        = 576
chamb_table[5].afebs_on551  = 12
chamb_table[5].afebs_on552  = 24

chamb_table[6].name         = 'ME3/2'
chamb_table[6].chmbtype     = ME3_2
chamb_table[6].alct         = ALCT384
chamb_table[6].wires        = 384
chamb_table[6].afebs_on551  = 12
chamb_table[6].afebs_on552  = 12

chamb_table[7].name         = 'ME4/1'
chamb_table[7].chmbtype     = ME4_1
chamb_table[7].alct         = ALCT672
chamb_table[7].wires        = 576
chamb_table[7].afebs_on551  = 12
chamb_table[7].afebs_on552  = 24

chamb_table[8].name         = 'ME4/2'
chamb_table[8].chmbtype     = ME4_2
chamb_table[8].alct         = ALCT384
chamb_table[8].wires        = 384
chamb_table[8].afebs_on551  = 12
chamb_table[8].afebs_on552  = 12

#------------------------------------------------------------------------------
# JTAG Instruction Registers
#-------------------------------------------------------------------------------
SLOW_CTL        = 0x0
FAST_CTL        = 0x1
BOARD_SN        = 0x2
MEZAN_SN        = 0x3
VRTX_CH	        = 0x3
V_IR            = 0x5
SC_IR           = 0x6

#------------------------------------------------------------------------------
# JTAG Chains
#-------------------------------------------------------------------------------
SLOWCTL_CONTROL = 0x0 # Slow Control Control
SLOWCTL_PROGRAM = 0x1 # Slow Control Programming
VIRTEX_CONTROL  = 0x4 # Virtex Control
VIRTEX_PROGRAM  = 0x5 # Virtex Programming

# TODO:
# Array of JTAG Chains... legacy of old code
# Still used in some places but hope to remove
# OK I think its all done
# arJTAGChains = [SLOWCTL_PROGRAM, SLOWCTL_CONTROL, VIRTEX_PROGRAM, VIRTEX_CONTROL]

# Select JTAG Programming Chain
def SetChain(ch):
    jtag.set_chain(ch)

#------------------------------------------------------------------------------
# Virtex Control
#------------------------------------------------------------------------------

# Write Virtex Register
def WriteRegister(reg, value, length=-1):
    if (length==-1):
        # These Registers should NOT be written automatically since their size is board dependent
        if (reg == 0x01 or reg == 0x02 or reg == 0x13 or reg == 0x14 or reg == 0x15 or reg == 0x16 or reg==0x16 or reg == 0x1A):
            print ("Very naughty call to Write Register...")
            sys.exit()

        length = RegSz[reg]     # length of register
    else:
        length = length

    mask   = 2**(length)-1  # Bitmask of 1s to mask the register
    jtag.WriteIR(reg, V_IR)
    return(jtag.WriteDR(value & mask, length))

# Read Virtex Register
def ReadRegister(reg, length=-1):
    if (length==-1):
        # These Registers should NOT be written automatically since their size is board dependent
        if (reg == 0x01 or reg == 0x02 or reg == 0x13 or reg == 0x14 or reg == 0x15 or reg == 0x16 or reg==0x16 or reg == 0x1A):
            print ("Very naughty call to Write Register...")
            sys.exit()

        length = RegSz[reg]     # length of register
    else:
        length = length

    jtag.WriteIR(reg, V_IR)
    result = jtag.ReadDR(0x0,length)
    return(result)

#------------------------------------------------------------------------------
# S/N Readout
#------------------------------------------------------------------------------

alct_idreg  = MutableNamedTuple()   #ALCT ID Register
sc_idreg    = MutableNamedTuple()   #Slow Control ID Register
v_idreg     = MutableNamedTuple()

#------------------------------------------------------------------------------

# Read Slow Control or Mezzanine FIRMWARE FPGA ID Codes
def ReadIDCode (alct_ctl):
    if (alct_ctl == SLOW_CTL):
        SetChain(SLOW_CTL) # Slow Control Control Chain
        jtag.WriteIR(0, SC_IR)
        return(jtag.ReadDR(0x00, CTRL_SC_ID_DR_SIZE))
    elif (alct_ctl == FAST_CTL):
        SetChain(4) # Virtex Control Chain
        jtag.WriteIR(0, V_IR)
        return(jtag.ReadDR(0x00, USER_V_ID_DR_SIZE))
    else:
        return(0)

# Read Board Silicon Serial Numbers
def ReadBoardSN(board_type):
    SetChain(4) # Virtex Control Chain

    if board_type == BOARD_SN:
        cr_str    = ReadRegister(RdCfg)
        cr_str    = cr_str & 0X0FFFFFFFFFFFFFFFFF

        #cr_str[1] = 0
        #cr_str = '0020A03806B1193FC1'

        WriteRegister(WrCfg, cr_str)
    elif board_type == MEZAN_SN:
        cr_str = ReadRegister(RdCfg)
        cr_str = cr_str | 0x100000000000000000
        #cr_str[1] = '1'
        #cr_str = '1020A03806B1193FC1'
        WriteRegister(WrCfg, cr_str)
    else:
        return(0)

    # reset DS2401
    jtag.WriteIR (SNreset, V_IR)
    time.sleep(0.001)
    jtag.WriteIR (SNwrite1, V_IR)
    time.sleep(0.050)

    # write read command 0x33
    jtag.WriteIR (SNwrite1, V_IR)
    time.sleep(0.001)
    jtag.WriteIR (SNwrite1, V_IR)
    time.sleep(0.001)
    jtag.WriteIR (SNwrite0, V_IR)
    time.sleep(0.001)
    jtag.WriteIR (SNwrite0, V_IR)
    time.sleep(0.001)
    jtag.WriteIR (SNwrite1, V_IR)
    time.sleep(0.001)
    jtag.WriteIR (SNwrite1, V_IR)
    time.sleep(0.001)
    jtag.WriteIR (SNwrite0, V_IR)
    time.sleep(0.001)
    jtag.WriteIR (SNwrite0, V_IR)
    time.sleep(0.001)

    #read 64 bits of SN bit by bit
    result=0
    for i in range(64):
        jtag.WriteIR(SNRead,V_IR)
        bit = jtag.ReadDR(0,1) & 0x1
        result = result | bit << i
    return(result)

# Generates tuple from idcode
def StrToIDCode(idstr):
    id = alct_idreg()
    if (len(idstr) <= 64):
        id.chip     = 0xF    & (idcode)
        id.version  = 0xF    & (idcode >> 4)
        id.year     = 0xFFFF & (idcode >> 8)
        id.day      = 0xFF   & (idcode >> 24)
        id.month    = 0xFF   & (idcode >> 32)
    return(id)

#------------------------------------------------------------------------------
# Mezzanine Utilities
#------------------------------------------------------------------------------

def SCReadEPROMID():
    jtag.WriteIR(0x7F0,11)
    time.sleep(0.1)     #time.sleep 100 ms
    jtag.WriteIR(0x7FF,11)
    jtag.WriteIR(0x7FE,11)
    result = jtag.ReadDR(0xffffffff,33)
    jtag.WriteIR(0x7FF,11)
    return (result)

def SCReadFPGAID():
    jtag.WriteIR(0x7F0,11)
    time.sleep(0.1)     #time.sleep 100 ms
    jtag.WriteIR(0x7FF,11)
    jtag.WriteIR(0x6FF,11)
    result = jtag.ReadDR(0x1fffffffe,33)
    jtag.WriteIR(0x7FF,11)
    return(result)

def SCEraseEPROM():
    if (SCReadEPROMID & SC_EPROM_ID_MASK) == SC_EPROM_ID :
        jtag.WriteIR(0x7E8, 11)
        jtag.WriteDR(0x04,   7)
        jtag.WriteIR(0x7EB, 11)
        jtag.WriteDR(0x001, 17)
        jtag.WriteIR(0x7EC, 11)

        time.sleep(0.2)     #sleep 200 ms
        jtag.WriteIR(0x7F0, 11)

        time.sleep(0.1)     #sleep 100 ms
        jtag.WriteIR(0x7FF, 11)
        jtag.WriteDR(0x0,    2)
        return(True)
    else:
        return(False)

def SCBlankCheckEPROM(errs):
    length = 16385
    blocks = 64

    if	(SCReadEPROMID & SC_EPROM_ID_MASK) == SC_EPROM_ID:
        jtag.WriteIR(0x7E8,11)
        jtag.WriteDR(0x34,7)
        jtag.WriteIR(0x7E5,11)
        time.sleep(0.1)     #time.sleep 100 ms
        errs = 0
        for i in range(0,blocks):
            jtag.StartDRShift()
            pmax = length//32
            for p in range(pmax):
                data = 0
                if (length-32*p) > 32:
                    data = jtag.ShiftData(0xFFFFFFFF, 32, False)
                    if data == 0xFFFFFFFF :
                        errs += 1
                else:
                    data = jtag.ShiftData(0xFFFFFFFF, length - 32*p, True)
                    if data == (0xFFFFFFFF >> (32-(length - 32*p))):
                        errs += 1
            jtag.ExitDRShift()
            if (errs > 0):
                break
        jtag.WriteIR(0x7F0,11)
        time.sleep(0.1)     #time.sleep 100 ms
        jtag.WriteIR(0x7FF,11)
        jtag.WriteIR(0x7F0,11)
        time.sleep(0.1)     #time.sleep 100 ms
        jtag.WriteIR(0x7FF,11)
        jtag.WriteIR(0x7F0,11)
        time.sleep(0.1)     #time.sleep 100 ms
        jtag.WriteIR(0x7FF,11)
        if (errs == 0):
            result = True
    else:
        result = False

def VReadFPGAID():
    jtag.WriteIR(0x1F,5)
    jtag.WriteIR(0x1F,5)
    jtag.WriteIR(0x9,5)
    result = jtag.ReadDR(0xFFFFFFFF,34)
    jtag.WriteIR(0x1F,5)
    return(result)

def VReadEPROMID1():
    jtag.WriteIR(0x1FF0,13)
    time.sleep(0.1)     #time.sleep 100 ms
    jtag.WriteIR(0x1FFF,13)
    jtag.WriteIR(0x1FFF,13)
    jtag.WriteIR(0x1FFE,13)
    result = jtag.ReadDR(0xffffffff,34)
    jtag.WriteIR(0x1FFF,13)
    return(result)

def VReadEPROMID2():
    jtag.WriteIR(0x1FFFF0,21)
    time.sleep(0.1)     #time.sleep 100 ms
    jtag.WriteIR(0x1FFFFF,21)
    jtag.WriteIR(0x1FFFFE,21)
    result = jtag.ReadDR(0xffffffff,34)
    jtag.WriteIR(0x1FFFFFF,21)
    return(result)

def VEraseEPROM1():
    if  ((VReadEPROMID1 & V_EPROM1_ID_MASK) == V_EPROM1_ID) or  \
        ((VReadEPROMID1 & V_EPROM1_ID_MASK) == V_EPROM1_ID2):
        jtag.WriteIR(0x1FE8,13)
        jtag.WriteDR(0x8,8)
        jtag.WriteIR(0x1FEB,13)
        jtag.WriteDR(0x2,18)
        jtag.WriteIR(0x1FEC,13)
        time.sleep(0.2)     #time.sleep 200 ms
        jtag.WriteIR(0x1FF0,13)
        time.sleep(0.1)     #time.sleep 100 ms
        jtag.WriteIR(0x1FFF,13)
        result = True
    else:
        result = False
    return(result)

def VEraseEPROM2():
    if  ((VReadEPROMID2 & V_EPROM2_ID_MASK) == V_EPROM2_ID) or \
        ((VReadEPROMID2 & V_EPROM2_ID_MASK) == V_EPROM2_ID2):
        jtag.WriteIR(0x1FFFE8,21)
        jtag.WriteDR(0x4,8)
        jtag.WriteIR(0x1FFFEB,21)
        jtag.WriteDR(0x1,18)
        jtag.WriteIR(0x1FFFEC,21)
        time.sleep(0.2)     #time.sleep 200 ms
        jtag.WriteIR(0x1FFFF0,21)
        time.sleep(0.1)     #time.sleep 100 ms
        jtag.WriteIR(0x1FFFFF,21)
        return(True)
    else:
        return(False)

def V600EraseEPROM():
    if  ((VReadEPROMID1 & V_EPROM2_ID_MASK) == V_EPROM2_ID) or \
        ((VReadEPROMID1 & V_EPROM2_ID_MASK) == V_EPROM2_ID2) :
        jtag.WriteIR(0x1FE8,13)
        jtag.WriteDR(0x8,8)
        jtag.WriteIR(0x1FEB,13)
        jtag.WriteDR(0x2,18)
        jtag.WriteIR(0x1FEC,13)
        time.sleep(0.2)     #time.sleep 200 ms
        jtag.WriteIR(0x1FF0,13)
        time.sleep(0.1)     #time.sleep 100 ms
        jtag.WriteIR(0x1FFF,13)
        return(True)
    else:
        return(False)
    return(result)

def VBlankCheckEPROM1(errs):
    length = 8192
    blocks = 512
    result=False

    if  ((VReadEPROMID1 & V_EPROM1_ID_MASK) == V_EPROM1_ID) or \
        ((VReadEPROMID1 & V_EPROM1_ID_MASK) == V_EPROM1_ID2):
        jtag.WriteIR(0x1FE8,13)
        jtag.WriteDR(0x34,7)
        jtag.WriteIR(0x1FF0,13)
        time.sleep(0.1)     #time.sleep 100 ms
        jtag.WriteIR(0x1FE8,13)
        jtag.WriteDR(0x34,7)
        jtag.WriteIR(0x1FEB,13)
        jtag.WriteDR(0x0,17)
        errs = 0

        for i in range(0,blocks):
            jtag.WriteIR(0x1FEF,13)
            time.sleep(0.1)     #time.sleep 100 ms
            jtag.StartDRShift()
            for p in range(0,(length)//32):
                data = 0
                if ( (length-32*p) > 32):
                    data = jtag.ShiftData(0xFFFFFFFF, 32, False)
                    if (data == 0xFFFFFFFF):
                        errs += 1
                else:
                    data = jtag.ShiftData(0xFFFFFFFF, length - 32*p, True)
                    if data == (0xFFFFFFFF >> (32-(length - 32*p))):
                        errs += 1
            jtag.ExitDRShift()
            if (errs > 0) :
                break

        jtag.WriteIR(0x1FF0,13)
        time.sleep(0.1)     #time.sleep 100 ms
        jtag.WriteIR(0x1FFF,13)
        jtag.WriteIR(0x1FFF,13)
        jtag.WriteDR(0x0,2)

        if (errs == 0):
            result = True
        else:
            result = errs

    return(result)

def VBlankCheckEPROM2(errs):
    return(0)
    #PLACEHOLDER

def V600BlankCheckEPROM(errs):
    return(0)
    #PLACEHOLDER

# Detect Mezzanine Type -- Works with only V600E or V1000E...
# TODO: update for Spartan ID Codes
def DetectMezzanineType():
    SetChain(VIRTEX_PROGRAM)
    # Mezzanine Chip Types
    # VIRTEX600  =  0
    # VIRTEX1000 =  1
    # UNKNOWN    = -1

    #######################################################################
    # Check if we have a Match for the Virtex 1000E
    #######################################################################
    Err = 0

    # Check EPROM 1 ID Code
    jtag.WriteIR(0x1FFFFF, V1000_IR_SIZE)
    jtag.WriteIR(0x1FFEFF, V1000_IR_SIZE)
    data = jtag.ReadDR(0x0, V_ID_DR_SIZE)
    data = data & V_EPROM1_ID_MASK

    if (data != V_EPROM1_ID) and (data != V_EPROM1_ID2):
        Err+=1

    # Check EPROM 2 ID Code
    jtag.WriteIR(0x1FFFFF, V1000_IR_SIZE)
    jtag.WriteIR(0x1FFFFE, V1000_IR_SIZE)
    data = jtag.ReadDR(0x0, V_ID_DR_SIZE)
    data = data & V_EPROM2_ID_MASK

    if (data != V_EPROM2_ID) and (data != V_EPROM2_ID2):
        Err+=1

    # Check Virtex ID Code
    jtag.WriteIR(0x1FFFFF, V1000_IR_SIZE)
    jtag.WriteIR(0x09FFFF, V1000_IR_SIZE)
    data = jtag.ReadDR(0x0, V_ID_DR_SIZE)
    data = data & V1000E_ID_MASK

    if data != V1000E_ID:
        Err += 1

    # No Errors So We Have a Match
    if Err==0:
        return (VIRTEX1000)

    #######################################################################
    # It wasn't the 1000, so now check if it Matches the Virtex600E
    #######################################################################

    # Reset Error Counter
    Err = 0


    # Check EEPROM ID Code
    jtag.WriteIR(0x1FFF,    V600_IR_SIZE)
    jtag.WriteIR(0x1FFF,    V600_IR_SIZE)
    jtag.WriteIR(0x1FFE,    V600_IR_SIZE)
    data = jtag.ReadDR(0x0, V_ID_DR_SIZE)
    data = data & V_EPROM2_ID_MASK

    if (data != V_EPROM2_ID) and (data != V_EPROM2_ID2):
        Err += 1

    # Check Virtex ID Code
    jtag.WriteIR       (0x1FFF,    V600_IR_SIZE)
    jtag.WriteIR       (0x09FF,    V600_IR_SIZE)
    data = jtag.ReadDR (0x0,       V_ID_DR_SIZE)
    data = data & V600E_ID_MASK

    if data != V600E_ID:
        Err +=1

    # No Errors, so we have a match
    if Err == 0:
        return(VIRTEX600)

    #######################################################################
    # It wasn't either of those... so we return -1 (Unknown)
    #######################################################################
    else:
        return(-1)

def ReadIDCode (index):
    if index == 0:
        SetChain(VIRTEX_PROGRAM)
        # Read Virtex ID Code
        jtag.WriteIR(0xFFFF,21)
        return(jtag.ReadDR (0,32))
    if index == 1:
        # Read EPROM #1 ID Code
        jtag.WriteIR(0x1FFEFF,21)
        return(jtag.ReadDR (0,32))
    if index == 2:
        # Read EPROM #2 ID Code
        jtag.WriteIR(0x1FFFFE,21)
        return(jtag.ReadDR (0,32))
    if index == 3:
        # Set Slow Control Control Chain
        SetChain(SLOWCTL_CONTROL)
        # Read Slow Control Spartan User ID Code
        jtag.WriteIR(0x0,6)
        return(jtag.ReadDR (0,40))
