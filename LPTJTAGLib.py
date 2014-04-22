import ctypes

base_adr    = 0x378
status_adr  = base_adr + 0x1
ctrl_adr    = base_adr + 0x2

TDI         = 0x01
TCK         = 0x02
TMS         = 0x04
TDITMS      = 0x05
TCKTMS      = 0x06
notTCKTMS   = 0xF9
TDO         = 0x10
TRST        = 0x04
STRB        = 0x01


def GetPortByte(adr):
    return(ctypes.windll.inpout32.Inp32(adr))

def SetPortByte(adr,data):
    ctypes.windll.inpout32.Out32(adr, data)

def openLPTJTAG(TComponent):
    LPTPort = parallel.Parallel()

def closeLPTJTAG():
    return(0)

def setchainLPTJTAG(Chain):
    SetPortByte(base_adr, Chain)
    SetPortByte(ctrl_adr, 11)
    SetPortByte(ctrl_adr, 0)
    SetPortByte(base_adr, 0)

def resetLPTJTAG():  
    SetPortByte(base_adr, 0)
    SetPortByte(ctrl_adr, STRB | TRST)  # Strobe with TRST high
    SetPortByte(ctrl_adr, STRB)         # Strobe with TRST low
    SetPortByte(ctrl_adr, STRB | TRST)  # Strobe with TRST high
    SetPortByte(base_adr, 0)

def enableLPTJTAG(): 
    status = GetPortByte(ctrl_adr)
    SetPortByte(ctrl_adr, status | 0x02)

def TMSHighLPTJTAG(): 
    SetPortByte(base_adr, TMS)
    SetPortByte(base_adr, TCKTMS)
    SetPortByte(base_adr, TMS)

def TMSLowLPTJTAG(): 
    SetPortByte(base_adr, 0)
    SetPortByte(base_adr, TCK)
    SetPortByte(base_adr, 0)

def idleLPTJTAG(): 
    for i in range(5):
        TMSHighLPTJTAG()

def jtagioLPTJTAG(TMSvalue, TDIvalue, TDOvalue):
    sendbit = GetPortByte(base_adr)

    if (TDIvalue>0):
        sendbit = (sendbit | TDI)
    else:
        sendbit = (sendbit & (not TDI))

    if (TMSvalue>0):
        sendbit = (sendbit | TMS)
    else: 
        sendbit = (sendbit & (not TMS))
    sendbit = sendbit | 0x10
    SetPortByte(base_adr, sendbit)
    sendbit = sendbit | TCK
    SetPortByte(base_adr, sendbit)
    rcvbit  = GetPortByte(status_adr)
    rcvbit  = (not rcvbit) & TDO
    sendbit = sendbit & (not TCK)
    SetPortByte(base_adr, sendbit)
    if (rcvbit == TDO):
        TDOvalue = 0
    else:
        TDOvalue = 1

def ShiftDataLPTJTAG(Data, DataSize, sendtms):
    if (DataSize > 32):
        result = 0
    else:
        tmp = 0
        for i in range(DataSize): 
            jtagioLPTJTAG ( (DataSize & sendtms), (Data & 0x01), tdo)
            tmp = tmp | (( tdo & 0x01) << i )
            Data = Data >> 1
    result = tmp
    return(result)

def StartIRShiftLPTJTAG():
    jtagioLPTJTAG(0, 0, tdo)
    jtagioLPTJTAG(1, 0, tdo)
    jtagioLPTJTAG(1, 0, tdo)
    jtagioLPTJTAG(0, 0, tdo)
    jtagioLPTJTAG(0, 0, tdo)

def StartDRShiftLPTJTAG():
    jtagioLPTJTAG(0, 0, tdo)
    jtagioLPTJTAG(1, 0, tdo)
    jtagioLPTJTAG(0, 0, tdo)
    jtagioLPTJTAG(0, 0, tdo)

def ExitIRShiftLPTJTAG():
    jtagioLPTJTAG(1, 0, tdo)
    jtagioLPTJTAG(0, 0, tdo)
    jtagioLPTJTAG(0, 0, tdo)
    jtagioLPTJTAG(0, 0, tdo)

def ExitDRShiftLPTJTAG():
    jtagioLPTJTAG(1, 0, tdo)
    jtagioLPTJTAG(0, 0, tdo)
    jtagioLPTJTAG(0, 0, tdo)
    jtagioLPTJTAG(0, 0, tdo)


def ExitDRShiftLPTJTAG():
    jtagioLPTJTAG(1, 0, tdo)
    jtagioLPTJTAG(0, 0, tdo)
    jtagioLPTJTAG(0, 0, tdo)
    jtagioLPTJTAG(0, 0, tdo)
