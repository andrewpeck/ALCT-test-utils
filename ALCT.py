import time

from JTAGLib     import *
from ALCT        import *
from LPTJTAGLib  import *
from SlowControl import *

ConfigFile      = 'alct_tests.ini'
VIRTEX600       = 0
VIRTEX1000      = 1
UNKNOWN         = 255
IDRead          = 0x00
HCMaskRead      = 0x01
HCMaskWrite     = 0x02
RdTrig          = 0x03
WrTrig          = 0x04
RdCfg           = 0x06 # read control register
WrCfg           = 0x07 # write control register
Wdly            = 0x0d # write delay lines. cs_dly bits in Par
Rdly            = 0x0e # read  delay lines. cs_dly bits in Par
CollMaskRead    = 0x13
CollMaskWrite   = 0x14
ParamRegRead    = 0x15
ParamRegWrite   = 0x16
InputEnable     = 0x17
InputDisable    = 0x18
YRwrite         = 0x19
OSread          = 0x1a
SNRead          = 0x1b
SNwrite0        = 0x1c
SNwrite1        = 0x1d
SNreset         = 0x1e
Bypass          = 0x1f

PROG_SC_EPROM_ID        = 0x0005024093
PROG_SC_EPROM_ID_MASK   = 0x1ffffffff

PROG_SC_FPGA_ID         = 0x0000838126
PROG_SC_FPGA_ID_MASK    = 0x1ffffffff

PROG_V_EPROM1_ID        = 0x000A04C126
PROG_V_EPROM1_ID_MASK   = 0x03fffffff
PROG_V_EPROM1_ID2       = 0x000A06C126

PROG_V_EPROM2_ID        = 0x0005026093
PROG_V_EPROM2_ID_MASK   = 0x03fffffff

PROG_V_EPROM2_ID2       = 0x0005036093

PROG_V_FPGA_ID          = 0x000290024c
PROG_V_FPGA_ID_MASK     = 0x003fffffff

PROG_V_FPGA600_7_ID     = 0x0021460126
PROG_V_FPGA600_7_ID_MASK= 0x003fffffff

PROG_V_FPGA600_ID       = 0x0001460126
PROG_V_FPGA600_ID_MASK  = 0x000fffffff


PROG_SC_IR_SIZE         = 11
PROG_SC_ID_DR_SIZE      = 33
PROG_V_IR_SIZE          = 21
PROG_V_ID_DR_SIZE       = 34

CTRL_SC_FPGA_ID         = 0x09072001B8
CTRL_SC_ID_DR_SIZE      = 40

USER_V_FPGA_ID          = 0x0925200207
USER_V_ID_DR_SIZE       = 40


V_IR        = 5
SC_IR       = 6
SLOW_CTL    = 0
FAST_CTL    = 1
BOARD_SN    = 2
MEZAN_SN    = 3

RegSz = [
    40,     # IDRead = 0x0,
    384,    # HCMaskRead    = 0x1,
    384,    # HCMaskWrite   = 0x2,
    2,      # RdTrig        = 0x3,
    2,      # WrTrig        = 0x4,
    0,      #
    69,     # RdCfg         = 0x6, // read control register
    69,     # WrCfg         = 0x7, // write control register
    0,
    0,
    0,
    0,
    0,
    120,    # Wdly          = 0xd, // write delay lines. cs_dly bits in Par
    120,    # Rdly          = 0xe, // read  delay lines. cs_dly bits in Par
    0,
    0,
    0,
    0,
    224,    # CollMaskRead  = 0x13,
    224,    # CollMaskWrite = 0x14,
    6,      # ParamRegRead  = 0x15,
    6,      # ParamRegWrite = 0x16,
    0,      # InputEnable   = 0x17,
    0,      # InputDisable  = 0x18,
    31,     # YRwrite       = 0x19,
    49,     # OSread        = 0x1a,
    1,      # SNread        = 0x1b,
    0,
    0,
    0,
    1]       # Bypass        = 0x1f


NUM_OF_DELAY_GROUPS         = 4
NUM_OF_DELAY_CHIPS_IN_GROUP = 6
MAX_DELAY_GROUPS            = 7
MAX_DELAY_CHIPS_IN_GROUP    = 6
MAX_NUM_AFEB                = 42
NUM_AFEB                    = 42

parlen  = None

ADC_REF = 1.225 # Reference Voltage

arJTAGChains = [0x1, 0x0, 0x5, 0x4]

arADCChannel = [1, 0, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0, 10, 
                9, 8,  7, 6, 5, 4, 3, 2, 1, 0, 0, 1, 2,  3, 
                4, 5,  6, 7, 8, 0, 1, 2, 3, 4, 5, 6, 7,  8]

arADCChip    = [2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 
                0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 3, 3, 3, 
                3, 3, 3, 3, 3, 4, 4, 4, 4, 4, 4, 4, 4, 4]

mapGroupMask = [0, 0, 0, 1, 1, 1, 2, 2, 2, 3, 3, 3, 0, 0, 
                0, 1, 1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 4, 5, 
                5, 5, 6, 6, 6, 4, 4, 4, 5, 5, 5, 6, 6, 6]

class ADCValues:
    Ref
    RefVal
    Coef
    Toler

ThreshToler = 4

arVoltages = [ ADCValues() for i in range(4)] 

arVoltages[0].Ref       = '1.8V'
arVoltages[0].RefVal    = 1.8
arVoltages[0].Coef      = 0.005878
arVoltages[0].Toler     = 0.1

arVoltages[1].Ref       = '3.3V'
arVoltages[1].RefVal    = 3.3
arVoltages[1].Coef      = 0.005878
arVoltages[1].Toler     = 0.2

arVoltages[2].Ref       = '1st 5.5V'
arVoltages[2].RefVal    = '5.65'
arVoltages[2].Coef      = '0.005878'
arVoltages[2].Toler     = 0.2

arVoltages[3].Ref       = '2nd 5.5V'
arVoltages[3].RefVal    = '5.65'
arVoltages[3].Coef      = '0.005878'
arVoltages[3].Toler     = 0.2

arCurrents = [ ADCValues() for i in range(4)] 

arCurrents[0].ref       = '1.8v'      
arCurrents[0].refval    = 0.667
arCurrents[0].coef      = 0.002987
arCurrents[0].toler     = 0.1

arCurrents[1].ref       = '3.3v'      
arCurrents[1].refval    = 1.1
arCurrents[1].coef      = 0.002987
arCurrents[1].toler     = 0.2

arCurrents[2].ref       = '1st 5.5V'      
arCurrents[2].refval    = 0.150
arCurrents[2].coef      = 0.002987
arCurrents[2].toler     = 0.1

arCurrents[3].ref       = '2nd 5.5V'      
arCurrents[3].refval    = 0.150
arCurrents[3].coef      = 0.002987
arCurrents[3].toler     = 0.1

arTemperature = ADCValues()
arTemperature.ref       = 'On Board' 
arTemperature.refVal    = 25.0
arTemperature.coef      = 0.1197
arTemperature.toler     = 5.0

#ALCTTYPE
ALCT288 = 0 # ALCT 288 Channels
ALCT384 = 1 # ALCT 384 Channels
ALCT672 = 2 # ALCT 672 Channels

#CHAMBER
ME1_1	= 0 # ME1/1
ME1_2	= 1 # ME1/2
ME1_3	= 2 # ME1/3
ME2_1	= 3 # ME2/1
ME2_2	= 4 # ME2/2
ME3_1	= 5 # ME3/1
ME3_2	= 6 # ME3/2
ME4_1	= 7 # ME4/1
ME4_2	= 8 # ME4/2

#PWR_SPLY
V18_PWR_SPLY = 0	# Power Supply 1.8V
V33_PWR_SPLY = 1	# Power Supply 3.3V
V55_1_PWR_SPLY = 2	# Power Supply 5.5V (1)
V55_2_PWR_SPLY = 3	# Power Supply 5.5V (2)

class TALCTType:
    name
    alct
    channels
    groups
    chips
    delaylines
    pwrchans

class TChamberType:
    name
    chmbtype
    alct
    wires
    afebs_on551
    afebs_on552


alct_table = [ TALCTType() for i in range(3)] 

alct_table[0].name          = 'ALCT288'
alct_table[0].alct          = ALCT288
alct_table[0].channels      = 288
alct_table[0].groups        = 3
alct_table[0].chips         = 6
alct_table[0].delaylines    = 16
alct_table[0].pwrchans      = 3

alct_table[1].name          = 'ALCT384'
alct_table[1].alct          = ALCT384
alct_table[1].channels      = 384
alct_table[1].groups        = 4
alct_table[1].chips         = 6
alct_table[1].delaylines    = 16
alct_table[1].pwrchans      = 4

alct_table[2].name          = 'ALCT672'
alct_table[2].alct          = ALCT672
alct_table[2].channels      = 672
alct_table[2].groups        = 7
alct_table[2].chips         = 6
alct_table[2].delaylines    = 16
alct_table[2].pwrchans      = 4

chamb_table = [ TChamberType() for i in range(9)]

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

class DelayChip: 
    Value
    Pattern

DelayGroup = [ DelayChip() for i in range(MAX_DELAY_CHIPS_IN_GROUP)]
ALCTDelays = [ DelayChip() for i in range(MAX_DELAY_GROUPS)]
TPtrnImage ('i') # Array of bytes [0..5] [0..7]


#problem
ALCTSTATUS =  (	EALCT_SUCCESS,   	# Successful completion
                EALCT_FILEOPEN,         # Filename could not be opened
                EALCT_FILEDEFECT, 	# Configuration file inconsistency
                EALCT_PORT, 		# JTAG Device problem
                EALCT_CHAMBER, 		# Bad chamber_type number
                EALCT_ARG, 		# Argument Out Of Range
                EALCT_TESTFAIL)         # Test failure

class idreg:
    chip
    version
    day
    month
    year

alct_idreg  = idreg()   #ALCT ID Register
sc_idreg    = idreg()   #Slow Control ID Register
v_idreg     = idreg() 

class ConfigParameter: 
    name
    descr
    value
    default
    value_type

#more constants
FIFO_RESET = 0xC
FIFO_READ  = 0xA
FIFO_WRITE = 0x9

class JTAGreg : 
    val
    len

MeasDlyChan # array of size [0..41][0..15] of type Currency
MeasDly # array of size [0..41] of type Currency

IDReadReg       = JTAGReg() 
IDReadReg.val   = 0x00
IDReadReg.len   = 40

RdDataReg       = JTAGReg()  
RdDataReg.val   = 0x01 
RdDataReg.len   = 16

RdCntReg        = JTAGReg()  
RdCntReg.val    = 0x02 
RdCntReg.len    = 128

WrDatF 	        = JTAGReg()  
WrDatF.val      = 0x04 
WrDatF.len      = 16

WrAddF 	        = JTAGReg()  
WrAddF.val      = 0x06 
WrAddF.len      = 10

WrParamF        = JTAGReg()  
WrParamF.val    = 0x08 
WrParamF.len    = 4

WrFIFO	        = JTAGReg()  
WrFIFO.val      = 0x0A 
WrFIFO.len      = 1

WrDlyF	        = JTAGReg()  
WrDlyF.val      = 0x0B 
WrDlyF.len      = 8

ALCTWdly        = JTAGReg()  
ALCTWdly.val    = 0x0D 
ALCTWdly.len    = 120

ALCTRdly        = JTAGReg()  
ALCTRdly.val    = 0x0E 
ALCTRdly.len    = 120

RdParamDly      = JTAGReg()  
RdParamDly.val  = 0x15 
RdParamDly.len  = 6 # !! Change for Different Boards

WrParamDly      = JTAGReg()  
WrParamDly.val  = 0x16 
WrParamDly.len  = 6 # !! Change for Different Boards


class Rfield:
    name
    mask
    bit
    default

CRfld = [ Rfield() for i in range(26)] 

CRfld[0].name       ='trig_mode'
CRfld[0].mask       =3
CRfld[0].bit        =0
CRfld[0].default    =0

CRfld[1].name       ='ext_trig_en'
CRfld[1].mask       =1
CRfld[1].bit        =2
CRfld[1].default    =0

CRfld[2].name       ='pretrig_halt'
CRfld[2].mask       =1
CRfld[2].bit        =3
CRfld[2].default    =0

CRfld[3].name       ='inject'
CRfld[3].mask       =1
CRfld[3].bit        =4
CRfld[3].default    =0

CRfld[4].name       ='inject_mode'
CRfld[4].mask       =1
CRfld[4].bit        =5
CRfld[4].default    =0

CRfld[5].name       ='inject_mask'
CRfld[5].mask       =0x7f
CRfld[5].bit        =6
CRfld[5].default    =0x7f

CRfld[6].name       ='nph_thresh'
CRfld[6].mask       =7
CRfld[6].bit        =13
CRfld[6].default    =2

CRfld[7].name       ='nph_pattern'
CRfld[7].mask       =7
CRfld[7].bit        =16
CRfld[7].default    =4

CRfld[8].name       ='drift_delay'
CRfld[8].mask       =3
CRfld[8].bit        =19
CRfld[8].default    =3

CRfld[9].name       ='fifo_tbins'
CRfld[9].mask       =0x1f
CRfld[9].bit        =21
CRfld[9].default    =7

CRfld[10].name       ='fifo_pretrig'
CRfld[10].mask       =0x1f
CRfld[10].bit        =26
CRfld[10].default    =1

CRfld[11].name       ='fifo_mode'
CRfld[11].mask       =3
CRfld[11].bit        =31
CRfld[11].default    =1

CRfld[12].name       ='fifo_lastlct'
CRfld[12].mask       =7
CRfld[12].bit        =33
CRfld[12].default    =3

CRfld[13].name       ='l1a_delay'
CRfld[13].mask       =0xff
CRfld[13].bit        =36
CRfld[13].default    =0x78

CRfld[14].name       ='l1a_window'
CRfld[14].mask       =0xf
CRfld[14].bit        =44
CRfld[14].default    =3

CRfld[15].name       ='l1a_offset'
CRfld[15].mask       =0xf
CRfld[15].bit        =48
CRfld[15].default    =0

CRfld[16].name       ='l1a_internal'
CRfld[16].mask       =1
CRfld[16].bit        =52
CRfld[16].default    =0

CRfld[17].name       ='board_id'
CRfld[17].mask       =7
CRfld[17].bit        =53
CRfld[17].default    =5

CRfld[18].name       ='bxn_offset'
CRfld[18].mask       =0xf
CRfld[18].bit        =56
CRfld[18].default    =0

CRfld[19].name       ='ccb_enable'
CRfld[19].mask       =1
CRfld[19].bit        =60
CRfld[19].default    =0

CRfld[20].name       ='alct_jtag_ds'
CRfld[20].mask       =1
CRfld[20].bit        =61
CRfld[20].default    =1

CRfld[21].name       ='alct_tmode'
CRfld[21].mask       =3
CRfld[21].bit        =62
CRfld[21].default    =0

CRfld[22].name       ='alct_amode'
CRfld[22].mask       =3
CRfld[22].bit        =64
CRfld[22].default    =0

CRfld[23].name       ='alct_mask_all'
CRfld[23].mask       =1
CRfld[23].bit        =66
CRfld[23].default    =0

CRfld[24].name       ='trig_info_en'
CRfld[24].mask       =1
CRfld[24].bit        =67
CRfld[24].default    =0

CRfld[25].name       ='sn_select'
CRfld[25].mask       =1
CRfld[25].bit        =68
CRfld[25].default    =0


CRdescr = [
            'Virtex Trigger Mode',
            'External Trigger Enable',
            'Pre-Trigger and Halt Mode',
            'Inject Test Pattern',
            'Injector Repeat Mode (requires Inject Test Pattern = 1)',
            'Injector LCT Chip Mask [6..0]. Bit n maps to LCT chip n',
            'Number of Planes Hit Threshold for Pre-Trigger',
            'Pattern hits required after drift delay to allow an LCT-trigger',
            'Drift delay after pre-trigger (25ns steps)',
            'Total number of FIFO time bins per wire group',
            'FIFO time bins before per-trigger (included in total)',
            'FIFO Mode',
            'FIFO: Last LCT chip to be read out',
            'Level 1 Accept delay after pre-trigger',
            'Level 1 Accept window width (25ns steps)',
            'Level 1 Accept counter Pre-Load value (arbitrary value)',
            'L1A generated internally during L1A window',
            'ALCT2001 circuit board ID (arbitrary value)',
            'Bunch Crossing Counter Offset (set to match Cathode LCT bxn)',
            'CCB Disable (Ignores CCb signals l1A, BXn, BxReset)',
            'ALCT-bus Enable (affects all LCT chips)',
            'ALCT Test Pattern Mode (affects all LCT chips if ALCT-bus Enable = 1)',
            'ALCT Accelerator Muon Mode (affects all LCT chips)',
            'Mask All Wire Group inputs to LCT chips (affects all LCT chips)',
            'ALCT-bus spare signals (not currently used, set to be 0)' ]

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


#import JTAGLib, JTAGUtils, SysUtils

def SetChain(ch): 
    set_chain(arJTAGChains[ch])

def WriteRegister(reg, value, overload):
    WriteIR(reg, V_IR) 
    result = WriteDR(value, RegSz[reg])
    return (result)

def ReadRegister(reg): 
    WriteIR(reg, V_IR)
    result = ReadDR(0,RegSz[reg])
    return(result)

def PrepareDelayLinePatterns(dlys, image): #dlys istype ALCTDelays, image istype TPtrnImage
    for i in range (0,4): 
        dlys[i][0].Pattern = FlipByte(image[1][i*2]) | (word(image[4][i*2]) << 8)
        dlys[i][1].Pattern = FlipByte(image[1][i*2]) | (word(image[4][i*2]) << 8)
        dlys[i][2].Pattern = FlipByte(image[1][i*2]) | (word(image[4][i*2]) << 8)
        dlys[i][3].Pattern = FlipByte(image[1][i*2]) | (word(image[4][i*2]) << 8)
        dlys[i][4].Pattern = FlipByte(image[1][i*2]) | (word(image[4][i*2]) << 8)
        dlys[i][5].Pattern = FlipByte(image[1][i*2]) | (word(image[4][i*2]) << 8)

def Write6DelayLines(dlys, mask, option):   # overloaded function
    WriteIR(ParamRegWrite, V_IR)
    WriteDR(0x1ff & (not (mask << 2)), parlen)

    WriteIR(ParamRegRead, V_IR)
    ReadDR('0', parlen)

    WriteIR(Wdly, V_IR)
    StartDRShift

    for i in range(0,6):
        value   = ShiftData(FlipHalfByte(dlys[i].Value), 4, False)
        pattern = ShiftData(dlys[i].Pattern, 16, i=5)

    if ((option is bool) and (option is True)):
        dlys[i].Value = value
        dlys[i].Pattern = pattern
    elif (option is readdlys):
        readdlys[i].value   = shiftdata(fliphalfbyte(dlys[i].value), 4, False)
        readdlys[i].pattern = shiftdata(dlys[i].pattern, 16, i=5)

    ExitDRShift 
    WriteIR(IntToHex(ParamRegWrite,2), V_IR)
    WriteDR('1ff', parlen)

def SCReadEPROMID():
    WriteIR('7F0',11)
    time.sleep(0.1)     #sleep 100 ms
    WriteIR('7FF',11)
    WriteIR('7FE',11)
    result = ReadDR('ffffffff',33)
    WriteIR('7FF',11)
    return (result)

def SCReadFPGAID(): 
    WriteIR('7F0',11)
    time.sleep(0.1)     #sleep 100 ms
    WriteIR('7FF',11)
    WriteIR('6FF',11)
    result = ReadDR('1fffffffe',33)
    WriteIR('7FF',11)
    return(result)

def SCEraseEPROM(): 
    if ( (int(SCReadEPROMID,16) & PROG_SC_EPROM_ID_MASK) == PROG_SC_EPROM_ID ):
        WriteIR('7E8',11)
        WriteDR('4',7)
        WriteIR('7EB',11)
        WriteDR('1',17)
        WriteIR('7EC',11)
        time.sleep(0.2)     #sleep 200 ms
        WriteIR('7F0',11)
        time.sleep(0.1)     #sleep 100 ms
        WriteIR('7FF',11)
        WriteDR('0',2)
        result = True
    else:
        result = False
    return(result)


def SCBlankCheckEPROM(errs):
    len = 16385
    blocks = 64
    if	(Int(SCReadEPROMID,16) & PROG_SC_EPROM_ID_MASK) == PROG_SC_EPROM_ID:
        WriteIR('7E8',11)
        WriteDR('34',7)
        WriteIR('7E5',11)
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
        WriteIR('7F0',11)
        time.sleep(0.1)     #sleep 100 ms
        WriteIR('7FF',11)
        WriteIR('7F0',11)
        time.sleep(0.1)     #sleep 100 ms
        WriteIR('7FF',11)
        WriteIR('7F0',11)
        time.sleep(0.1)     #sleep 100 ms
        WriteIR('7FF',11)
        if (errs == 0):
            result = True
    else: 
        result = False


def VReadFPGAID(): 
    WriteIR('1F',5)
    WriteIR('1F',5)
    WriteIR('9',5)
    result = ReadDR('ffffffff',34)
    WriteIR('1F',5)
    return(result)

def VReadEPROMID1(): 
    WriteIR('1FF0',13)
    time.sleep(0.1)     #sleep 100 ms
    WriteIR('1FFF',13)
    WriteIR('1FFF',13)
    WriteIR('1FFE',13)
    result = ReadDR('ffffffff',34)
    WriteIR('1FFF',13)
    return(result)

def VReadEPROMID2(): 
    WriteIR('1FFFF0',21)
    time.sleep(0.1)     #sleep 100 ms
    WriteIR('1FFFFF',21)
    WriteIR('1FFFFE',21)
    result = ReadDR('ffffffff',34)
    WriteIR('1FFFFFF',21)
    return(result)


def VEraseEPROM1(): 
    if  ((int(VReadEPROMID1,16) & PROG_V_EPROM1_ID_MASK) == PROG_V_EPROM1_ID) or  \
        ((int(VReadEPROMID1,16) & PROG_V_EPROM1_ID_MASK) == PROG_V_EPROM1_ID2): 
        WriteIR('1FE8',13)
        WriteDR('8',8)
        WriteIR('1FEB',13)
        WriteDR('2',18)
        WriteIR('1FEC',13)
        time.sleep(0.2)     #sleep 200 ms
        WriteIR('1FF0',13)
        time.sleep(0.1)     #sleep 100 ms
        WriteIR('1FFF',13)
        result = True
    else:
        result = False
    return(result)


def VEraseEPROM2(): 
    if  ((int(VReadEPROMID2,16) & PROG_V_EPROM2_ID_MASK) == PROG_V_EPROM2_ID) or \
        ((int(VReadEPROMID2,16) & PROG_V_EPROM2_ID_MASK) == PROG_V_EPROM2_ID2):
        WriteIR('1FFFE8',21)
        WriteDR('4',8)
        WriteIR('1FFFEB',21)
        WriteDR('1',18)
        WriteIR('1FFFEC',21)
        time.sleep(0.2)     #sleep 200 ms
        WriteIR('1FFFF0',21)
        time.sleep(0.1)     #sleep 100 ms
        WriteIR('1FFFFF',21)
        result = True
    else:
        result = False
    return(result)


def V600EraseEPROM(): 
    if  ((int(VReadEPROMID1,16) & PROG_V_EPROM2_ID_MASK) == PROG_V_EPROM2_ID) or \
        ((int(VReadEPROMID1,16) & PROG_V_EPROM2_ID_MASK) == PROG_V_EPROM2_ID2) :
        WriteIR('1FE8',13)
        WriteDR('8',8)
        WriteIR('1FEB',13)
        WriteDR('2',18)
        WriteIR('1FEC',13)
        time.sleep(0.2)     #sleep 200 ms
        WriteIR('1FF0',13)
        time.sleep(0.1)     #sleep 100 ms
        WriteIR('1FFF',13)
        result = True
    else: 
        result = False
    return(result)

def VBlankCheckEPROM1(errs): 
    len = 8192
    blocks = 512
    if  ((int(VReadEPROMID1,16) & PROG_V_EPROM1_ID_MASK) == PROG_V_EPROM1_ID) or \
        ((int(VReadEPROMID1,16) & PROG_V_EPROM1_ID_MASK) == PROG_V_EPROM1_ID2):
        WriteIR('1FE8',13)
        WriteDR('34',7)
        WriteIR('1FF0',13)
        time.sleep(0.1)     #sleep 100 ms
        WriteIR('1FE8',13)
        WriteDR('34',7)
        WriteIR('1FEB',13)
        WriteDR('0',17)
        errs = 0

        for i in range(0,blocks):
            WriteIR('1FEF',13)
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

        WriteIR('1FF0',13)
        time.sleep(0.1)     #sleep 100 ms
        WriteIR('1FFF',13)
        WriteIR('1FFF',13)
        WriteDR('0',2)

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

def SetThreshold(ch, value):
    len = 12
    if (ActiveHW):
        temp = 0
        realch = ch
        if (ch >= 33):
            realch = ch+3
        time.sleep(0.1)     #sleep 100 ms
        tmp = value & 0xFF
        tmp = tmp | (( realch % 12) << 8)
        for i in range(0,len):
            temp = temp | (((tmp >> i)  & 0x1) << (11-i))

        WriteIR(IntToHex(0x8+(realch // 12),2), SC_IR)
        WriteDR(IntToHex(temp,3), len)


def ReadThreshold(ch):
    len = 11
    result = 0
    if (ActiveHW):
        time.sleep(0.1)     #sleep 100 ms
        temp = 0
        tmp  = arADCChannel[ch]
        for i in range(0,4):
            temp = temp | (((tmp >> i) & 0x1) << (3-i))

        WriteIR(IntToHex(0x10+arADCChip[ch],2), SC_IR)
        WriteDR(IntToHex(temp,3),len)

        time.sleep(0.1)     #sleep 100 ms

        WriteIR(IntToHex(0x10+arADCChip[ch],2), SC_IR)

        tmp = int(ReadDR(IntToHex(temp,3),len),16)

        temp = 0

        for i in range(1,len):
            temp = temp | (((tmp >> i) & 0x1) << (10-i))
        result = temp

    return(result)


def SetGroupStandbyReg(group, value):
    wgroups = 7
    data = ReadStandbyReg()
    if ( (data == '') and (group >=0) and (group < wgroups) ):
        res = int(data,16)
        res = (res ^ ((res >> (group*6) & (int(0x3f))) << (6*group))) | ((int(value & 0x3F)) << (group*6))
        SetStandbyReg(IntToHex(res, 12))


def ReadGroupStandbyReg(group):
    wgroups = 7
    result  = 0
    data    = ReadStandbyReg()
    if ((data == '') and (group >= 0) and (group < (wgroups))):
        result = (int(data,16) >> (group*6)) & 0x3F
    return(result)


def SetStandbyReg(value):
    len = 42
    if (ActiveHW):
        WriteIR('24', SC_IR)
        WriteDR(value, len)

def ReadStandbyReg(): 
    len = 42
    result = ''
    if (ActiveHW):
        WriteIR('25', SC_IR)
        result = ReadDR('0',len)
    return(result)


def SetStandbyForChan(chan, onoff):
    if (chan >= 0) and (chan < 42) : 
        value = ReadGroupStandbyReg(chan // 6) & 0x3F
        value = (value ^ (((value >> (chan % 6)) & 0x1 ) << (chan % 6) )) | (int(onoff) << (chan % 6))
        SetGroupStandbyReg(chan % 6, value)

def SetTestPulsePower(sendval):
    len = 1
    if (ActiveHW):
        WriteIR('26', SC_IR)
        WriteDR(IntToHex(sendval,1), len)

def ReadTestPulsePower(): 
    len = 1
    result = -1
    if (ActiveHW):
        WriteIR('27', SC_IR)
        result = int(ReadDR('0',len),16)
    return(result)

def SetTestPulsePowerAmp(value):
    len = 9
    if (ActiveHW):
        temp = 0
        for i in range(0,len-1):
            temp = temp | (((value >> i) & 0x1) << (7-i))
        WriteIR('3', SC_IR)
        WriteDR(IntToHex(temp, 3), len)

def SetTestPulseWireGroupMask(value):
    len = 7
    if (ActiveHW):
        WriteIR('20', SC_IR)
        WriteDR(IntToHex(value & 0x7f, 2), len)

def ReadTestPulseWireGroupMask(): 
    len = 7
    result = -1
    if (ActiveHW):
        WriteIR('21', SC_IR)
        result = int(ReadDR('0', len),16)
    return(result)

def SetTestPulseStripLayerMask(value):
    len = 6
    if (ActiveHW):
        WriteIR('22', SC_IR)
        WriteDR(IntToHex(value & 0x3f, 2), len)

def ReadTestPulseStripLayerMask(): 
    len = 6
    result = -1
    if (ActiveHW):
        WriteIR('23', SC_IR)
        result = int(ReadDR('0', len),16)

def ReadVoltageADC(chan):
    len = 11
    result = 0
    if (ActiveHW):
        temp = 0
        for i in range(0,4):
            temp = temp | ((((chan+6) >> i) & 0x1) << (3-i))

        for i in range(0,3):
            WriteIR('12', SC_IR)
            temp = int(ReadDR(IntToHex(temp,3), len),16)
        result = 0

        for i in range(0,len):
            result = result | (((temp >> i) & 0x1) << (10-i))
    return(result)

def ReadVoltage(chan): 
    result = ReadVoltageADC(chan)*arVoltages[chan].Coef
    return(result)

def ReadCurrentADC(chan):
    len = 11
    result = 0
    if (ActiveHW): 
        temp = 0
        for i in range(0,4):
            temp = temp | ((((chan+2) >> i) & 0x1) << (3-i))
        for i in range(0,3):
            WriteIR('12', SC_IR)
            temp = int(ReadDR(IntToHex(temp,3), len),16)
        result = 0
        for i in range(1,len):
            result = result | (((temp >> i) & 0x1) << (10-i))
    return(result)

def ReadCurrent(chan):
    result = ReadCurrentADC(chan)*arCurrents[chan].Coef
    return(result)

def ReadTemperatureADC(): 
    len = 11
    result = 0
    if (ActiveHW):
        for i in range(3): 
            WriteIR('12', SC_IR)
            temp = int(ReadDR('5', len),16)

        for i in range(1,len): 
            result = result | (((temp >> i) & 0x1) << (10-i))
    return(result)

def  ReadTemperature(): 
    result = ReadTemperatureADC()*arTemperature.Coef-50
    return(result)

################################################################################
# Test Board FIFO Functions
################################################################################

def SetFIFOMode(mode):
    if (ActiveHW):
        WriteIR(WrParamF.val, V_IR)
        WriteDR(IntToHex((0x8 | mode) & 0xF,1),WrParamF.len)

def SetFIFOReset(): 
    if (ActiveHW): 
        WriteIR(WrParamF.val, V_IR)
        WriteDR(8,WrParamF.len)
        WriteIR(WrParamF.val, V_IR)
        WriteDR(FIFO_RESET,WrParamF.len)
        WriteIR(WrParamF.val, V_IR)
        WriteDR(8,WrParamF.len)

def SetFIFOWrite(): 
    if (ActiveHW): 
        WriteIR(WrParamF.val, V_IR)
        WriteDR(FIFO_WRITE,WrParamF.len)

def SetFIFORead(): 
    if (ActiveHW): 
        WriteIR(WrParamF.val, V_IR)
        WriteDR(FIFO_READ,WrParamF.len)

def SetFIFOReadWrite(): 
    if (ActiveHW): 
        WriteIR(WrParamF.val, V_IR)
        WriteDR(FIFO_WRITE | FIFO_READ,WrParamF.len)

def FIFOClock(): 
    if (ActiveHW): 
        WriteIR(WrFIFO.val, V_IR)
        WriteDR('1',WrFIFO.len)

def ReadFIFOCounters(): 
    if (ActiveHW): 
        WriteIR(RdCntReg.val, V_IR)
        result = ReadDR('0',RdCntReg.len)
    return(result)

def SetFIFOValue(val):
    if (ActiveHW): 
        WriteIR(WrDatF.val, V_IR)
        WriteDR(val,WrDatF.len)

def SetFIFOChannel(ch,startdly):
    if (ActiveHW): 
        WriteIR(WrAddF.val, V_IR)
        WriteDR( ch | startdly << 6,WrAddF.len)

def SetTestBoardDelay(delay):
    if (ActiveHW): 
        WriteIR(WrParamF.val, V_IR)
        WriteDR(FIFO_RESET,WrParamF.len)

        WriteIR(WrDlyF.val, V_IR)
        WriteDR(IntToHex(FlipByte((255-delay) & 0xFF),2) ,WrDlyF.len)

        WriteIR(WrParamF.val, V_IR)
        WriteDR(8,WrParamF.len)

def SetALCTBoardDelay(ch, delay):
    if (ActiveHW): 
        for i in range (MAX_DELAY_CHIPS_IN_GROUP): 
            dlys[i].Value = 0
            dlys[i].Pattern = 0

        dlys[ch % MAX_DELAY_CHIPS_IN_GROUP].Value = delay

        Write6DelayLines(dlys, 1 << (ch // MAX_DELAY_CHIPS_IN_GROUP))

def SetTestBoardFIFO(fifoval, fifochan, numwords, startdelay, alctdelay, testboarddelay):
    numwords=1
    startdelay=2
    alctdelay=0
    testboarddelay=0

    if (ActiveHW): 
        SetFIFOReset
        SetFIFOChannel(fifochan, startdelay )
        SetFIFOValue(fifoval)
        SetTestBoardDelay(testboarddelay)
        SetALCTBoardDelay(fifochan, alctdelay)
        SetFIFOWrite
        for i in range(1,numwords+1):
            FIFOClock

def SetDelayTest(fifoval, fifochan, startdelay, alctdelay, testboarddelay):
    startdelay=2
    alctdelay=0
    testboarddelay=0
    if (ActiveHW): 
        SetFIFOChannel(fifochan, startdelay)
        SetFIFOValue(fifoval)
        SetTestBoardDelay(testboarddelay)
        SetALCTBoardDelay(fifochan, alctdelay)

def ReadFIFOValue():
    if (ActiveHW): 
        WriteIR(RdDataReg.val, V_IR)
        result = ReadDR(0,RdDataReg.len)
        return(result)
    else: 
        return(0)

def ALCTEnableInput(): 
    if (ActiveHW): 
        WriteIR(WrParamDly.val, V_IR)
        WriteDR(0x1FD,parlen)
        WriteIR(RdParamDly.val, V_IR)
        result = ReadDR(0, parlen)
        return(result)
    else: 
        return(0)

def ALCTDisableInput():
    if (ActiveHW): 
        WriteIR(WrParamDly.val, V_IR)
        WriteDR(0x1FF,parlen)
        WriteIR(RdParamDly.val, V_IR)
        result = ReadDR(0, parlen)
        return(result)
    else: 
        return(1)

def ReadFIFO(vals, numwords, cntrs):
    if (ActiveHW): 
        SetFIFOReset()
        SetFIFOWrite()
        FIFOClock()
        SetFIFOReadWrite()
        ALCTEnableInput()

        for i in range(numwords): 
            FIFOClock
            vals[i] = ReadFIFOValue

        cntstr = ReadFIFOCounters()
        result = cntstr

        for i in range (16):
            cntrs[15-i] = int(cntstr[i*2+1,i*2+2] + cntstr[i*2+2,i*2+3],16)

def ReadFIFOfast(numwords, cntrs):
    if (ActiveHW): 
        SetFIFOReset()
        SetFIFOWrite()
        FIFOClock()
        SetFIFOReadWrite()
        ALCTEnableInput()
        WriteIR(WrFIFO.val,V_IR)           # FIFOClock
        for i in range(numwords):
            if (ActiveHW): WriteDR(0x1,WrFIFO.len)    # FIFOClock

        cntstr = ReadFIFOCounters()

        for i in range(16):
            cntrs[15-i] = int(cntstr[i*2+1,i*2+2] + cntstr[i*2+2,i*2+3],16)


def PinPointRiseTime(TimeR, value, ch, StartDly_R, alct_dly, num): 
    #SetLength(cntrs, 16)
    RegisterMaskDone = 0
    tb_dly = 0

    SetDelayTest(value, ch, StartDly_R, alct_dly, tb_dly)

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

def PinPointRiseTime50(TimeR, TimeR_50, value, ch, StartDly_R, alct_dly, num): 

    SetDelayTest(value, ch, StartDly_R, alct_dly, tb_dly)

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

def PinPointFallTime(TimeF, value, ch, StartDly_F, alct_dly, num): 

    SetDelayTest(value, ch, StartDly_F, alct_dly, tb_dly)
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


def FindStartDly(StartDly_R, StartDly_F, value, ch, alct_dly, num): 

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

    #SetLength(cntrs, 16)
    tb_dly = 0

    SetDelayTest(value, ch, StartDly, alct_dly, tb_dly)

    for StartDly in range (5,16):
        # Access board
        SetFIFOChannel(ch, StartDly)
        ReadFIFOfast(num,cntrs)

        # Check counters and increment
        ChannelsCntr = 0  
        MaskDoneR    = 0

        for i in range(16):
            if (cntrs[i] > (num/2)) and ((value & (1 << i))>0):
                Inc(ChannelsCntr)
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

def FindStartDlyPin(StartDly_R, StartDly_F, value, ch, alct_dly, num, RegMaskDone, ):
    RegMaskDoneR = 0
    RegMaskDoneF = 0
    MaxChannelsCntr = 0
    FoundTimeBin  = False
    FirstCnhR = False    
    AllChnR = False
    FirstChnF = False    
    AllChnF = False
    StartDly_R = 5       
    StartDly_F = 5
    StartDly = 5
    tb_dly  = 0

    SetDelayTest(value, ch, StartDly, alct_dly, tb_dly)

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


def MeasureDelay(ch, PulseWidth, BeginTime_Min, DeltaBeginTime, Delay_Time, AverageDelay_Time, ErrMeasDly, RegMaskDone):
    MinWidth    = 30 
    MaxWidth    = 45
    value       = 0xFFFF
    num         = 100
    ErrMeasDly  = 0

    #pointless initialization
    for i in range(16): 
        TimeR_0[i] = 0
        TimeF_0[i] = 0
        TimeR_15[i] = 0
        DelayTimeR_0[i] = 0
        DelayTimeF_0[i] = 0
        DelayTimeR_15[i] = 0
        PulseWidth[i] = 0
        DeltaBeginTime[ch][i] = 0
        Delay_Time[ch][i] = 0

    alct_dly = 0

    if FindStartDlyPin(StartDly_R, StartDly_F, value, ch, alct_dly, num, RegMaskDone): 
        PinPointRiseTime(TimeR_0, value, ch, StartDly_R, alct_dly, num)
        PinPointFallTime(TimeF_0, value, ch, StartDly_F, alct_dly, num)

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

    alct_dly = 15
    AverageDelay_Time[ch] = 0 
    SumDelay_Time = 0

    if FindStartDly(StartDly_R, StartDly_F, value, ch, alct_dly, num): 
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

#def WriteToFile(BeginTime_Min: MeasDly
#    DeltaBeginTime: MeasDlyChan
#    DelayTime: MeasDlyChan
#    Average: MeasDly
#    BoardNum: string
#    PathString: string)
#var
#    TxtFile : TextFile
#    DataBuffer1, DataBuffer2: string
#    chip, channel, i: integer
#    //Create a file with the given path and the ALCT Board Number
#    AssignFile(TxtFile, PathString)
#    try
#        Rewrite(TxtFile)
#
#        writeln(TxtFile, '**********************************')
#        writeln(TxtFile, 'Delay Test Results' + #9 + 'Board# ' + BoardNum)
#        writeln(TxtFile, '**********************************')
#        writeln(TxtFile, '')
#        DataBuffer1 := ''
#        for i:=0 to 15 do
#            DataBuffer1 := DataBuffer1 + inttostr(i) + #9
#        writeln(TxtFile, #9 +#9 +#9 + 'Channel #')
#        writeln(TxtFile, #9 +#9 +#9 + DataBuffer1)
#
#        for chip:= 0 to NUM_AFEB-1 do
#            writeln(TxtFile, 'Chip #' + inttostr(chip))
#            writeln(TxtFile, 'Begin time: ' + CurrToStr(BeginTime_Min[chip]))
#            DataBuffer1 := ''
#            DataBuffer2 := ''
#            for channel := 0 to 15 do
#                DataBuffer1 := DataBuffer1 + CurrToStr(DeltaBeginTime[chip][channel]) + #9
#                DataBuffer2 := DataBuffer2 + CurrToStr(DelayTime[chip][channel]) + #9
#
#            writeln(TxtFile, 'Delta Begin Times:' + #9 + DataBuffer1)
#            writeln(TxtFile, 'Delay Times:' + #9 + #9 + DataBuffer2)
#            writeln(TxtFile, 'Average: ' + CurrToStr(Average[chip]))
#            writeln(TxtFile, '')
#    finally
#        CloseFile(TxtFile)
#
#
#
#
#{
#def FindStartDlyR(var StartDlyR_f: integer StartDly: integer; value: integer; ch: integer; alct_dly: integer; num: integer): boolean
#var
#    size, i, num_dly_ch, ChannelsCntr, tb_dly, StartDlyR: integer
#    cntrs : array of byte
#    vals : array of word
#    SetLength(vals, num)
#    SetLength(cntrs, 16)
#    tb_dly := 0
#    for i:=0 to 15 do
#        if ((value and (1 shl i))>0) 
#            Inc(num_dly_ch)
#
#        for StartDlyR := StartDly-1 downto 2 do
#            //Access board
#            SetTestBoardFIFO(value, ch, 1, StartDlyR, alct_dly, tb_dly)
#            SetFIFOReadWrite
#            ReadFIFO(vals,num,cntrs)
#
#            //Check counters and increment
#            ChannelsCntr := 0
#            for i:=0 to 15 do
#                if (cntrs[i] = 0) and ((value and (1 shl i))>0) 
#                    Inc(ChannelsCntr)
#
#                //Check if time bin is found
#                if(ChannelsCntr = num_dly_ch) 
#                    StartDlyR_f := StartDlyR
#                    break
#
#            if(ChannelsCntr = num_dly_ch) 
#                Result := True
#            else
#                Result := False
#
#
#def FindStartDlyF_tmp(var StartDlyF_f: integer StartDly: integer; value: integer; ch: integer; alct_dly: integer; num: integer): boolean
#var
#    size, i, num_dly_ch, ChannelsCntr, tb_dly, StartDlyF: integer
#    cntrs : array of byte
#    vals : array of word
#    SetLength(vals, num)
#    SetLength(cntrs, 16)
#    tb_dly := 0
#    for i:=0 to 15 do
#        if ((value and (1 shl i))>0) 
#            Inc(num_dly_ch)
#
#        for StartDlyF := StartDly+1 to 15 do
#            //Access board
#            SetTestBoardFIFO(value, ch, 1, StartDlyF, alct_dly, tb_dly)
#            SetFIFOReadWrite
#            ReadFIFO(vals,num,cntrs)
#
#            //Check counters and increment
#            ChannelsCntr := 0
#            for i:=0 to 15 do
#                if (cntrs[i] = 0) and ((value and (1 shl i))>0) 
#                    Inc(ChannelsCntr)
#
#                //Check if time bin is found
#                if(ChannelsCntr = num_dly_ch) 
#                    StartDlyF_f := StartDlyF
#                    break
#
#            if(ChannelsCntr = num_dly_ch) 
#                Result := True
#            else
#                Result := False
#
#
#def FindStartDlyF(var StartDlyF_f: integer value: integer; ch: integer; alct_dly: integer; num: integer): boolean
#var
#    size, i, num_dly_ch, ChannelsCntr, tb_dly, StartDlyF: integer
#    cntrs : array of byte
#    vals : array of word
#    SetLength(vals, num)
#    SetLength(cntrs, 16)
#    ChannelsCntr := 0
#    tb_dly := 0
#    for i:=0 to 15 do
#        if ((value and (1 shl i))>0) 
#            Inc(num_dly_ch)
#
#        for StartDlyF := StartDlyF_f-1 downto 2 do
#            //Access board
#            SetTestBoardFIFO(value, ch, 1, StartDlyF, alct_dly, tb_dly)
#            SetFIFOReadWrite
#            ReadFIFO(vals,num,cntrs)
#
#            //Check counters and increment
#            ChannelsCntr := 0
#            for i:=0 to 15 do
#                if (cntrs[i] <> 0) and ((value and (1 shl i))>0) 
#                    Inc(ChannelsCntr)
#
#                //Check if time bin is found
#                if(ChannelsCntr = num_dly_ch) 
#                    StartDlyF_f := StartDlyF
#                    break
#
#            if(ChannelsCntr = num_dly_ch) 
#                Result := True
#            else
#                Result := False
#        }
