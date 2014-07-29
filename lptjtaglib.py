#!/usr/bin/env python3

################################################################################
# LPT JTAG Driver Built around inpout32.dll
# Windoze only ! Sorry. 
################################################################################
import ctypes
import os

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
    if os.name == 'nt':
        return(ctypes.windll.inpout32.Inp32(adr))
    else: 
        return(0x0)

# Writes Byte to LPT Port
def SetPortByte(adr,data):
    if os.name == 'nt':
        ctypes.windll.inpout32.Out32(adr, data)

# Legacy function
def openLPTJTAG():
    return(0)

# Legacy function
def closeLPTJTAG():
    return(-1)

# Set JTAG Chain
def setchainLPTJTAG(Chain):
    if os.name == 'nt':
        SetPortByte(base_adr, Chain)
        SetPortByte(ctrl_adr, 11)
        SetPortByte(ctrl_adr, 0)
        SetPortByte(base_adr, 0)

# Send JTAG Test Logic Reset
def resetLPTJTAG():  
    if os.name == 'nt':
        SetPortByte(base_adr, 0)
        SetPortByte(ctrl_adr, STRB | TRST)  # Strobe with TRST high
        SetPortByte(ctrl_adr, STRB)         # Strobe with TRST low
        SetPortByte(ctrl_adr, STRB | TRST)  # Strobe with TRST high
        SetPortByte(base_adr, 0)

def enableLPTJTAG(): 
    if os.name == 'nt':
        status = GetPortByte(ctrl_adr)
        SetPortByte(ctrl_adr, status | 0x02)

# Writes a 1 to TMS
def TMSHighLPTJTAG(): 
    if os.name == 'nt':
        SetPortByte(base_adr, TMS)
        SetPortByte(base_adr, TCK | TMS)
        SetPortByte(base_adr, TMS)

# Writes a 0 to TMS
def TMSLowLPTJTAG(): 
    if os.name == 'nt':
        SetPortByte(base_adr, 0)
        SetPortByte(base_adr, TCK)
        SetPortByte(base_adr, 0)

def idleLPTJTAG(): 
    if os.name == 'nt':
        for i in range(5):
            TMSHighLPTJTAG()

# Writes a TMS and TDI value, returns TDO
def jtagioLPTJTAG(TMSvalue, TDIvalue):
    if os.name == 'nt':
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
    else: 
        return(0x0)

# Starts an Instruction Register Shift
def StartIRShiftLPTJTAG():
    if os.name == 'nt':
        tdo=jtagioLPTJTAG(0, 0)
        tdo=jtagioLPTJTAG(1, 0)
        tdo=jtagioLPTJTAG(1, 0)
        tdo=jtagioLPTJTAG(0, 0)
        tdo=jtagioLPTJTAG(0, 0)

# Finishes an Instruction Register Shift
def ExitIRShiftLPTJTAG():
    if os.name == 'nt':
        tdo=jtagioLPTJTAG(1, 0)
        tdo=jtagioLPTJTAG(0, 0)
        tdo=jtagioLPTJTAG(0, 0)
        tdo=jtagioLPTJTAG(0, 0)

# Starts a Data Register Shift
def StartDRShiftLPTJTAG():
    if os.name == 'nt':
        tdo=jtagioLPTJTAG(0, 0)
        tdo=jtagioLPTJTAG(1, 0)
        tdo=jtagioLPTJTAG(0, 0)
        tdo=jtagioLPTJTAG(0, 0)

# Finishes a Data Register Shift
def ExitDRShiftLPTJTAG():
    if os.name == 'nt':
        tdo=jtagioLPTJTAG(1, 0)
        tdo=jtagioLPTJTAG(0, 0)
        tdo=jtagioLPTJTAG(0, 0)
        tdo=jtagioLPTJTAG(0, 0)
