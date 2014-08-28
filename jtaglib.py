#!/usr/bin/env python3

# ------------------------------------------------------------------------------
# Platform agnostic wrapper around the JTAG IO device of choice
# ALL IO in other modules should be done through this wrapper!!
# ------------------------------------------------------------------------------

import os
if os.name=='nt':
    BACKEND = "python"
else:
    BACKEND = "python"

if   BACKEND=="nativec": 
    import _lptjtaglib

    # system imports
    import sys

    #DEFINES
    IR_REG = 0
    DR_REG = 1

    def set_chain(chain):
        _lptjtaglib.setchain(chain)

    def StartIRShift():
        _lptjtaglib.StartIRShift()

    def StartDRShift():
        _lptjtaglib.StartDRShift()

    def ExitIRShift():
        _lptjtaglib.ExitIRShift()

    def ExitDRShift():
        _lptjtaglib.ExitDRShift()

    # Write JTAG Instruction Register
    def WriteIR(IR, IRSize):
        if (IRSize is None) or (IR is None):
            print("ERROR: Attempted to write invalid instruction register.")
            sys.exit()

        IR = _lptjtaglib.IOExchange(IR, IRSize,IR_REG)
        return(IR)

    # Write JTAG Data Register
    def WriteDR(DR, DRSize):
        if (DRSize is None) or (DR is None):
            print("ERROR: Attempted to write invalid data register.")
            sys.exit()

        DR = _lptjtaglib.IOExchange(DR, DRSize, DR_REG)
        return(DR)

    # Read JTAG Data Register
    def ReadDR(DR, DRSize):
        if (DRSize is None) or (DR is None):
            print("ERROR: Attempted to write invalid data register.")
            sys.exit()

        DR = _lptjtaglib.IOExchange(DR, DRSize, DR_REG)
        return(DR)

    # Shift Data into JTAG Register, bit-by-bit
    def ShiftData(Data, DataSize, sendtms):
        # Quit if nothing is passed as data
        if (DataSize is None) or (Data is None):
            print("ERROR: Attempted to shift invalid data.")
            sys.exit()

        # Quit if data is too large
        if (DataSize < 0 or DataSize >32):
            print("ERROR: Attempted to shift too large of data (>32 bits at a time).")
            sys.exit()
        return(lptjtaglib.ShiftData(Data, DataSize, sendtms))

    #-------------------------------------------------------------------------------
    # Sends and receives JTAG data... wrapper to to Start IR/DR Shift, Shift in data
    # while reading from TDO.. exit IR/DR shift. Returns TDO data.
    #-------------------------------------------------------------------------------
    def IOExchange(Send, DataSize, RegType):
        if (DataSize is None) or (Send is None):
            print("ERROR: attempting to write nothing to IOExchange")
            sys.exit()

        Recv = _lptjtaglib.IOExchange(Send, DataSize, RegType)
        return (Recv)

elif BACKEND=="ctypes": 
    import ctypes
    lptjtaglib = ctypes.CDLL('lptjtaglib.dll')

    # system imports
    import sys

    # local imports

    #DEFINES
    IR_REG = 0
    DR_REG = 1

    def set_chain(chain):
        lptjtaglib.setchain(chain)

    def StartIRShift():
        lptjtaglib.StartIRShift()

    def StartDRShift():
        lptjtaglib.StartDRShift()

    def ExitIRShift():
        lptjtaglib.ExitIRShift()

    def ExitDRShift():
        lptjtaglib.ExitDRShift()

    # Write JTAG Instruction Register
    def WriteIR(IR, IRSize):
        if (IRSize is None) or (IR is None):
            print("ERROR: Attempted to write invalid instruction register.")
            sys.exit()

        IR = IOExchange(IR, IRSize,IR_REG)
        return(IR)

    # Write JTAG Data Register
    def WriteDR(DR, DRSize):
        if (DRSize is None) or (DR is None):
            print("ERROR: Attempted to write invalid data register.")
            sys.exit()

        return(IOExchange(DR, DRSize, DR_REG))

    # Read JTAG Data Register
    def ReadDR(DR, DRSize):
        return(WriteDR(DR, DRSize))

    # Shift Data into JTAG Register, bit-by-bit
    def ShiftData(Data, DataSize, sendtms):
        # Quit if nothing is passed as data
        if (DataSize is None) or (Data is None):
            print("ERROR: Attempted to shift invalid data.")
            sys.exit()

        # Quit if data is too large
        if (DataSize < 0 or DataSize >32):
            print("ERROR: Attempted to shift too large of data (>32 bits at a time).")
            sys.exit()
        return(lptjtaglib.ShiftData(Data, DataSize, sendtms))

    #-------------------------------------------------------------------------------
    # Sends and receives JTAG data... wrapper to to Start IR/DR Shift, Shift in data
    # while reading from TDO.. exit IR/DR shift. Returns TDO data.
    #-------------------------------------------------------------------------------
    def IOExchange(Send, DataSize, RegType):
        #if (DataSize is None) or (Send is None):
        #    print("ERROR: attempting to write nothing to IOExchange")
        #    sys.exit()
        #return (lptjtaglib.IOExchange(Send, DataSize, RegType))

        if (DataSize is None) or (Send is None):
            print("ERROR: attempting to write nothing to IOExchange")
            sys.exit()

        # We can write 8 bits at a time
        ChunkSize   = 8

        # Number of words needed to shift entire data
        nChunks     = (abs(DataSize-1)//ChunkSize) + 1

        # instruction register or data register? 
        # initiate data shift
        if (RegType == IR_REG):
            lptjtaglib.StartIRShift()
        elif (RegType == DR_REG):
            lptjtaglib.StartDRShift()

        Recv=0 # Received Data (reconstructed Full-packet)
        tdo =0 # Test data out (byte-by-byte)

        # this whole loop can be simplified a lot.. e.g. this seems it should have the same behavior 
        # but need to test to be sure
        #for i in range(nChunks):
        #    if i==nChunks-1: 
        #        tdo = 0xFF & ShiftData(0xFF & (Send >> 8*i), DataSize - ChunkSize*i, True)
        #    else: 
        #        tdo = 0xFF & ShiftData(0xFF & (Send >> 8*i), ChunkSize,              False)
        #    Recv = Recv | tdo << (8*i)

        for i in range(nChunks):
            if (DataSize > ChunkSize*i):  # i don't think this "if" is needed
                # not the last byte sent
                if (DataSize - ChunkSize*i) > ChunkSize:
                    tdo = 0xFF & lptjtaglib.ShiftData(0xFF & (Send >> 8*i), ChunkSize,              False)
                # the last byte sent needs to have a TMS sent with it
                else:
                    tdo = 0xFF & lptjtaglib.ShiftData(0xFF & (Send >> 8*i), DataSize - ChunkSize*i, True)

            Recv = Recv | tdo << (8*i)

        if   (RegType == IR_REG):
            lptjtaglib.ExitIRShift()
        elif (RegType == DR_REG):
            lptjtaglib.ExitDRShift()

        return (Recv)

elif BACKEND == "python": 
    # system imports
    import sys

    # local imports
    import lptjtaglib


    #DEFINES
    IR_REG = 0
    DR_REG = 1

    def set_chain(Chan):
        lptjtaglib.setchainLPTJTAG(Chan)

    def StartIRShift():
        lptjtaglib.StartIRShiftLPTJTAG()

    def StartDRShift():
        lptjtaglib.StartDRShiftLPTJTAG()

    def ExitIRShift():
        lptjtaglib.ExitIRShiftLPTJTAG()

    def ExitDRShift():
        lptjtaglib.ExitDRShiftLPTJTAG()

    # Write JTAG Instruction Register
    def WriteIR(IR, IRSize):
        if (IRSize is None) or (IR is None):
            print("ERROR: Attempted to write invalid instruction register.")
            sys.exit()

        IR = IOExchange(IR, IRSize, IR_REG)
        return(IR)

    # Write JTAG Data Register
    def WriteDR(DR, DRSize):
        if (DRSize is None) or (DR is None):
            print("ERROR: Attempted to write invalid data register.")
            sys.exit()

        DR = IOExchange(DR, DRSize, DR_REG)
        return(DR)

    # Read JTAG Data Register
    def ReadDR(DR, DRSize):
        if (DR is None) or (DRSize is None):
            print("ERROR: Attempted to read invalid data register.")
            sys.exit()

        DR = IOExchange(DR, DRSize, DR_REG)
        return(DR)

    # Shift Data into JTAG Register, bit-by-bit
    def ShiftData(Data, DataSize, sendtms):
        result = 0

        # Quit if nothing is passed as data
        if (DataSize is None) or (Data is None):
            print("ERROR: Attempted to shift invalid data.")
            sys.exit()

        # Quit if data is too large
        if (DataSize < 0 or DataSize >32):
            print("ERROR: Attempted to shift too large of data (>32 bits at a time).")
            sys.exit()

        for i in range(1,DataSize+1):

            # TMS should get HIGH on the last bit of the last byte of an instruction
            # Otherwise it should be LOW
            if (sendtms) and (i==DataSize):
                tms = 0x1
            else:
                tms = 0x0

            #set TDI value
            tdi = Data & (0x1)

            #write data
            tdo=lptjtaglib.jtagioLPTJTAG(tms, tdi)

            #Throw out that bit
            Data = Data >> 1

            #Read in TDO
            result = result | ((tdo & 0x01) << (i-1))

        return(result)

    #-------------------------------------------------------------------------------
    # Sends and receives JTAG data... wrapper to to Start IR/DR Shift, Shift in data
    # while reading from TDO.. exit IR/DR shift. Returns TDO data.
    #-------------------------------------------------------------------------------
    def IOExchange(Send, DataSize, RegType):
        if (DataSize is None) or (Send is None):
            print("ERROR: attempting to write nothing to IOExchange")
            sys.exit()

        # We can write 8 bits at a time
        ChunkSize   = 8

        # Number of words needed to shift entire data
        nChunks     = (abs(DataSize-1)//ChunkSize) + 1

        # instruction register or data register? 
        # initiate data shift
        if (RegType == IR_REG):
            StartIRShift()
        elif (RegType == DR_REG):
            StartDRShift()

        Recv=0 # Received Data (reconstructed Full-packet)
        tdo =0 # Test data out (byte-by-byte)

        # this whole loop can be simplified a lot.. e.g. this seems it should have the same behavior 
        # but need to test to be sure
        #for i in range(nChunks):
        #    if i==nChunks-1: 
        #        tdo = 0xFF & ShiftData(0xFF & (Send >> 8*i), DataSize - ChunkSize*i, True)
        #    else: 
        #        tdo = 0xFF & ShiftData(0xFF & (Send >> 8*i), ChunkSize,              False)
        #    Recv = Recv | tdo << (8*i)

        for i in range(nChunks):
            if (DataSize > ChunkSize*i):  # i don't think this "if" is needed
                # not the last byte sent
                if (DataSize - ChunkSize*i) > ChunkSize:
                    tdo = 0xFF & ShiftData(0xFF & (Send >> 8*i), ChunkSize,              False)
                # the last byte sent needs to have a TMS sent with it
                else:
                    tdo = 0xFF & ShiftData(0xFF & (Send >> 8*i), DataSize - ChunkSize*i, True)

            Recv = Recv | tdo << (8*i)

        if   (RegType == IR_REG):
            ExitIRShift()
        elif (RegType == DR_REG):
            ExitDRShift()

        return (Recv)

    #def open_jtag():
    #    lptjtaglib.openLPTJTAG()
    #
    #def close_jtag():
    #    lptjtaglib.closeLPTJTAG()
    #def reset_jtag():
    #    lptjtaglib.resetLPTJTAG()

    #def enable_jtag():
    #    lptjtaglib.enableLPTJTAG()

    #def idle_jtag():
    #    lptjtaglib.idleLPTJTAG()

    #def rti_jtag():
    #    lptjtaglib.rtiLPTJTAG()

    #def oneclock_jtag():
    #    lptjtaglib.oneclockLPTJTAG()

    #def TMS_High():
    #    lptjtaglib.TMSHighLPTJTAG()

    #def TMS_Low():
    #    lptjtaglib.TMSLowLPTJTAG()

    #def lights_jtag():
    #    lptjtaglib.lightsLPTJTAG()

    #def jtag_io(tms_, tdi_):
    #    tdo=lptjtaglib.jtagioLPTJTAG(tms_, tdi_)
    #    return(tdo)

