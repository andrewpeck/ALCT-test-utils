#!/usr/bin/env python3

#-------------------------------------------------------------------------------
# LPT JTAG Driver Built around inpout32.dll
# 04/22/2014 Driver written around inpout32.dll, for Windows only 
#            But it DOES supposedly work with windows 7, as well as with 
#            64 bit machines (using the appropriate version of inpout32.dll
# 08/26/2014 Updated to work also with Linux through the portio module.. yay. 
#
#-------------------------------------------------------------------------------

#-Imports-----------------------------------------------------------------------
import os
if os.name == 'posix': 
    import portio
if os.name == 'nt':
    import ctypes

#-Register Definitions----------------------------------------------------------
# LPT Addresses
BASE_ADR    = 0x378
STATUS_ADR  = BASE_ADR + 0x1
CTRL_ADR    = BASE_ADR + 0x2

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
    if   os.name == 'nt':
        return(ctypes.windll.inpout32.Inp32(adr))
    elif os.name == 'posix' : 
        if os.getuid():
            #print('Need root permissions for direct port access')
            return(0xFF)
        else: 
            return(portio.inp(adr))
    else: 
        return(0xFF)

# Writes Byte to LPT Port
def SetPortByte(adr,data):
    if   os.name == 'nt':
        ctypes.windll.inpout32.Out32(adr, data)
    if os.name == 'posix':
        if (not os.getuid()):
            portio.outb(data,adr)
        

# Legacy function
#def openLPTJTAG():
#    return(0)

# Legacy function
#def closeLPTJTAG():
#    return(-1)

# Set JTAG Chain
def setchainLPTJTAG(Chain):
    SetPortByte(BASE_ADR, Chain)
    SetPortByte(CTRL_ADR, 11)
    SetPortByte(CTRL_ADR, 0)
    SetPortByte(BASE_ADR, 0)

# Send JTAG Test Logic Reset
def resetLPTJTAG():  
    SetPortByte(BASE_ADR, 0)
    SetPortByte(CTRL_ADR, STRB | TRST)  # Strobe with TRST high
    SetPortByte(CTRL_ADR, STRB)         # Strobe with TRST low
    SetPortByte(CTRL_ADR, STRB | TRST)  # Strobe with TRST high
    SetPortByte(BASE_ADR, 0)

def enableLPTJTAG(): 
    status = GetPortByte(CTRL_ADR)
    SetPortByte(CTRL_ADR, status | 0x02)

# Writes a 1 to TMS
def TMSHighLPTJTAG(): 
    SetPortByte(BASE_ADR, TMS)
    SetPortByte(BASE_ADR, TCK | TMS)
    SetPortByte(BASE_ADR, TMS)

# Writes a 0 to TMS
def TMSLowLPTJTAG(): 
    SetPortByte(BASE_ADR, 0)
    SetPortByte(BASE_ADR, TCK)
    SetPortByte(BASE_ADR, 0)

def idleLPTJTAG(): 
    for i in range(5):
        TMSHighLPTJTAG()

# Writes a TMS and TDI value, returns TDO
def jtagioLPTJTAG(TMSvalue, TDIvalue):
    # Read Current Port Data
    sendbyte = GetPortByte(BASE_ADR)


    # choose TDI Bit
    sendbyte = sendbyte & ~TDI
    if (TDIvalue):
        sendbyte = sendbyte | TDI

    # choose TMS Bit
    sendbyte = sendbyte & ~TMS
    if (TMSvalue):
        sendbyte = sendbyte | TMS

    # Set TDO high for some reason?
    sendbyte = sendbyte | TDO

    # Write data to port
    SetPortByte(BASE_ADR, sendbyte)

    # Clock rise
    sendbyte = sendbyte | TCK
    SetPortByte(BASE_ADR, sendbyte)

    # Read data from port
    rcvbit  = GetPortByte(STATUS_ADR)

    # Extract TDO Bit
    TDOvalue = (rcvbit & TDO) > 0

    # Clock fall
    sendbyte = sendbyte & (~TCK)
    SetPortByte(BASE_ADR, sendbyte)
        
    return(TDOvalue)

# Starts an Instruction Register Shift
def StartIRShiftLPTJTAG():
    jtagioLPTJTAG (0,0)
    jtagioLPTJTAG (1,0)
    jtagioLPTJTAG (1,0)
    jtagioLPTJTAG (0,0)
    jtagioLPTJTAG (0,0)

# Finishes an Instruction Register Shift
def ExitIRShiftLPTJTAG():
    jtagioLPTJTAG (1,0)
    jtagioLPTJTAG (0,0)
    jtagioLPTJTAG (0,0)
    jtagioLPTJTAG (0,0)

# Starts a Data Register Shift
def StartDRShiftLPTJTAG():
    jtagioLPTJTAG (0,0)
    jtagioLPTJTAG (1,0)
    jtagioLPTJTAG (0,0)
    jtagioLPTJTAG (0,0)

# Finishes a Data Register Shift
def ExitDRShiftLPTJTAG():
    jtagioLPTJTAG (1,0)
    jtagioLPTJTAG (0,0)
    jtagioLPTJTAG (0,0)
    jtagioLPTJTAG (0,0)
