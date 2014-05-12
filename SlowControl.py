import time

from JTAGLib     import *
from LPTJTAGLib  import *
from ALCT        import *
from Common      import Now
from Common      import Printer

import sys

# Read Slow Control or Mezzanine FPGA ID Codes
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

# Read Board Silicon Serial Numbers 
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
    
# Generates tuple from idcode 
def StrToIDCode(idstr): 
    id = alct_idreg()
    if (len(idstr) <= 64): 
        id.chip     = 0xF    & (idcode)
        id.version  = 0xF    & (idcode >> 4)
        id.year     = 0xFFFF & (idcode >> 8)
        id.day      = 0xFF   & (idcode >> 24)
        id.month    = 0xFF   & (idcode >> 32)
    return(id)

# Set AFEB Threshold (value from 0-255)
# Sets threshold in ADC counts
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

# Returns AFEB Threshold on channel ch
# Returns value in ADC Counts (0-1023)
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

# Read ALCT board 12 bit voltage monitoring 
# Returns value in ADC counts (0-1023)
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

# Read ALCT board 12 bit current monitoring
# Returns value in ADC counts (0-1023)
def ReadCurrentADC(chan):
    SetChain(SLOW_CTL)
    DRlength = 11
    data = 0
    
    for i in range(4):
        data = data | ((((chan+2) >> i) & 0x1) << (3-i))
        
    for i in range(0,3):
        WriteIR(0x12, SC_IR)
        read = ReadDR(data, DRlength)

    result=FlipDR(read,DRlength)
    
    return(result)

# Read on board temperature sensor
# Returns value in ADC counts (0-1023)
def ReadTemperatureADC(): 
    DRlength = 11
    for i in range(3): 
        WriteIR(0x12, SC_IR)
        read = ReadDR(0x5, DRlength)

    result=FlipDR(read,DRlength)
    return(result)

# Read on board temperature sensor
# Returns value in degrees C
def ReadTemperature(): 
    result = ReadTemperatureADC()*arTemperature.coef-50
    return(result)

# Checks All board Thresholds
# Optional depth argument allows for a quick scan
# Only the modulo of the depth will be checked
# e.g. depth=1 checks all thresholds
#      depth=17 will check 0,17,34,...etc
def CheckThresholds(NUM_AFEBS,depth=1): 
    print("Checking AFEB Thresholds") 
    CurrErrs=0
    for afeb in range(NUM_AFEBS): 
        if afeb !=0: print("")
        for thresh in range(256): 
            if thresh%depth == 0: 
                write=thresh
                SetThreshold(afeb,write)
                read = ReadThreshold(afeb)/4.0
                output=("\t AFEB #%02i: Write=%03i Read=%03.0f" % (afeb,write,read) ) 
                Printer(output)
                if abs(write-read)>ThreshToler: 
                    print("\nERROR in AFEB #%02i: Write=%03i Read=%03.0f" % (afeb,write,read) ) 
                    CurrErrs +=1

    if CurrErrs==0: 
        print('\n\t ====> Passed')
        return(0)
    else: 
        print('\t ====> Failed Thresholds Quick Test with %i Errors' % CurrErrs)
        return(1)

# Checks ALCT-AFEB standby register
def CheckStandbyRegister(): 
    print("Checking Standby Register")
    CurrErrs = 0
    for i in range(7): 
        sendval = 0x30 | (i & 0x0f)
        SetGroupStandbyReg(i, sendval)
        readval = ReadGroupStandbyReg(i)
        if readval != sendval: 
            CurrErrs = CurrErrs+1
            print('Error: Standby Register for Wire Group #%i send=%02X read=%02X' % ((i+1),sendval,readval))

    if CurrErrs==0: 
        print('\t ====> Passed')
        return(0)
    else: 
        print('\t ====> Failed Standby Register Test with %i Errors' % CurrErrs)
        return(1)

# Checks Test Pulse Down register
def CheckTestPulsePowerDown(): 
    print('Checking Test Pulse Power Down')
    CurrErrs = 0
    sendval = 0
    SetTestPulsePower(sendval)
    readval = ReadTestPulsePower()
    if readval != sendval: 
        print('\t Error: Test Pulse Power Down send=%02X read=%02X' % (sendval,readval))
        CurrErrs+=1

    if CurrErrs==0: 
        print('\t ====> Passed')
        return(0)
    else: 
        print('\t ====> Failed Test Pulse Power Down Test with %i Errors' % CurrErrs)
        return(1)

# Checks Test Pulse Up register
def CheckTestPulsePowerUp(): 
    print('Checking Test Pulse Power Up')
    CurrErrs = 0
    sendval = 0
    SetTestPulsePower(sendval)
    readval = ReadTestPulsePower()
    if readval != sendval: 
        print('Error: Test Pulse Power Up send=%02X read=%02X' % (sendval,readval))
        CurrErrs += 1

    if CurrErrs==0: 
        print('\t ====> Passed')
        return(0)
    else: 
        print('\t ====> Failed Test Pulse Power Up Test with %i Errors' % CurrErrs)
        return(1)

def CheckTestPulseWireGroupMask(): 
    print('Checking Test Pulse Wire Group Mask')
    CurrErrs = 0
    sendval = 0
    for sendval in range (0x7F+1): 
        SetTestPulseWireGroupMask(sendval)
        readval = ReadTestPulseWireGroupMask()
        if readval != sendval: 
            print('\t Error: Test Pulse Wire Group Mask send=%02X read=%02X' % (sendval,readval))
            CurrErrs += 1
    if CurrErrs==0: 
        print('\t ====> Passed')
        return(0)
    else: 
        print('\t ====> Failed Test Pulse Wire Group Mask Test with %i Errors' % CurrErrs)
        return(1)

def CheckTestPulseStripLayerMask(): 
    print('Checking Test Pulse Strip Layer Mask')
    CurrErrs = 0
    for sendval in range(0x3F+1): 
        SetTestPulseWireGroupMask(sendval)
        readval = ReadTestPulseWireGroupMask()
        if readval != sendval:
            print('\t Error: Test Pulse Strip Layer Mask send=%02X read=%02X' % (sendval,readval))
            CurrErrs += 1
    if CurrErrs==0: 
        print('\t ====> Passed')
        return(0)
    else: 
        print('\t ====> Failed Test Pulse Wire Group Mask Test with %i Errors' % CurrErrs)
        return(1)

# Automatically checks all voltages for a given alct type
def CheckVoltages(alcttype): 
    print('Checking Voltages')
    CurrErrs=0
    for i in range(alct[alcttype].pwrchans): 
        readval = ReadVoltageADC(i)
        voltage = readval * arVoltages[i].coef
        toler   = arVoltages[i].toler
        ref     = arVoltages[i].refval

        if abs(voltage-ref) > toler: 
            CurrErrs+=1
            print("\t Fail", end='')
        else: 
            print("\t Pass ", end='')

        print("\t %s \tread=%.03f expect=%.03f +- %0.03f" % (arVoltages[i].ref, voltage, ref, toler))

    if CurrErrs==0: 
        print('\t ====> Passed')
        return(0)
    else: 
        print('\t ====> Failed Voltage Test with %i Errors' % CurrErrs)
        return(1)

# Automatically checks all currents for a given alct type
def CheckCurrents(alcttype): 
    print('Checking Currents')
    CurrErrs=0
    for i in range(alct[alcttype].pwrchans): 
        readval = ReadCurrentADC(i)
        current = readval * arCurrents[i].coef
        toler   = arCurrents[i].toler

        if alcttype==0:  # ALCT 288
            ref = arCurrents[i].ref288
        if alcttype==1:  # ALCT 384
            ref = arCurrents[i].ref384
        if alcttype==2:  # ALCT 672
            ref = arCurrents[i].ref672

        if abs(current-ref) > toler: 
            CurrErrs+=1
            print("\t Fail", end='')
        else: 
            print("\t Pass ", end='')

        print("\t %s \tread=%.03f expect=%.03f +- %0.03f" % (arCurrents[i].ref, readval*arCurrents[i].coef, arCurrents[i].refval, arCurrents[i].toler))

    if CurrErrs==0: 
        print('\t ====> Passed')
        return(0)
    else: 
        print('\t ====> Failed Current Test with %i Errors' % CurrErrs)
        return(1)
        
# Checks temperature against reference (should be close to ambient)
def CheckTemperature(): 
    print('Checking Temperature')
    CurrErrs=0
    readval = ReadTemperatureADC()
    temp = (readval * arTemperature.coef)-50
    if not (abs(temp-arTemperature.refval) < arTemperature.toler): 
        CurrErrs+=1
        print("Error: ", end='')
    print("\t %s read=%.03f expect=%.03f +- %0.03f" % (arTemperature.ref, temp, arTemperature.refval, arTemperature.toler))

    if CurrErrs==0: 
        print('\t ====> Passed')
        return(0)
    else: 
        print('\t ====> Failed Current Test with %i Errors' % CurrErrs)
        return(1)
        
# Runs an automatic self-test of Slow Control Functions
# Should have _Normal_ ALCT Firmware Installed for Test
# Other firmwares will work but have different current/voltage requirements
def SelfTest(alcttype):
    CurrErrs = 0
    Errs    = 0
    SetChain(SLOW_CTL)

    print("\n%s> Start Slow Control Self Test\n" % Now()) 
    Errs += CheckVoltages(alcttype)
    Errs += CheckCurrents(alcttype)
    Errs += CheckTemperature()
    Errs += CheckThresholds(alct[alcttype].groups*6,17)
    Errs += CheckStandbyRegister()
    Errs += CheckTestPulsePowerDown() 
    Errs += CheckTestPulsePowerUp() 
    Errs += CheckTestPulseWireGroupMask()
    SetStandbyReg(0) #Turn Off All AFEBs

    if Errs>0: 
        print('\nSlow Control Self Test Failed with %i Failed Subtests' % Errs)
    else: 
        print('\nSlow Control Self Test Finished Without Errors')

    k=input("\n<cr> to return to menu: ")
