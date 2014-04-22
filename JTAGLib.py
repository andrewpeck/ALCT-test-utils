import LPTJTAGLib.py

IR_REG = 0
DR_REG = 1
modulename = '"ppdev"'
jtagdevice = '/dev/jtag'

def open_jtag:
if (!ActiveHW):
    if (!driverJTAG):
        nPort = openLPTJTAG(Owner)
        if nPort = -1 : 
            ActiveHW = False
        else :
            ActiveHW = True

def close_jtag():
    if ActiveHW:
        closeLPTJTAG()
        nPort = -1
        ActiveHW = False

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

def jtag_io(tms_, tdi_, tdo_)
    if ActiveHW: jtagioLPTJTAG(tms_, tdi_, tdo_)

# Write JTAG Instruction Register 
def WriteIR(IR, IRSize):
    arLen = ((IRSize-1) // 8) + 1
    for i in range(arLen): 
        arIR[i] = 0xFF & (IR >> i*8)
    IOExchange(arIR, arIR, IRSize, IR_REG)
    return(arIr)

# Write JTAG Data Register
def WriteDR(DR, DRSize):
    arLen = ((DRSize-1) // 8) + 1
    for i in range(arLen): 
        arDR[i] = 0xFF & (DR >> i*8)
    IOExchange(arDR, arDR, DRSize, DR_REG)
    return(arDr)

# Read JTAG Data Register
def ReadDR(DR, DRSize):
    arLen = ((DRSize-1) // 8) + 1
    for i in range(arLen): 
        arDR[i] = 0xFF & (DR >> i*8)
    IOExchange(arDR, arDR, DRSize, DR_REG)
    return(arDr)

#ShiftData(Data: Longword DataSize: byte; sendtms: boolean): Longword;
def ShiftData(Data, DataSize, sendtms):
    if ActiveHW and (DataSize > 0) and (DataSize <= 32) : 
        for i in range(DataSize):
            #set TMS value
            if (sendtms): 
                tms = 0xFF & DataSize
            else: 
                tms = 0x00

            #set TDI value
            tdi = Data & 0x01

            #write data
            jtag_io(tms, tdi, tdo)

            tmp := tmp | ( (tdo & 0x01) << i )
            Data := Data >> 1
        return(tmp)
    else: 
        return 0

def IOExchange(Send, Recv, Size, RegType):
    ChunkSz = 8
    #I:  longint
    if (!ActiveHW or (Size <= 0): 
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
                    Recv[i] = 0xFF & ShiftData(Send[i], ChunkSz, false)
                else: 
                    Recv[i] = 0xFF & ShiftData(Send[i], Size - ChunkSz*i, true)

        if RegType = IR_REG: 
            ExitIRShift()
        else: 
            ExitDRShift()
        return (size)

def StartIRShift(): 
    jtag_io(0, 0, tdo)
    jtag_io(1, 0, tdo)
    jtag_io(1, 0, tdo)
    jtag_io(0, 0, tdo)
    jtag_io(0, 0, tdo)

def StartDRShift() 
    jtag_io(0, 0, tdo)
    jtag_io(1, 0, tdo)
    jtag_io(0, 0, tdo)
    jtag_io(0, 0, tdo)

def ExitIRShift(): 
    jtag_io(1, 0, tdo)
    jtag_io(0, 0, tdo)
    jtag_io(0, 0, tdo)
    jtag_io(0, 0, tdo)

def ExitDRShift(): 
    jtag_io(1, 0, tdo)
    jtag_io(0, 0, tdo)
    jtag_io(0, 0, tdo)
    jtag_io(0, 0, tdo)



