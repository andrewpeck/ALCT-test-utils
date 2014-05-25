################################################################################
# JTAGLib.py -- Platform agnostic wrapper around the JTAG IO device of choice
#               ALL IO in other modules should be done through this wrapper!! 
################################################################################

import LPTJTAGLib
import os
import sys

IR_REG = 0
DR_REG = 1

def open_jtag():
    if os.name == 'nt': 
        LPTJTAGLib.openLPTJTAG()

def close_jtag():
    if os.name == 'nt': 
        LPTJTAGLib.closeLPTJTAG()

def set_chain(Chan):
    if os.name == 'nt': 
        LPTJTAGLib.setchainLPTJTAG(Chan)

def reset_jtag():
    if os.name == 'nt': 
        LPTJTAGLib.resetLPTJTAG()

def enable_jtag():
    if os.name == 'nt': 
        LPTJTAGLib.enableLPTJTAG()

def idle_jtag():
    if os.name == 'nt': 
        LPTJTAGLib.idleLPTJTAG()

def rti_jtag():
    if os.name == 'nt': 
        LPTJTAGLib.rtiLPTJTAG()

def oneclock_jtag():
    if os.name == 'nt': 
        LPTJTAGLib.oneclockLPTJTAG()

def TMS_High(): 
    if os.name == 'nt': 
        LPTJTAGLib.TMSHighLPTJTAG()

def TMS_Low(): 
    if os.name == 'nt': 
        LPTJTAGLib.TMSLowLPTJTAG()

def lights_jtag(): 
    if os.name == 'nt': 
        LPTJTAGLib.lightsLPTJTAG()

def jtag_io(tms_, tdi_): 
    if os.name == 'nt': 
        tdo=LPTJTAGLib.jtagioLPTJTAG(tms_, tdi_)
        return(tdo)

def StartIRShift():
    if os.name == 'nt': 
        LPTJTAGLib.StartIRShiftLPTJTAG()

def StartDRShift():
    if os.name == 'nt': 
        LPTJTAGLib.StartDRShiftLPTJTAG()

def ExitIRShift():
    if os.name == 'nt': 
        LPTJTAGLib.ExitIRShiftLPTJTAG()

def ExitDRShift(): 
    if os.name == 'nt': 
        LPTJTAGLib.ExitDRShiftLPTJTAG()

# Write JTAG Instruction Register 
def WriteIR(IR, IRSize):

    if (IRSize is None) or (IR is None): 
        print("ERROR: Attempted to write invalid instruction register.")
        sys.exit()

    IR = IOExchange(IR, IRSize, IR_REG)
    return(IR)

# Write JTAG Data Register
def WriteDR(DR, DRSize):
    if (DRSize is None) or (DR is None): 
        print("ERROR: Attempted to write invalid data register.")
        sys.exit()

    DR = IOExchange(DR, DRSize, DR_REG)
    return(DR)

# Read JTAG Data Register
def ReadDR(DR, DRSize):
    if (DR is None) or (DRSize is None): 
        print("ERROR: Attempted to read invalid data register.")
        sys.exit()

    DR = IOExchange(DR, DRSize, DR_REG)
    return(DR)

# Shift Data into JTAG Register
def ShiftData(Data, DataSize, sendtms):
    result = 0

    # Quit if nothing is passed as data
    if (DataSize is None) or (Data is None): 
        print("ERROR: Attempted to shift invalid data.")
        sys.exit()

    # Quit if data is too large
    if (DataSize < 0 or DataSize >32):
        print("ERROR: Attempted to shift invalid sized data.")
        sys.exit()

    for i in range(1,DataSize+1):

        #set TMS value
        if (sendtms) and (i==DataSize):
           tms = 0x1
        else:
            tms = 0x00
        #set TDI value
        tdi = Data & (0x1)

        #write data
        tdo=jtag_io(tms, tdi)

        #Shift out one bit
        Data = Data >> 1

        result = result | ((tdo & 0x01) << (i-1))

    return(result)

################################################################################
# Sends and receives JTAG data... wrapper to to Start IR/DR Shift, Shift in data
# while reading from TDO.. exit IR/DR shift. Returns TDO data. 
################################################################################
def IOExchange(Send, DataSize, RegType):
    
    if (DataSize is None) or (Send is None): 
        print("ERROR: Invalid data. Error reading or board disconnected!")
        sys.exit()

    # We shift in 8 bit words 
    ChunkSize   = 8

    # Number of words needed to shift entire data 
    nChunks     = ( abs(DataSize-1)//ChunkSize) + 1

    if (RegType == IR_REG): 
        StartIRShift()
    elif (RegType == DR_REG): 
        StartDRShift()
    
    Recv=0 # Received Data
    for i in range(nChunks):
        #print("nchunks loop = %i" % i)
        if (DataSize > ChunkSize*i):
            if (DataSize - ChunkSize*i) > ChunkSize:
                tdo = 0xFF & ShiftData(0xFF & (Send >> 8*i), ChunkSize, False)
            else:
                tdo = 0xFF & ShiftData(0xFF & (Send >> 8*i), DataSize - ChunkSize*i, True)

        Recv = Recv | tdo << (8*i)
    
    if RegType == IR_REG: 
        ExitIRShift()
    else: 
        ExitDRShift()
    return (Recv)
