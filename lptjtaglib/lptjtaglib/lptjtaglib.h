#ifndef LPTJTAGLIB_H
#define LPTJTAGLIB_H

#ifndef _LPTJTAGLIB_EXPORTS
#define _LPTJTAGLIB_API __declspec(dllexport)
#else
#define _LPTJTAGLIB_API __declspec(dllimport)
#endif

//#include <windows.h>

// LPT Addresses
#define BASE_ADR    0x378
#define STATUS_ADR  0x379
#define CTRL_ADR    0x37A

// JTAG-to-LPT Pin Mapping
#define TDI         0x01
#define TCK         0x02
#define TMS         0x04
#define TDITMS      0x05
#define TCKTMS      0x06
#define notTCKTMS   0xF9
#define TDO         0x10
#define TRST        0x04
#define STRB        0x01

extern "C" __declspec(dllexport) short jtagio ( short TMSvalue,  short TDIvalue); 
extern "C" __declspec(dllexport) void  setchain( short chain); 
extern "C" __declspec(dllexport) void  StartIRShift(); 
extern "C" __declspec(dllexport) void  ExitIRShift(); 
extern "C" __declspec(dllexport) void  StartDRShift(); 
extern "C" __declspec(dllexport) void  ExitDRShift(); 
extern "C" __declspec(dllexport) int   ShiftData(int Data, int DataSize, int sendtms); 
extern "C" __declspec(dllexport) int   IOExchange(int Send, int DataSize, int RegType); 

//short _stdcall Inp32( short PortAddress);
//void  _stdcall Out32( short PortAddress,  short data);
/* ----Prototypes of Inp and Outp--- */
extern "C" __declspec(dllexport) short GetPortByte(short adr); 
extern "C" __declspec(dllexport) void  SetPortByte(short adr, short data); 

#endif