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
# Mezzanine Control Addresses
# ------------------------------------------------------------------------------

# Name          Adr      Len   Dir     Description
IDRead         = 0x00  #  40    read    Virtex ID register
HCMaskRead     = 0x01  #  384   read    hot mask
HCMaskWrite    = 0x02  #  384   write   hot mask
RdTrig         = 0x03  #  5     read    trigger register
WrTrig         = 0x04  #  5     write   trigger register
RdCfg          = 0x06  #  69    read    control register
WrCfg          = 0x07  #  69    write   control register
Wdly           = 0x0D  #  120   write   delay lines. cs_dly bits in Par
Rdly           = 0x0E  #  121?  read    delay lines. cs_dly bits in Par
CollMaskRead   = 0x13  #  224   read    collision pattern mask
CollMaskWrite  = 0x14  #  224   write   collision pattern mask
ParamRegRead   = 0x15  #  6     read    delay line control register actually
DelayCtrlRead  = 0x15
ParamRegWrite  = 0x16  #  6     read    delay line control register actually
DelayCtrlWrite = 0x16
InputEnable    = 0x17  #  0     write?  commands to disable and enable input
InputDisable   = 0x18  #  0     write?  commands to disable and enable input
YRwrite        = 0x19  #  31    write   output register (for debugging with UCLA test board)
OSread         = 0x1A  #  49    read    output storage
SNread         = 0x1B  #  1     read    one bit of serial number
SNwrite0       = 0x1C  #  0     write   0 bit into serial number chip
SNwrite1       = 0x1D  #  0     write   1 bit into serial number chip
SNreset        = 0x1E  #  0     write   reset serial number chip
Bypass         = 0x1F  #  1     bypass

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

#-------------------------------------------------------------------------------
# ALCTTYPE Enumeration
#-------------------------------------------------------------------------------
ALCT288 = 0 # ALCT 288 Channels
ALCT384 = 1 # ALCT 384 Channels
ALCT672 = 2 # ALCT 672 Channels

# ------------------------------------------------------------------------------
# Virtex Mezzanine ID Enumeration
# ------------------------------------------------------------------------------

VIRTEX600       = 0x00 # Mezzanine Detection Virtex 600 Code
VIRTEX1000      = 0x01 # Mezzanine Detection Virtex 1000 Code

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

#ALCT384 = 1
alct[1].name          = 'ALCT384'
alct[1].channels      = 384
alct[1].groups        = 4
alct[1].chips         = 24
alct[1].delaylines    = 16
alct[1].pwrchans      = 4

#ALCT672 = 2
alct[2].name          = 'ALCT672'
alct[2].channels      = 672
alct[2].groups        = 7
alct[2].chips         = 42
alct[2].delaylines    = 16
alct[2].pwrchans      = 4

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

# Read Slow Control or Mezzanine FIRMWARE FPGA ID Codes
#def ReadIDCode (alct_ctl):
#    if (alct_ctl == SLOW_CTL):
#        SetChain(SLOW_CTL) # Slow Control Control Chain
#        jtag.WriteIR(0, SC_IR)
#        return(jtag.ReadDR(0x00, CTRL_SC_ID_DR_SIZE))
#    elif (alct_ctl == FAST_CTL):
#        SetChain(4) # Virtex Control Chain
#        jtag.WriteIR(0, V_IR)
#        return(jtag.ReadDR(0x00, USER_V_ID_DR_SIZE))
#    else:
#        return(0)

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
    jtag.WriteIR(0x7FF,11)
    jtag.WriteIR(0x7FE,11)
    result = jtag.ReadDR(0xffffffff,33)
    jtag.WriteIR(0x7FF,11)
    return (result)

def SCReadFPGAID():
    jtag.WriteIR(0x7F0,11)
    jtag.WriteIR(0x7FF,11)
    jtag.WriteIR(0x6FF,11)
    result = jtag.ReadDR(0x1fffffffe,33)
    jtag.WriteIR(0x7FF,11)
    return(result)

def VReadFPGAID():
    jtag.WriteIR(0x1F,5)
    jtag.WriteIR(0x1F,5)
    jtag.WriteIR(0x9,5)
    result = jtag.ReadDR(0xFFFFFFFF,34)
    jtag.WriteIR(0x1F,5)
    return(result)

def VReadEPROMID1():
    jtag.WriteIR(0x1FF0,13)
    jtag.WriteIR(0x1FFF,13)
    jtag.WriteIR(0x1FFF,13)
    jtag.WriteIR(0x1FFE,13)
    result = jtag.ReadDR(0xffffffff,34)
    jtag.WriteIR(0x1FFF,13)
    return(result)

def VReadEPROMID2():
    jtag.WriteIR(0x1FFFF0,21)
    jtag.WriteIR(0x1FFFFF,21)
    jtag.WriteIR(0x1FFFFE,21)
    result = jtag.ReadDR(0xffffffff,34)
    jtag.WriteIR(0x1FFFFFF,21)
    return(result)

# Detect Mezzanine Type -- Works with only V600E or V1000E...
# TODO: update for Spartan ID Codes? Maybe pointless since we don't have test firmware for the Spartan :(
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


    # Check EEPROM2 ID Code
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



def slow_control_fpga_id():
    # Field       Len Typical Description
    # -------     --- ------- --------------------------
    # [3:0]       4   7       Chip ID number, fixed at 7
    # [7:4]       4   C       Software Version ID [0-F]
    # [23:8]      16  2001    Year: 4 BCD digits
    # [31:24]     8   17      Day:  2 BCD digits
    # [39:32]     8   09      Month: 2 BCD digits
    SetChain(SLOWCTL_CONTROL)
    jtag.WriteIR(0x0,6)
    return(jtag.ReadDR (0,40))

def mezzanine_fpga_id():
    #	Virtex-E / Spartan-6 ID register
    #	Field		Len	Name	Description
    #	-------		---	----	--------------------------
    #	[5:0]		6	ver		Firmware version
    #	[8:6]		3	wgn		(see Table 9)
    #	[9]			1	bf		(see Table 9)
    #	[10]		1	np		(see Table 9)
    #	[11]		1	mr		(see Table 9)
    #	[12]		1	ke		(see Table 9)
    #	[13]		1	rl		(see Table 9)
    #	[14]		1	pb		(see Table 9)
    #	[15]		1	sp6		(see Table 9)
    #	[16]		1	seu		(see Table 9)
    #	[18:17]		2	resvd	Reserved
    #	[30:19]		12	year	binary code
    #	[35:31]		5	day		binary code
    #	[39:36]		4	month	binary code
    SetChain(VIRTEX_CONTROL)
    jtag.WriteIR(0x0,6)
    return(jtag.ReadDR (0,40))


def ReadIDCode (index):
    # Read Virtex ID Code
    if index == 0:
        return(mezzanine_fpga_id())

    # Read EPROM #1 ID Code
    if index == 1:
        jtag.WriteIR(0x1FFFFF, 21)
        jtag.WriteIR(0x1FFEFF, 21)
        return(jtag.ReadDR(0x0, 32) & V_EPROM1_ID_MASK)

    # Read EPROM #2 ID Code
    if index == 2:
        jtag.WriteIR(0x1FFFFF, V1000_IR_SIZE)
        jtag.WriteIR(0x1FFFFE, V1000_IR_SIZE)
        data = jtag.ReadDR(0x0, V_ID_DR_SIZE) & V_EPROM2_ID_MASK
        if (data > 0):
            return(data)
        else:
            # Check EEPROM2 ID Code
            jtag.WriteIR(0x1FFF,    V600_IR_SIZE)
            jtag.WriteIR(0x1FFF,    V600_IR_SIZE)
            jtag.WriteIR(0x1FFE,    V600_IR_SIZE)
            return(jtag.ReadDR(0x0, V_ID_DR_SIZE) & V_EPROM2_ID_MASK)

    # Read Slow Control Spartan User ID Code
    if index == 3:
        return(slow_control_fpga_id())
