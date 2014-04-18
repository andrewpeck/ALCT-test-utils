#if (sys.platform == win32): 
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

def closeLPTJTAG:

def setchainLPTJTAG(Chain):
    SetPortByte(base_adr, Chain)
    SetPortByte(ctrl_adr, 11)
    SetPortByte(ctrl_adr, 0)
    SetPortByte(base_adr, 0)

def resetLPTJTAG: 
    SetPortByte(base_adr, 0);
    SetPortByte(ctrl_adr, STRB | TRST);  # Strobe with TRST high
    SetPortByte(ctrl_adr, STRB);         # Strobe with TRST low
    SetPortByte(ctrl_adr, STRB | TRST);  # Strobe with TRST high
    SetPortByte(base_adr, 0);

def enableLPTJTAG:
    status = GetPortByte(ctrl_adr)
    SetPortByte(ctrl_adr, status | 0x02);

def TMSHighLPTJTAG:
    SetPortByte(base_adr, TMS)
    SetPortByte(base_adr, TCKTMS);
    SetPortByte(base_adr, TMS);

def TMSLowLPTJTAG:
    SetPortByte(base_adr, 0);
    SetPortByte(base_adr, TCK);
    SetPortByte(base_adr, 0);

def idleLPTJTAG:
    for i in range(5):
        TMSHighLPTJTAG()

def jtagioLPTJTAG(TMSvalue, TDIvalue, TDOvalue):
    sendbit = GetPortByte(base_adr)

    if (TDIvalue>0):
        sendbit = (sendbit | TDI)
    else:
        sendbit = (sendbit & (!TDI))

    if (TMSvalue>0):
        sendbit = (sendbit | TMS)
    else: 
        sendbit = (sendbit & (!TMS));

    sendbit = sendbit | 0x10
    SetPortByte(base_adr, sendbit)
    sendbit = sendbit | TCK;
    SetPortByte(base_adr, sendbit)
    rcvbit  = GetPortByte(status_adr);
    rcvbit  = (!rcvbit) & TDO;
    sendbit = sendbit & (!TCK);
    SetPortByte(base_adr, sendbit)
    if (rcvbit == TDO):
        TDOvalue = 0
    else:
        TDOvalue = 1

def ShiftDataLPTJTAG(Data, DataSize, sendtms):
    if (DataSize > 32)
        result = 0
    else
begin
    tmp := 0;

    for i:=1 to DataSize do
    begin
        jtagioLPTJTAG( byte ((i = DataSize) and sendtms), byte (Data and $01), tdo);
        tmp := tmp or ( (Longword (tdo and $01)) shl (i-1) );
        Data := Data shr 1;
    end;

    Result := tmp;
end;
end;

procedure StartIRShiftLPTJTAG();
var
    tdo:    byte;
begin
    jtagioLPTJTAG(0, 0, tdo);
    jtagioLPTJTAG(1, 0, tdo);
    jtagioLPTJTAG(1, 0, tdo);
    jtagioLPTJTAG(0, 0, tdo);
    jtagioLPTJTAG(0, 0, tdo);
end;

procedure StartDRShiftLPTJTAG();
var
    tdo:    byte;
begin
    jtagioLPTJTAG(0, 0, tdo);
    jtagioLPTJTAG(1, 0, tdo);
    jtagioLPTJTAG(0, 0, tdo);
    jtagioLPTJTAG(0, 0, tdo);
end;

procedure ExitIRShiftLPTJTAG();
var
    tdo:    byte;
begin
    jtagioLPTJTAG(1, 0, tdo);
    jtagioLPTJTAG(0, 0, tdo);
    jtagioLPTJTAG(0, 0, tdo);
    jtagioLPTJTAG(0, 0, tdo);
end;

procedure ExitDRShiftLPTJTAG();
var
    tdo:    byte;
begin
    jtagioLPTJTAG(1, 0, tdo);
    jtagioLPTJTAG(0, 0, tdo);
    jtagioLPTJTAG(0, 0, tdo);
    jtagioLPTJTAG(0, 0, tdo);
end;


end.
