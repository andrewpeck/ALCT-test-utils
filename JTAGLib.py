from LPTJTAGLib import *
ActiveHW = 1

IR_REG = 0
DR_REG = 1
modulename = '"ppdev"'
jtagdevice = '/dev/jtag'

def open_jtag():
    ActiveHW = openLPTJTAG()

def close_jtag():
    ActiveHW = closeLPTJTAG()

def set_chain(Chan):
    if ActiveHW: setchainLPTJTAG(Chan)

def reset_jtag():
    if ActiveHW: resetLPTJTAG()

def enable_jtag():
    if ActiveHW: enableLPTJTAG()

def idle_jtag():
    if ActiveHW: idleLPTJTAG()

def rti_jtag():
    if ActiveHW: rtiLPTJTAG()

def oneclock_jtag():
     if ActiveHW: oneclockLPTJTAG()

def TMS_High(): 
    if ActiveHW: TMSHighLPTJTAG()

def TMS_Low(): 
     if ActiveHW: TMSLowLPTJTAG()

def lights_jtag(): 
    if ActiveHW: lightsLPTJTAG()

def jtag_io(tms_, tdi_): 
    tdo=jtagioLPTJTAG(tms_, tdi_)
    return(tdo)

# Write JTAG Instruction Register 
def WriteIR(IR, IRSize):
    #arLen = ((IRSize-1) // 8) + 1
    #arIR = []
    #for i in range(arLen): 
    #    arIR.append (0xFF & (IR >> i*8))
    IR = IOExchange(IR, IRSize, IR_REG)
    return(IR)

# Write JTAG Data Register
def WriteDR(DR, DRSize):
    #arLen = ((DRSize-1) // 8) + 1
    #arDR = []
    #for i in range(arLen): 
    #    arDR.append (0xFF & (DR >> i*8))
    DR = IOExchange(DR, DRSize, DR_REG)
    return(DR)

# Read JTAG Data Register
def ReadDR(DR, DRSize):
    #arLen = ((DRSize-1) // 8) + 1
    #arDR = []
    #for i in range(arLen): 
    #    arDR.append (0xFF & (DR >> i*8))
    DR = IOExchange(DR, DRSize, DR_REG)
    return(DR)

def ShiftData(Data, DataSize, sendtms):
    result = 0

    if (DataSize < 0 or DataSize >32):
        return(0)
    for i in range(1,DataSize+1):
        #set TMS value
        if (sendtms) and (i==DataSize):
           tms = 0x01
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

def IOExchange(Send, DataSize, RegType):
    ChunkSize   = 8
    nChunks     = ( abs(DataSize-1)//ChunkSize) + 1
    Recv=0
    
    if (DataSize <= 0): 
        return(0)

    if (RegType == IR_REG): 
        StartIRShift()
    elif (RegType == DR_REG): 
        StartDRShift()
    
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
    #print(Recv)
    return (Recv)

def StartIRShift():
    StartIRShiftLPTJTAG()

def StartDRShift():
    StartDRShiftLPTJTAG()

def ExitIRShift():
    ExitIRShiftLPTJTAG()

def ExitDRShift(): 
    ExitDRShiftLPTJTAG()



