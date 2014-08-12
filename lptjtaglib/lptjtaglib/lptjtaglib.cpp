//------------------------------------------------------------------------------
// LPT JTAG Driver Built around inpout32.dll
// Windows only ! Sorry. But it DOES supposedly work with windows 7 
//------------------------------------------------------------------------------

#include "StdAfx.h"
#pragma comment(linker,"/DEFAULTLIB:inpout32.lib")
#pragma comment(lib,"./inpout32.lib")
short _stdcall Inp32(short PortAddress);
void _stdcall Out32(short PortAddress, short data);
#include "lptjtaglib.h"
#include "windows.h"
#include <stdlib.h>


#define IR_REG 0
#define DR_REG 1

BOOL APIENTRY DllMain ( HINSTANCE hModule,
					   DWORD ul_reason_for_call,
					   LPVOID lpReserved
					   )
{
	return TRUE; 
}

//------------------------------------------------------------------------------
// Low Level I/O
//------------------------------------------------------------------------------
// Set JTAG Chain
__declspec(dllexport) void setchain( short chain)
{
    SetPortByte(BASE_ADR, chain); 
    SetPortByte(CTRL_ADR, 11); 
    SetPortByte(CTRL_ADR, 0); 
    SetPortByte(BASE_ADR, 0); 
}

// Writes a TMS and TDI value, returns TDO
__declspec(dllexport) short jtagio ( short TMSvalue,  short TDIvalue)
{
    short TDOvalue; 
    short sendbit; 
    short rcvbit; 

    // Read Current Port Data
    sendbit = GetPortByte(BASE_ADR); 

    // choose TDI Bit
    if (TDIvalue>0) 
    {
        sendbit = sendbit | TDI; 
    } 
    else 
    {
        sendbit = sendbit & (~TDI); 
    }

    // choose TMS Bit
    if (TMSvalue>0)
    {
        sendbit = sendbit | TMS; 
    }
    else 
    {
        sendbit = sendbit & (~TMS); 
    }

    // Don't Change TDO bit
    // Write data to port
    sendbit = sendbit | TDO; 
    SetPortByte(BASE_ADR, sendbit); 

    // Clock rise
    sendbit = sendbit | TCK; 
    SetPortByte(BASE_ADR, sendbit); 

    // Read data from port
    rcvbit  = GetPortByte(STATUS_ADR); 

	//Clock fall
	sendbit = sendbit & (~TCK); 
	SetPortByte(BASE_ADR, sendbit);

	// Mask Out TDO Bit
    rcvbit   =  (~rcvbit) & TDO; 
	
	if (rcvbit == TDO)
		TDOvalue = 0;
	else 
		TDOvalue = 1;

    return(TDOvalue); 
}

// Starts an Instruction Register Shift
__declspec(dllexport) void StartIRShift ()
{
    jtagio(0, 0); 
    jtagio(1, 0); 
    jtagio(1, 0); 
    jtagio(0, 0); 
    jtagio(0, 0); 
}

// Finishes an Instruction Register Shift
__declspec(dllexport) void ExitIRShift()
{
    jtagio(1, 0); 
    jtagio(0, 0); 
    jtagio(0, 0); 
    jtagio(0, 0); 
}

// Starts a Data Register Shift
__declspec(dllexport) void StartDRShift()
{
    jtagio(0, 0);
    jtagio(1, 0);
    jtagio(0, 0);
    jtagio(0, 0);
}

// Finishes a Data Register Shift
__declspec(dllexport) void ExitDRShift() 
{
    jtagio(1, 0);
    jtagio(0, 0);
    jtagio(0, 0);
    jtagio(0, 0);
}

// Shift Data into JTAG Register, bit-by-bit
__declspec(dllexport) int ShiftData(int Data, int DataSize, int sendtms)
{
    int result = 0; 
    short tms=0; 
    short tdi=0; 
    short tdo=0; 
    int i;

    for (i=1; i <= DataSize; i++) {
        // TMS should get HIGH on the last bit of the last byte of an instruction
        // Otherwise it should be LOW
        if ((sendtms) && (i==DataSize))
            tms = 0x1; 
        else
            tms = 0x0; 

        // set TDI value
        tdi = Data & (0x1); 

        // write data
        tdo=jtagio(tms, tdi); 

        // Throw out that bit
        Data = Data >> 1; 

        // Read in TDO
        result = result | ((tdo & 0x01) << (i-1)); 
    }

    return(result); 
}

//-------------------------------------------------------------------------------
// Sends and receives JTAG data... wrapper to to Start IR/DR Shift, Shift in data
// while reading from TDO.. exit IR/DR shift. Returns TDO data.
//-------------------------------------------------------------------------------
__declspec(dllexport) int IOExchange(int Send, int DataSize, int RegType)
{
    // We can write 8 bits at a time
    short ChunkSize   = 8; 
    int   Recv=0; 
    short tdo=0;
    int i; // Iterator

    // Number of words needed to shift entire data
    short nChunks = (abs(DataSize-1)/ChunkSize) + 1; 

    // instruction register or data register? 
    // initiate data shift
    if (RegType == IR_REG)
        StartIRShift(); 
    else if (RegType == DR_REG)
        StartDRShift(); 

    // this whole loop can be simplified a lot.. e.g. this seems it should have the same behavior 
    // but need to test to be sure
    // for i in range(nChunks):
    //     if i==nChunks-1: 
    //         tdo = 0xFF & ShiftData(0xFF & (Send >> 8*i), DataSize - ChunkSize*i, True)
    //     else: 
    //         tdo = 0xFF & ShiftData(0xFF & (Send >> 8*i), ChunkSize,              0)
    //     Recv = Recv | tdo << (8*i)

    for (i=0; i<nChunks; i++)
    {
        if (DataSize > ChunkSize*i)  // i don't think this "if" is needed
        {
            // not the last byte sent
            if ((DataSize - ChunkSize*i) > ChunkSize)
                tdo = 0xFF & ShiftData(0xFF & (Send >> 8*i), ChunkSize, 0); 
            // the last byte sent needs to have a TMS sent with it
            else
                tdo = 0xFF & ShiftData(0xFF & (Send >> 8*i), DataSize - ChunkSize*i, 1); 

        }
        Recv = Recv | tdo << (8*i); 
    }

    if  (RegType == IR_REG)
        ExitIRShift(); 
    else if (RegType == DR_REG)
        ExitDRShift(); 

    //return (Recv); 
    return (0xF);
}

// Reads Byte off LPT Port
__declspec(dllexport) short GetPortByte(short adr)
{
#ifdef _LINUX
	return (0xFF);  
#else
    return(Inp32(adr));  
#endif
}

// Writes Byte to LPT Port
extern "C" void SetPortByte(short adr, short data)
{
#ifdef _LINUX
	
#else
    Out32(adr, data);
#endif
}