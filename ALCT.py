################################################################################
# ALCT.py -- Generic Tools for ALCT I/O, Register Definitions
################################################################################

from time        import sleep 
from Common      import MutableNamedTuple
from JTAGLib     import *
from ALCT        import *
from LPTJTAGLib  import *
from SlowControl import *

ActiveHW = 1

VIRTEX600       = 0x00 # Mezzanine Detection Virtex 600 Code
VIRTEX1000      = 0x01 # Mezzanine Detection Virtex 1000 Code 
UNKNOWN         = 0xFF # Mezzanine Detection Unknown ID Code

################################################################################
# Mezzanine Control Addresses
################################################################################
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

################################################################################
# Array of the Sizes of Virtex Register Locations
# Used by WriteRegister and ReadRegister
################################################################################

RegSz = {
    0x00: 40,   # IDRead        
    0x01: 384,  # HCMaskRead    
    0x02: 384,  # HCMaskWrite   
    0x03: 2,    # RdTrig        
    0x04: 2,    # WrTrig        
    0x06: 69,   # RdCfg         // read control register
    0x07: 69,   # WrCfg         // write control register
    0x0D: 120,  # Wdly          // write delay lines. cs_dly bits in Par
    0x0E: 120,  # Rdly          // read  delay lines. cs_dly bits in Par
    0x13: 224,  # CollMaskRead  
    0x14: 224,  # CollMaskWrite 
    0x15: 6,    # ParamRegRead  
    0x16: 6,    # ParamRegWrite 
    0x17: 0,    # InputEnable   
    0x18: 0,    # InputDisable  
    0x19: 31,   # YRwrite       
    0x1A: 49,   # OSread        
    0x1B: 1,    # SNread        
    0x1F: 1}    # Bypass        

################################################################################
# ID Masks and ID Codes
################################################################################

PROG_SC_EPROM_ID        = 0X0005024093
PROG_SC_EPROM_ID_MASK   = 0X01FFFFFFFF

PROG_SC_FPGA_ID         = 0X0000838126
PROG_SC_FPGA_ID_MASK    = 0X01FFFFFFFF

PROG_V_EPROM1_ID        = 0X000A04C126
PROG_V_EPROM1_ID_MASK   = 0X003FFFFFFF
PROG_V_EPROM1_ID2       = 0X000A06C126

PROG_V_EPROM2_ID        = 0X0005026093
PROG_V_EPROM2_ID_MASK   = 0X003FFFFFFF

PROG_V_EPROM2_ID2       = 0X0005036093

PROG_V_FPGA_ID          = 0X000290024C
PROG_V_FPGA_ID_MASK     = 0X003FFFFFFF

PROG_V_FPGA600_7_ID     = 0X0021460126
PROG_V_FPGA600_7_ID_MASK= 0X003FFFFFFF

PROG_V_FPGA600_ID       = 0X0001460126
PROG_V_FPGA600_ID_MASK  = 0X000FFFFFFF

PROG_SC_IR_SIZE         = 11
PROG_SC_ID_DR_SIZE      = 33
PROG_V_IR_SIZE          = 21
PROG_V_ID_DR_SIZE       = 34

CTRL_SC_FPGA_ID         = 0x09072001B8
CTRL_SC_ID_DR_SIZE      = 40

USER_V_FPGA_ID          = 0x0925200207
USER_V_ID_DR_SIZE       = 40

################################################################################
# JTAG Chains
################################################################################
SLOW_CTL        = 0x0
FAST_CTL        = 0x1
BOARD_SN        = 0x2
MEZAN_SN        = 0x3
VRTX_CH	        = 0x3
V_IR            = 0x5
SC_IR           = 0x6

SLOWCTL_PROGRAM = 0x1 # Slow Control Programming
SLOWCTL_CONTROL = 0x0 # Slow Control Control
VIRTEX_PROGRAM  = 0x5 # Virtex Programming
VIRTEX_CONTROL  = 0x4 # Virtex Control
#array of JTAG Chains... legacy of old code
arJTAGChains = [0x1, 0x0, 0x5, 0x4]


################################################################################
# Board Parameters
################################################################################

MAX_DELAY_GROUPS            = 7
MAX_DELAY_CHIPS_IN_GROUP    = 6
MAX_NUM_AFEB                = 42
parlen                      = None

################################################################################
# Threshold Read/Write Stuff
################################################################################

ADC_REF = 1.225 # ADC Reference Voltage
ThreshToler = 4 # Threshold Tolerance (discrepancy is ok within +- ThreshToler)

arADCChannel = [1, 0, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0, 10, 
                9, 8,  7, 6, 5, 4, 3, 2, 1, 0, 0, 1, 2,  3, 
                4, 5,  6, 7, 8, 0, 1, 2, 3, 4, 5, 6, 7,  8]

arADCChip    = [2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 
                0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 3, 3, 3, 
                3, 3, 3, 3, 3, 4, 4, 4, 4, 4, 4, 4, 4, 4]

mapGroupMask = [0, 0, 0, 1, 1, 1, 2, 2, 2, 3, 3, 3, 0, 0, 
                0, 1, 1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 4, 5, 
                5, 5, 6, 6, 6, 4, 4, 4, 5, 5, 5, 6, 6, 6]

################################################################################
# Container for ADC Voltage Measurement
################################################################################
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

################################################################################
# Container for ADC Current Measurement
################################################################################
arCurrents = [ MutableNamedTuple() for i in range(4)] 

arCurrents[0].ref       = '1.8v'      
arCurrents[0].ref288    = 0.58
arCurrents[0].ref384    = 0.94 # double check this
arCurrents[0].ref672    = 0.94 # double check this
arCurrents[0].coef      = 0.002987
arCurrents[0].toler     = 0.1

arCurrents[1].ref       = '3.3v'      
arCurrents[1].ref288    = 1.28
arCurrents[1].ref384    = 2.81 # double check this
arCurrents[1].ref672    = 2.81 # double check this
arCurrents[1].coef      = 0.002987
arCurrents[1].toler     = 0.2

arCurrents[2].ref       = '5.5v1'      
arCurrents[2].ref288    = 0.15
arCurrents[2].ref384    = 0.15 # double check this
arCurrents[2].ref672    = 0.15 # double check this
arCurrents[2].coef      = 0.002987
arCurrents[2].toler     = 0.1

arCurrents[3].ref       = '5.5v2'      
arCurrents[3].ref288    = 0.00
arCurrents[3].ref384    = 0.15  # double check this
arCurrents[3].ref672    = 0.15  # double check this
arCurrents[3].coef      = 0.002987
arCurrents[3].toler     = 0.1

################################################################################
# Container for ADC Temperature Measurement
################################################################################
arTemperature = MutableNamedTuple()
arTemperature.ref       = 'On Board Temperature' 
arTemperature.refval    = 25.0
arTemperature.coef      = 0.1197
arTemperature.toler     = 5.0

################################################################################
# ALCTTYPE Definitions
################################################################################
ALCT288 = 0 # ALCT 288 Channels
ALCT384 = 1 # ALCT 384 Channels
ALCT672 = 2 # ALCT 672 Channels

################################################################################
# CHAMBER Definitions
################################################################################
ME1_1   = 0 # ME1/1
ME1_2   = 1 # ME1/2
ME1_3   = 2 # ME1/3
ME2_1   = 3 # ME2/1
ME2_2   = 4 # ME2/2
ME3_1   = 5 # ME3/1
ME3_2   = 6 # ME3/2
ME4_1   = 7 # ME4/1
ME4_2   = 8 # ME4/2

################################################################################
# Power Supply Enumeration
################################################################################
V18_PWR_SPLY   = 0        # Power Supply 1.8V
V33_PWR_SPLY   = 1        # Power Supply 3.3V
V55_1_PWR_SPLY = 2        # Power Supply 5.5V (1)
V55_2_PWR_SPLY = 3        # Power Supply 5.5V (2)

################################################################################
# Array of Tuples to hold Properties of Different Board Types
################################################################################
alct = [ MutableNamedTuple() for i in range(3)] 

#ALCT288 = 0
alct[0].name          = 'ALCT288'   # Name 
alct[0].channels      = 288         # Number of channels on board
alct[0].groups        = 3           # Number of Delay Chip Groups
alct[0].chips         = 6           # Number of Delay Chips per Group
alct[0].delaylines    = 16          # Number of Channels Per Delay Chip
alct[0].pwrchans      = 3           # Number of Power Inputs

#ALCT288 = 1
alct[1].name          = 'ALCT384'
alct[1].channels      = 384
alct[1].groups        = 4
alct[1].chips         = 6
alct[1].delaylines    = 16
alct[1].pwrchans      = 4

#ALCT288 = 2
alct[2].name          = 'ALCT672'
alct[2].channels      = 672
alct[2].groups        = 7
alct[2].chips         = 6
alct[2].delaylines    = 16
alct[2].pwrchans      = 4

################################################################################
# Array of Tuples to hold properties of Different Chamber Types
# Unused at the moment... consider to remove.. 
################################################################################
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


################################################################################
# ALCT Status Codes... Unused? 
################################################################################
#ALCTSTATUS = {
#        1: "EALCT_SUCCESS",   	# Successful completion
#        2: "EALCT_FILEOPEN",    # Filename could not be opened
#        3: "EALCT_FILEDEFECT", 	# Configuration file inconsistency
#        4: "EALCT_PORT", 	# JTAG Device problem
#        5: "EALCT_CHAMBER", 	# Bad chamber_type number
#        6: "EALCT_ARG", 	# Argument Out Of Range
#        7: "EALCT_TESTFAIL"}    # Test failure

alct_idreg  = MutableNamedTuple()   #ALCT ID Register
sc_idreg    = MutableNamedTuple()   #Slow Control ID Register
v_idreg     = MutableNamedTuple() 

################################################################################
# more constants.. should move with the rest
################################################################################
FIFO_RESET = 0xC
FIFO_READ  = 0xA
FIFO_WRITE = 0x9

IDReadReg          = MutableNamedTuple() 
IDReadReg.val      = 0x00
IDReadReg.length   = 40

RdDataReg          = MutableNamedTuple()  
RdDataReg.val      = 0x01 
RdDataReg.length   = 16

WrDatF 	        = MutableNamedTuple()  
WrDatF.val      = 0x04 
WrDatF.length      = 16

WrAddF 	        = MutableNamedTuple()  
WrAddF.val      = 0x06 
WrAddF.length      = 10

WrParamF        = MutableNamedTuple()  
WrParamF.val    = 0x08 
WrParamF.length    = 4


CRfld = [ MutableNamedTuple() for i in range(26)] 


# unused ? 
#CRfld[0].name       ='trig_mode'
#CRfld[0].mask       =3
#CRfld[0].bit        =0
#CRfld[0].default    =0
#
#CRfld[1].name       ='ext_trig_en'
#CRfld[1].mask       =1
#CRfld[1].bit        =2
#CRfld[1].default    =0
#
#CRfld[2].name       ='pretrig_halt'
#CRfld[2].mask       =1
#CRfld[2].bit        =3
#CRfld[2].default    =0
#
#CRfld[3].name       ='inject'
#CRfld[3].mask       =1
#CRfld[3].bit        =4
#CRfld[3].default    =0
#
#CRfld[4].name       ='inject_mode'
#CRfld[4].mask       =1
#CRfld[4].bit        =5
#CRfld[4].default    =0
#
#CRfld[5].name       ='inject_mask'
#CRfld[5].mask       =0x7f
#CRfld[5].bit        =6
#CRfld[5].default    =0x7f
#
#CRfld[6].name       ='nph_thresh'
#CRfld[6].mask       =7
#CRfld[6].bit        =13
#CRfld[6].default    =2
#
#CRfld[7].name       ='nph_pattern'
#CRfld[7].mask       =7
#CRfld[7].bit        =16
#CRfld[7].default    =4
#
#CRfld[8].name       ='drift_delay'
#CRfld[8].mask       =3
#CRfld[8].bit        =19
#CRfld[8].default    =3
#
#CRfld[9].name       ='fifo_tbins'
#CRfld[9].mask       =0x1f
#CRfld[9].bit        =21
#CRfld[9].default    =7
#
#CRfld[10].name       ='fifo_pretrig'
#CRfld[10].mask       =0x1f
#CRfld[10].bit        =26
#CRfld[10].default    =1
#
#CRfld[11].name       ='fifo_mode'
#CRfld[11].mask       =3
#CRfld[11].bit        =31
#CRfld[11].default    =1
#
#CRfld[12].name       ='fifo_lastlct'
#CRfld[12].mask       =7
#CRfld[12].bit        =33
#CRfld[12].default    =3
#
#CRfld[13].name       ='l1a_delay'
#CRfld[13].mask       =0xff
#CRfld[13].bit        =36
#CRfld[13].default    =0x78
#
#CRfld[14].name       ='l1a_window'
#CRfld[14].mask       =0xf
#CRfld[14].bit        =44
#CRfld[14].default    =3
#
#CRfld[15].name       ='l1a_offset'
#CRfld[15].mask       =0xf
#CRfld[15].bit        =48
#CRfld[15].default    =0
#
#CRfld[16].name       ='l1a_internal'
#CRfld[16].mask       =1
#CRfld[16].bit        =52
#CRfld[16].default    =0
#
#CRfld[17].name       ='board_id'
#CRfld[17].mask       =7
#CRfld[17].bit        =53
#CRfld[17].default    =5
#
#CRfld[18].name       ='bxn_offset'
#CRfld[18].mask       =0xf
#CRfld[18].bit        =56
#CRfld[18].default    =0
#
#CRfld[19].name       ='ccb_enable'
#CRfld[19].mask       =1
#CRfld[19].bit        =60
#CRfld[19].default    =0
#
#CRfld[20].name       ='alct_jtag_ds'
#CRfld[20].mask       =1
#CRfld[20].bit        =61
#CRfld[20].default    =1
#
#CRfld[21].name       ='alct_tmode'
#CRfld[21].mask       =3
#CRfld[21].bit        =62
#CRfld[21].default    =0
#
#CRfld[22].name       ='alct_amode'
#CRfld[22].mask       =3
#CRfld[22].bit        =64
#CRfld[22].default    =0
#
#CRfld[23].name       ='alct_mask_all'
#CRfld[23].mask       =1
#CRfld[23].bit        =66
#CRfld[23].default    =0
#
#CRfld[24].name       ='trig_info_en'
#CRfld[24].mask       =1
#CRfld[24].bit        =67
#CRfld[24].default    =0
#
#CRfld[25].name       ='sn_select'
#CRfld[25].mask       =1
#CRfld[25].bit        =68
#CRfld[25].default    =0

# Unused ? 
#CRdescr = [
#            'Virtex Trigger Mode',
#            'External Trigger Enable',
#            'Pre-Trigger and Halt Mode',
#            'Inject Test Pattern',
#            'Injector Repeat Mode (requires Inject Test Pattern = 1)',
#            'Injector LCT Chip Mask [6..0]. Bit n maps to LCT chip n',
#            'Number of Planes Hit Threshold for Pre-Trigger',
#            'Pattern hits required after drift delay to allow an LCT-trigger',
#            'Drift delay after pre-trigger (25ns steps)',
#            'Total number of FIFO time bins per wire group',
#            'FIFO time bins before per-trigger (included in total)',
#            'FIFO Mode',
#            'FIFO: Last LCT chip to be read out',
#            'Level 1 Accept delay after pre-trigger',
#            'Level 1 Accept window width (25ns steps)',
#            'Level 1 Accept counter Pre-Load value (arbitrary value)',
#            'L1A generated internally during L1A window',
#            'ALCT2001 circuit board ID (arbitrary value)',
#            'Bunch Crossing Counter Offset (set to match Cathode LCT bxn)',
#            'CCB Disable (Ignores CCb signals l1A, BXn, BxReset)',
#            'ALCT-bus Enable (affects all LCT chips)',
#            'ALCT Test Pattern Mode (affects all LCT chips if ALCT-bus Enable = 1)',
#            'ALCT Accelerator Muon Mode (affects all LCT chips)',
#            'Mask All Wire Group inputs to LCT chips (affects all LCT chips)',
#            'ALCT-bus spare signals (not currently used, set to be 0)' ]

# Unused ? 
OperDescr = [
            'Blank Check of Slow Control EPROM',
            'Blank Check of Virtex 1000 EPROM #1',
            'Blank Check of Virtex 1000 EPROM #2',
            'Blank Check of Virtex 600 EPROM',
            'Load Slow Control EPROM',
            'Load Slow Control FPGA',
            'Load Virtex 600 EPROM',
            'Load Virtex 600 FPGA',
            'Load Virtex 1000 EPROM #1',
            'Load Virtex 1000 EPROM #2',
            'Load Virtex 1000 FPGA' ]

# Select JTAG Programming Chain
def SetChain(ch): 
    set_chain(ch)

# Write Virtex Register
def WriteRegister(reg, value):
    WriteIR(reg, V_IR) 
    result = WriteDR(value, RegSz[reg])
    return (result)

# Read Virtex Register
def ReadRegister(reg): 
    WriteIR(reg, V_IR)
    result = ReadDR(0x0,RegSz[reg])
    return(result)

def SCReadEPROMID():
    WriteIR(0x7F0,11)
    time.sleep(0.1)     #sleep 100 ms
    WriteIR(0x7FF,11)
    WriteIR(0x7FE,11)
    result = ReadDR(0xffffffff,33)
    WriteIR(0x7FF,11)
    return (result)

def SCReadFPGAID(): 
    WriteIR(0x7F0,11)
    time.sleep(0.1)     #sleep 100 ms
    WriteIR(0x7FF,11)
    WriteIR(0x6FF,11)
    result = ReadDR(0x1fffffffe,33)
    WriteIR(0x7FF,11)
    return(result)

def SCEraseEPROM(): 
    if (SCReadEPROMID & PROG_SC_EPROM_ID_MASK) == PROG_SC_EPROM_ID :
        WriteIR(0x7E8, 11)
        WriteDR(0x4,7)
        WriteIR(0x7EB,11)
        WriteDR(0x1,17)
        WriteIR(0x7EC,11)
        time.sleep(0.2)     #sleep 200 ms
        WriteIR(0x7F0,11)
        time.sleep(0.1)     #sleep 100 ms
        WriteIR(0x7FF,11)
        WriteDR(0x0,2)
        result = True
    else:
        result = False
    return(result)

def SCBlankCheckEPROM(errs):
    len = 16385
    blocks = 64
    if	(SCReadEPROMID & PROG_SC_EPROM_ID_MASK) == PROG_SC_EPROM_ID:
        WriteIR(0x7E8,11)
        WriteDR(0x34,7)
        WriteIR(0x7E5,11)
        time.sleep(0.1)     #sleep 100 ms
        errs = 0
        for i in range(0,blocks):
            StartDRShift
            pmax = len//32
            for p in range(pmax):
                data = 0
                if (len-32*p) > 32:
                    data = ShiftData(0xFFFFFFFF, 32, False)
                    if data == 0xFFFFFFFF :
                        Inc(errs)
                else:
                    data = ShiftData(0xFFFFFFFF, len - 32*p, True)
                    if data == (0xFFFFFFFF >> (32-(len - 32*p))):
                        Inc(errs)
            ExitDRShift
            if (errs > 0):
                break
        WriteIR(0x7F0,11)
        time.sleep(0.1)     #sleep 100 ms
        WriteIR(0x7FF,11)
        WriteIR(0x7F0,11)
        time.sleep(0.1)     #sleep 100 ms
        WriteIR(0x7FF,11)
        WriteIR(0x7F0,11)
        time.sleep(0.1)     #sleep 100 ms
        WriteIR(0x7FF,11)
        if (errs == 0):
            result = True
    else: 
        result = False

def VReadFPGAID(): 
    WriteIR(0x1F,5)
    WriteIR(0x1F,5)
    WriteIR(0x9,5)
    result = ReadDR(0xffffffff,34)
    WriteIR(0x1F,5)
    return(result)

def VReadEPROMID1(): 
    WriteIR(0x1FF0,13)
    time.sleep(0.1)     #sleep 100 ms
    WriteIR(0x1FFF,13)
    WriteIR(0x1FFF,13)
    WriteIR(0x1FFE,13)
    result = ReadDR(0xffffffff,34)
    WriteIR(0x1FFF,13)
    return(result)

def VReadEPROMID2(): 
    WriteIR(0x1FFFF0,21)
    time.sleep(0.1)     #sleep 100 ms
    WriteIR(0x1FFFFF,21)
    WriteIR(0x1FFFFE,21)
    result = ReadDR(0xffffffff,34)
    WriteIR(0x1FFFFFF,21)
    return(result)

def VEraseEPROM1(): 
    if  ((VReadEPROMID1 & PROG_V_EPROM1_ID_MASK) == PROG_V_EPROM1_ID) or  \
        ((VReadEPROMID1 & PROG_V_EPROM1_ID_MASK) == PROG_V_EPROM1_ID2): 
        WriteIR(0x1FE8,13)
        WriteDR(0x8,8)
        WriteIR(0x1FEB,13)
        WriteDR(0x2,18)
        WriteIR(0x1FEC,13)
        time.sleep(0.2)     #sleep 200 ms
        WriteIR(0x1FF0,13)
        time.sleep(0.1)     #sleep 100 ms
        WriteIR(0x1FFF,13)
        result = True
    else:
        result = False
    return(result)

def VEraseEPROM2(): 
    if  ((VReadEPROMID2 & PROG_V_EPROM2_ID_MASK) == PROG_V_EPROM2_ID) or \
        ((VReadEPROMID2 & PROG_V_EPROM2_ID_MASK) == PROG_V_EPROM2_ID2):
        WriteIR(0x1FFFE8,21)
        WriteDR(0x4,8)
        WriteIR(0x1FFFEB,21)
        WriteDR(0x1,18)
        WriteIR(0x1FFFEC,21)
        time.sleep(0.2)     #sleep 200 ms
        WriteIR(0x1FFFF0,21)
        time.sleep(0.1)     #sleep 100 ms
        WriteIR(0x1FFFFF,21)
        result = True
    else:
        result = False
    return(result)

def V600EraseEPROM(): 
    if  ((VReadEPROMID1 & PROG_V_EPROM2_ID_MASK) == PROG_V_EPROM2_ID) or \
        ((VReadEPROMID1 & PROG_V_EPROM2_ID_MASK) == PROG_V_EPROM2_ID2) :
        WriteIR(0x1FE8,13)
        WriteDR(0x8,8)
        WriteIR(0x1FEB,13)
        WriteDR(0x2,18)
        WriteIR(0x1FEC,13)
        time.sleep(0.2)     #sleep 200 ms
        WriteIR(0x1FF0,13)
        time.sleep(0.1)     #sleep 100 ms
        WriteIR(0x1FFF,13)
        result = True
    else: 
        result = False
    return(result)

def VBlankCheckEPROM1(errs): 
    len = 8192
    blocks = 512
    if  ((VReadEPROMID1 & PROG_V_EPROM1_ID_MASK) == PROG_V_EPROM1_ID) or \
        ((VReadEPROMID1 & PROG_V_EPROM1_ID_MASK) == PROG_V_EPROM1_ID2):
        WriteIR(0x1FE8,13)
        WriteDR(0x34,7)
        WriteIR(0x1FF0,13)
        time.sleep(0.1)     #sleep 100 ms
        WriteIR(0x1FE8,13)
        WriteDR(0x34,7)
        WriteIR(0x1FEB,13)
        WriteDR(0x0,17)
        errs = 0

        for i in range(0,blocks):
            WriteIR(0x1FEF,13)
            time.sleep(0.1)     #sleep 100 ms
            StartDRShift
            for p in range(0,(len)//32):
                data = 0
                if ( (len-32*p) > 32):
                    data = ShiftData(0xFFFFFFFF, 32, False)
                    if (data == 0xFFFFFFFF):
                        Inc(errs)
                else:
                    data = ShiftData(0xFFFFFFFF, len - 32*p, True)
                    if data == (0xFFFFFFFF >> (32-(len - 32*p))):
                        Inc(errs)
            ExitDRShift
            if (errs > 0) :
                break

        WriteIR(0x1FF0,13)
        time.sleep(0.1)     #sleep 100 ms
        WriteIR(0x1FFF,13)
        WriteIR(0x1FFF,13)
        WriteDR(0x0,2)

        if (errs == 0):
            result = True

    else:
        result = False

    return(result)

def VBlankCheckEPROM2(errs):
    return(0)
    #PLACEHOLDER

def V600BlankCheckEPROM(errs):
    return(0)
    #PLACEHOLDER

def SetGroupStandbyReg(group, value):
    wgroups = 7
    data = ReadStandbyReg()
    if (group >=0) and (group < wgroups):
        res = data
        res = (res ^ ((res >> (group*6) & (0x3f)) << (6*group))) | ((value & 0x3F) << (group*6))
        SetStandbyReg(res & 0xFFFFFFFFFFFF)

def ReadGroupStandbyReg(group):
    SetChain(SLOW_CTL)
    wgroups = 7
    data    = ReadStandbyReg()
    if (group >=0) and (group < wgroups):
        return((data >> (group*6)) & 0x3F)
    else: 
        print("Problem with Read Group Standby Reg")

def SetStandbyReg(value):
    #SetChain(SLOW_CTL)
    len = 42
    WriteIR(0x24, SC_IR)
    WriteDR(value, len)

def ReadStandbyReg(): 
    SetChain(SLOW_CTL)
    len = 42
    WriteIR(0x25, SC_IR)
    result = ReadDR(0x0,len)
    return(result)

def SetStandbyForChan(chan, onoff):
    if (chan >= 0) and (chan < 42): 
        value = ReadGroupStandbyReg(chan // 6) & 0x3F
        value = (value ^ (((value >> (chan % 6)) & 0x1 ) << (chan % 6) )) | (int(onoff) << (chan % 6))
        SetGroupStandbyReg(chan % 6, value)

def SetTestPulsePower(sendval):
    len = 1
    WriteIR(0x26, SC_IR)
    WriteDR(sendval, len)

def ReadTestPulsePower(): 
    len = 1
    result = -1
    WriteIR(0x27, SC_IR)
    result = ReadDR(0x0,len)
    return(result)

def SetTestPulsePowerAmp(value):
    len = 9
    temp = 0
    for i in range(0,len-1):
        temp = temp | (((value >> i) & 0x1) << (7-i))
    WriteIR(0x3, SC_IR)
    WriteDR(temp, len)

def SetTestPulseWireGroupMask(value):
    len = 7
    if (ActiveHW):
        WriteIR(0x20, SC_IR)
        WriteDR(value & 0x7f, len)

def ReadTestPulseWireGroupMask(): 
    len = 7
    result = -1
    if (ActiveHW):
        WriteIR(0x21, SC_IR)
        result = ReadDR(0x0, len)
    return(result)

def SetTestPulseStripLayerMask(value):
    len = 6
    if (ActiveHW):
        WriteIR(0x22, SC_IR)
        WriteDR(value & 0x3f, len)

def ReadTestPulseStripLayerMask(): 
    len = 6
    result = -1
    if (ActiveHW):
        WriteIR(0x23, SC_IR)
        result = ReadDR(0x0, len)

#done
def FlipDR(data,length): 
    result=0
    for i in range(1,length):
        result = result | (((data >> i) & 0x1) << (10-i))
    return(result)

# Detect Mezzanine Type -- Works with only V600E or V1000E... 
# Need to update for Spartan
def DetectMezzanineType(): 
    SetChain(arJTAGChains[2])
    Err = 0
    # Mezzanine Chip Types
    # VIRTEX600  = 0x00 (0)
    # VIRTEX1000 = 0x01 (1)
    # UNKNOWN    = 0xFF (255)
    #Check EPROM 1 ID 
    ir = 0x1FFFFF
    WriteIR(ir, PROG_V_IR_SIZE)

    ir = 0x1FFEFF
    WriteIR(ir, PROG_V_IR_SIZE)

    data = 0x0000000000
    data = ReadDR(data, PROG_V_ID_DR_SIZE)

    data = data & PROG_V_EPROM1_ID_MASK

    if (data != PROG_V_EPROM1_ID) and (data != PROG_V_EPROM1_ID2): 
        Err+=1

    #Check EPROM 2 ID 
    ir = 0x1FFFFF
    WriteIR(ir, PROG_V_IR_SIZE)

    ir = 0x1FFFFE
    WriteIR(ir, PROG_V_IR_SIZE)

    data = 0x0000000000
    data = ReadDR(data, PROG_V_ID_DR_SIZE)
    data = data & PROG_V_EPROM2_ID_MASK
    if (data != PROG_V_EPROM2_ID) and (data != PROG_V_EPROM2_ID2): 
        Err+=1

    ir = 0x1FFFFF
    WriteIR(ir, PROG_V_IR_SIZE)

    ir = 0x09FFFF
    WriteIR(ir, PROG_V_IR_SIZE)

    data = 0x0000000000
    data = ReadDR(data, PROG_V_ID_DR_SIZE)
    data = data & PROG_V_FPGA_ID_MASK
    if data != PROG_V_FPGA_ID:   
        Err += 1

    if Err==0: 
        print('\t Mezanine Board with Xilinx Virtex 1000 chip is detected')
        MezChipType = VIRTEX1000
    else: 
        Err = 0
        ir = 0x1fff
        WriteIR(ir, PROG_V_IR_SIZE-8)

        ir = 0x1fff
        WriteIR(ir, PROG_V_IR_SIZE-8)

        ir = 0x1ffe
        WriteIR(ir, PROG_V_IR_SIZE-8)

        data = 0x0000000000
        data = ReadDR(data, PROG_V_ID_DR_SIZE)
        data = data & PROG_V_EPROM2_ID_MASK

        if (data != PROG_V_EPROM2_ID) and (data != PROG_V_EPROM2_ID2): 
            Err += 1

        ir = 0x1fff
        WriteIR(ir, PROG_V_IR_SIZE-8)

        ir = 0x09ff
        WriteIR(ir, PROG_V_IR_SIZE-8)

        data = 0x0000000000
        data = ReadDR(data, PROG_V_ID_DR_SIZE)
        data = data & PROG_V_FPGA600_ID_MASK
        if data != PROG_V_FPGA600_ID:
           Err +=1 

        if Err == 0: 
            print('\t Mezzanine Board with Xilinx Virtex 600 chip is detected')
            MezChipType = VIRTEX600
        else: 
            print('\t ERROR: Could not detect Mezanine Board')
            MezChipType = UNKNOWN
    return(MezChipType)
