from ALCT import *
import random
from common import Printer
from common import Now

def SingleCableTest(test,channel,npasses=50): 
    SetChain(arJTAGChains[3])
    errcnt      = 0
    CustomData  =0x1234
    senddata    =0x0000
    SuppressErrsSingleCable=True
    StopOnErrorSingleCable=False
    ErrCntSingleTest=50

    TestNames = ['Custom Data', 'Walking 1', 'Walking 0', 'Filling 1', 'Filling 0', 'Shifting 5s and As', 'Random Data']

    print('Running %s test on Channel %i' % (TestNames[test],channel))
    if test==0: multiple = 1
    if test==1: multiple = 16
    if test==2: multiple = 16
    if test==3: multiple = 16
    if test==4: 
        senddata    = 0xFFFF
        multiple = 16
    if test==5: multiple = 2
    if test==6: multiple = 1

    for cnt in range(npasses*multiple): 
        if test==0: senddata = CustomData                                   # 0 = Custom Data Test
        if test==1: senddata = 0x0000   |   (0xFFFF & (1 << (cnt % 16)))    # 1 = Walking 1 Test
        if test==2: senddata = 0xFFFF   & (~(0xFFFF & (1 << (cnt % 16))))   # 2 = Walking 0 Test
        if test==3:                                                         # 3 = Filling 1 Test
            if cnt%16==0: senddata=0x0001
            else: senddata = senddata | (0xFFFF & (1 << (cnt % 16)))        
        if test==4:                                                         # 4 = Filling 0 Test 
            if cnt%16 == 0: senddata=0xFFFE
            else: senddata = senddata & (~(0xFFFF & (1 << (cnt % 16))))    
        if test==5:                                                         # 5 = Shifting 5 and A
            if    ((cnt+1) % 2)==1: senddata = 0x5555
            else:                   senddata = 0xAAAA
        if test==6: senddata = random.getrandbits(16)                       # 6 = Random Data

        # Select Channel
        #WriteRegister(0x16,0x1FF & channel)
        WriteIR(0x16,V_IR)
        WriteDR(0x1FF & channel,9)

        #ReadRegister(0x15)
        WriteIR(0x15,V_IR)
        ReadDR (0x0,9)

        # Write Data
        #WriteRegister(0x18,0xFFFF & senddata)
        WriteIR(0x18,V_IR)
        WriteDR(0xFFFF & senddata,16)

        # Read Back Data
        #readdata= ReadRegister(0x17)
        WriteIR(0x17,V_IR)
        readdata = ReadDR(0x0,16)

        if readdata != senddata: 
            errcnt += 1
            #if ((not SuppressErrsSingleCable) or (SuppressErrsSingleCable and (errcnt <= ErrCntSingleTest))): 
                #print('\t ERROR: Pass #%02i Set Mask Register to 0x%04X Readback 0x%04X' % (cnt,senddata,readdata))
            if StopOnErrorSingleCable: 
                return(0)

        # Select Channel
        #WriteRegister(0x16,channel | 0x40)
        WriteIR(0x16,V_IR)
        WriteDR(0x1FF & (channel | 0x40),9)

        #WriteRegister(0x16,channel | 0x1FF) 
        WriteIR(0x16,V_IR)
        WriteDR(0x1FF & channel,9)

        #readdata = ReadRegister(0x19)
        WriteIR(0x19,V_IR)
        readdata = ReadDR(0x0,16)

        status = ('\t Pass #%02i Read=0x%04X Expect=0x%04X' % (cnt//multiple +1,readdata,senddata))
        #status = ('\t Pass #%02i: Read=%s Expect=%s' % ( cnt//multiple+1, ( bin(readdata)[2:] ).zfill(16), ( bin(senddata)[2:] ).zfill(16)))
        Printer(status)

        if readdata != senddata : 
            errcnt += 1
            if ((not SuppressErrsSingleCable) or (SuppressErrsSingleCable and (errcnt <= ErrCntSingleTest))): 
                print('\n\t ERROR: Pass #%02i Read=0x%04X Expect=0x%04X' % (cnt,readdata,senddata))
            if StopOnErrorSingleCable: 
                return(0)

    if errcnt==0: 
        print('\n\t ====> Passed')
        return(0)
    else: 
        print('\n\t ====> Failed Single Cable Test with %i Errors' % errcnt)
        return(errcnt)

def SingleCableSelfTest(): 
    print("\n%s > Starting Single Cable Automatic Test\n" % Now())
    NUM_OF_AFEBS=1
    for (channel) in range (NUM_OF_AFEBS): 
        for i in range(7):
            SingleCableTest(i,0,10)
               
