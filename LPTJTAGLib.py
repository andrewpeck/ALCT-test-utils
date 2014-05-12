################################################################################
# LPT JTAG Driver Built around inpout32.dll
################################################################################
import ctypes

# LPT Addresses
base_adr    = 0x378
status_adr  = base_adr + 0x1
ctrl_adr    = base_adr + 0x2

# JTAG-to-LPT Pin Mapping
TDI         = 0x01
TCK         = 0x02
TMS         = 0x04
TDITMS      = 0x05
TCKTMS      = 0x06
notTCKTMS   = 0xF9
TDO         = 0x10
TRST        = 0x04
STRB        = 0x01


# Reads Byte off LPT Port
def GetPortByte(adr):
    return(ctypes.windll.inpout32.Inp32(adr))

# Writes Byte to LPT Port
def SetPortByte(adr,data):
    ctypes.windll.inpout32.Out32(adr, data)

# Legacy function
def openLPTJTAG():
    return(0)

# Legacy function
def closeLPTJTAG():
    return(-1)

# Set JTAG Chain
def setchainLPTJTAG(Chain):
    SetPortByte(base_adr, Chain)
    SetPortByte(ctrl_adr, 11)
    SetPortByte(ctrl_adr, 0)
    SetPortByte(base_adr, 0)

# Send JTAG Test Logic Reset
def resetLPTJTAG():  
    SetPortByte(base_adr, 0)
    SetPortByte(ctrl_adr, STRB | TRST)  # Strobe with TRST high
    SetPortByte(ctrl_adr, STRB)         # Strobe with TRST low
    SetPortByte(ctrl_adr, STRB | TRST)  # Strobe with TRST high
    SetPortByte(base_adr, 0)

def enableLPTJTAG(): 
    status = GetPortByte(ctrl_adr)
    SetPortByte(ctrl_adr, status | 0x02)

# Writes a 1 to TMS
def TMSHighLPTJTAG(): 
    SetPortByte(base_adr, TMS)
    SetPortByte(base_adr, TCK | TMS)
    SetPortByte(base_adr, TMS)

# Writes a 0 to TMS
def TMSLowLPTJTAG(): 
    SetPortByte(base_adr, 0)
    SetPortByte(base_adr, TCK)
    SetPortByte(base_adr, 0)

def idleLPTJTAG(): 
    for i in range(5):
        TMSHighLPTJTAG()

# Writes a TMS and TDI value, returns TDO
def jtagioLPTJTAG(TMSvalue, TDIvalue):
    # Read Current Port Data
    sendbit = GetPortByte(base_adr)
   
    # choose TDI Bit
    if (TDIvalue>0):
        sendbit = sendbit | TDI
    else:
        sendbit = sendbit & ~TDI

    # choose TMS Bit
    if (TMSvalue>0):
        sendbit = sendbit | TMS
    else: 
        sendbit = sendbit & ~TMS

    # Don't Change TDO bit
    sendbit = sendbit | TDO

    # Write data to port
    SetPortByte(base_adr, sendbit)

    # Clock rise
    sendbit = sendbit | TCK
    SetPortByte(base_adr, sendbit)

    # Read data from port
    rcvbit  = GetPortByte(status_adr)

    # Extract TDO Bit
    rcvbit  = rcvbit & TDO
    rcvbit  = not rcvbit
    rcvbit  = rcvbit & 0xFF
    TDOvalue = not rcvbit

    # Clock fall
    sendbit = sendbit & (~TCK)
    SetPortByte(base_adr, sendbit)
        
    return(TDOvalue)

# Starts an Instruction Register Shift
def StartIRShiftLPTJTAG():
    tdo=jtagioLPTJTAG(0, 0)
    tdo=jtagioLPTJTAG(1, 0)
    tdo=jtagioLPTJTAG(1, 0)
    tdo=jtagioLPTJTAG(0, 0)
    tdo=jtagioLPTJTAG(0, 0)

# Finishes an Instruction Register Shift
def ExitIRShiftLPTJTAG():
    tdo=jtagioLPTJTAG(1, 0)
    tdo=jtagioLPTJTAG(0, 0)
    tdo=jtagioLPTJTAG(0, 0)
    tdo=jtagioLPTJTAG(0, 0)

# Starts a Data Register Shift
def StartDRShiftLPTJTAG():
    tdo=jtagioLPTJTAG(0, 0)
    tdo=jtagioLPTJTAG(1, 0)
    tdo=jtagioLPTJTAG(0, 0)
    tdo=jtagioLPTJTAG(0, 0)

# Finishes a Data Register Shift
def ExitDRShiftLPTJTAG():
    tdo=jtagioLPTJTAG(1, 0)
    tdo=jtagioLPTJTAG(0, 0)
    tdo=jtagioLPTJTAG(0, 0)
    tdo=jtagioLPTJTAG(0, 0)
