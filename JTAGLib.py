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

def jtag_io(tms_, tdi_, tdo_): 
    if ActiveHW: jtagioLPTJTAG(tms_, tdi_, tdo_)

# Write JTAG Instruction Register 
def WriteIR(IR, IRSize):
    arLen = ((IRSize-1) // 8) + 1
    arIR = []
    for i in range(arLen): 
        arIR.append (0xFF & (IR >> i*8))
    IOExchange(arIR, arIR, IRSize, IR_REG)
    return(arIR)

# Write JTAG Data Register
def WriteDR(DR, DRSize):
    arLen = ((DRSize-1) // 8) + 1
    arDR = []
    for i in range(arLen): 
        arDR.append (0xFF & (DR >> i*8))
    IOExchange(arDR, arDR, DRSize, DR_REG)
    return(arDR)

# Read JTAG Data Register
def ReadDR(DR, DRSize):
    arLen = ((DRSize-1) // 8) + 1
    arDR = []
    for i in range(arLen): 
        arDR.append (0xFF & (DR >> i*8))
    IOExchange(arDR, arDR, DRSize, DR_REG)
    return(arDR)

def ShiftData(Data, DataSize, sendtms):
    tmp = 0
    if (ActiveHW and (DataSize > 0) and (DataSize <= 32)) :
        for i in range(DataSize):
            #set TMS value
            if (sendtms): 
                tms = 0xFF & DataSize
            else: 
                tms = 0x00

            #set TDI value
            tdi = Data & 0x01

            tdo = 0

            #write data
            jtag_io(tms, tdi, tdo)

            tmp = tmp | ( (tdo & 0x01) << i )
            Data = Data >> 1
        return(tmp)
    else: 
        return 0

def IOExchange(Send, Recv, Size, RegType):
    ChunkSz = 8
    #I:  longint
    if (not ActiveHW) or (Size <= 0): 
            return(0)
    else: 
        if (RegType == IR_REG): 
            StartIRShift()
        elif (RegType == DR_REG): 
            StartDRShift()

        #for index,item in enumerate(my_list):
        for i,j in enumerate(Send):
            if (Size > ChunkSz*i): 
                if (Size - ChunkSz*i) > ChunkSz: 
                    Recv[i] = 0xFF & ShiftData(Send[i], ChunkSz, False)
                else: 
                    Recv[i] = 0xFF & ShiftData(Send[i], Size - ChunkSz*i, True)

        if RegType == IR_REG: 
            ExitIRShift()
        else: 
            ExitDRShift()
        return (Size)

def StartIRShift(): 
    tdo = 0
    jtag_io(0, 0, tdo)
    jtag_io(1, 0, tdo)
    jtag_io(1, 0, tdo)
    jtag_io(0, 0, tdo)
    jtag_io(0, 0, tdo)

def StartDRShift(): 
    tdo = 0
    jtag_io(0, 0, tdo)
    jtag_io(1, 0, tdo)
    jtag_io(0, 0, tdo)
    jtag_io(0, 0, tdo)

def ExitIRShift(): 
    tdo = 0
    jtag_io(1, 0, tdo)
    jtag_io(0, 0, tdo)
    jtag_io(0, 0, tdo)
    jtag_io(0, 0, tdo)

def ExitDRShift(): 
    tdo = 0
    jtag_io(1, 0, tdo)
    jtag_io(0, 0, tdo)
    jtag_io(0, 0, tdo)
    jtag_io(0, 0, tdo)



