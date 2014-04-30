import time
from JTAGLib     import *
from LPTJTAGLib  import *
from ALCT        import *
from common     import Now
from common     import Printer
import sys

#done
def ReadIDCode (alct_ctl): 
    if (alct_ctl == SLOW_CTL):
        SetChain(SLOW_CTL) # Slow Control Control Chain
        WriteIR(0, SC_IR)
        return(ReadDR(0x00, CTRL_SC_ID_DR_SIZE)) 
    elif (alct_ctl == FAST_CTL):
        SetChain(4) # Virtex Control Chain
        WriteIR(0, V_IR)
        return(ReadDR(0x00, USER_V_ID_DR_SIZE))
    else: 
        return(0)

#done
def ReadBoardSN(board_type):
    SetChain(4) # Virtex Control Chain
    
    if board_type == BOARD_SN: 
        cr_str    = ReadRegister(RdCfg)
        cr_str = cr_str & 0x0fffffffffffffffff
        
        #cr_str[1] = 0
        #cr_str = '0020A03806B1193FC1'
        
        WriteRegister(WrCfg, cr_str)
    elif board_type == MEZAN_SN:
        cr_str = ReadRegister(RdCfg)
        cr_str = cr_str | 0x100000000000000000
        #cr_str[1] = '1'
        #cr_str = '1020A03806B1193FC1'
        WriteRegister(WrCfg, cr_str)
    else: 
        return(0)

    # reset DS2401
    WriteIR (SNreset, V_IR)
    sleep(0.001)
    WriteIR (SNwrite1, V_IR)
    sleep(0.050)

    # write read command 0x33
    WriteIR (SNwrite1, V_IR)
    sleep(0.001)
    WriteIR (SNwrite1, V_IR) 
    sleep(0.001)
    WriteIR (SNwrite0, V_IR) 
    sleep(0.001)
    WriteIR (SNwrite0, V_IR) 
    sleep(0.001)
    WriteIR (SNwrite1, V_IR) 
    sleep(0.001)
    WriteIR (SNwrite1, V_IR) 
    sleep(0.001)
    WriteIR (SNwrite0, V_IR) 
    sleep(0.001)
    WriteIR (SNwrite0, V_IR) 
    sleep(0.001)

    #read 64 bits of SN bit by bit
    result=0
    for i in range(64):
        WriteIR(SNRead,V_IR)
        bit = ReadDR(0,1) & 0x1
        result = result | bit << i
    return(result)
    
def StrToIDCode(idstr): 
    id = alct_idreg()
    if (len(idstr) <= 64): 
        id.chip     = 0xF    & (idcode)
        id.version  = 0xF    & (idcode >> 4)
        id.year     = 0xFFFF & (idcode >> 8)
        id.day      = 0xFF   & (idcode >> 24)
        id.month    = 0xFF   & (idcode >> 32)
    return(id)

#done
def SetThreshold(ch, value):
    SetChain(0x0)
    DRlength  = 12
    data    = 0
    realch  = ch
    if (ch >= 33):
        realch = ch+3
    time.sleep(0.01)     #sleep 10 ms
    value = value & 0xFF
    value = value | (( realch % 12) << 8)
    
    for i in range(DRlength):
        data = data | (((value >> i)  & 0x1) << (11-i))

    WriteIR(0xFF & (0x8+(realch // 12)), SC_IR)
    WriteDR(data & 0xFFF, DRlength)

#done
def ReadThreshold(ch):
    SetChain(SLOW_CTL)
    DRLength = 11
    result = 0
    data = 0  

    channel = 0xFF & arADCChannel[ch]
    chip    = 0xFF & (0x10 + arADCChip[ch])
    

    for i in range(4):
        data = 0xFFF & (data | (((channel >> i) & 0x1) << (3-i)))

    time.sleep(0.01)     #sleep 10 ms

    WriteIR(chip, SC_IR)
    WriteDR(data, DRLength)

    #time.sleep(0.1)     #sleep 10 ms

    WriteIR(chip, SC_IR)
    read = ReadDR(data,DRLength)
    
    result=FlipDR(read,DRLength)
    
    return(result)

#done
def ReadVoltageADC(chan):
    SetChain(SLOW_CTL)
    DRlength = 11
    result = 0
    data = 0

    for i in range(4):
        data = data | ((((chan+6) >> i) & 0x1) << (3-i))

    data = data & 0xFFF

    for i in range(3):
        WriteIR(0x12, SC_IR)
        read = ReadDR(data, DRlength)
        
    result=FlipDR(read,DRlength)
    
    return(result)

#done
def ReadCurrentADC(chan):
    SetChain(SLOW_CTL)
    DRlength = 11
    data = 0
    
    for i in range(0,4):
        data = data | ((((chan+2) >> i) & 0x1) << (3-i))
        
    for i in range(0,3):
        WriteIR(0x12, SC_IR)
        read = ReadDR(data, DRlength)

    result=FlipDR(read,DRlength)
    
    return(result)

#done
def ReadTemperatureADC(): 
    DRlength = 11
    for i in range(3): 
        WriteIR(0x12, SC_IR)
        read = ReadDR(0x5, DRlength)

    result=FlipDR(read,DRlength)
    return(result)

#done
def ReadTemperature(): 
    result = ReadTemperatureADC()*arTemperature.coef-50
    return(result)

