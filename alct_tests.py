import SlowControl
import SingleCable
import TesterBoard
from ALCT        import *
from Common import Now
from Common import Day
import Delays

import random
import datetime
import time
import os

def main():
    ALCT384=1
    global  alcttype
    alcttype=ALCT384
    MainMenu()
    print("SIC TRANSIT GLORIA MUNDI")
    sleep(0.1)

def MainMenu():
    while True:
        os.system('cls')
        print("\n====================")
        print(  " ALCT JTAG Test Menu")
        print(  "====================\n")
        ReadIDCodes()
        DetectMezzanineType()
        print("")
        print("\t 0 ALCT Automatic Full Test")
        print("\t 1 Slow Control Tests")
        print("\t 2 Thresholds Linearity Full Scan")
        print("\t 3 Delay ASICs Pattern Test")
        print("\t 4 Delay ASICs Delay Test")
        print("\t 5 Single Cable Test")
        print("\t 8 Initialize JTAG Chains")

        k=input("\nChoose Test: ")
        if not k: break
        os.system('cls')


        ALCT384=1
        global  alcttype
        alcttype=ALCT384

        if k=="0":
            AutomaticFullTest()
        if k=="1":
            SlowControl.SubtestMenu(alcttype)
        if k=="2":
            SlowControl.CheckThresholds(alct[alcttype].groups*alct[alcttype].chips,1)
        if k=="3":
            delays.SubtestMenu(alcttype)
        if k=="4":
            TesterBoard.SubtestMenu(alcttype)
        if k=="5":
            SingleCable.SubtestMenu(alcttype)
        if k=="8":
            ChooseJTAGChain()

def ChooseJTAGChain():
        while True:
            os.system('cls')
            print("\n==========================")
            print(  " JTAG Chain Initialization")
            print(  "==========================\n")
            print("\t 0 Slow Control Programming Chain")
            print("\t 1 Slow Control Control Chain")
            print("\t 2 Mezzanine Programming Chain")
            print("\t 3 Mezzanine Control Chain")

            k=input("\nChoose chain or <cr> to return to Main Menu: ")
            os.system('cls')
            print("")
            if not k: break

            if k=="0":
                SetChain(arJTAGChains[0])
            if k=="1":
                SetChain(arJTAGChains[1])
            if k=="2":
                SetChain(arJTAGChains[2])
            if k=="3":
                SetChain(arJTAGChains[3])
            k=input("\n<cr> to return to menu: ")

def AutomaticFullTest():
    k=input("\nLoad Single Cable Firmware. Press s to skip, any key to Continue\n")
    if k!="s":
        SingleCable.SingleCableSelfTest()

    k=input("\nLoad Test Firmware. Press s to skip, any key to Continue\n")

    k=input("\nLoad Normal Firmware. Press s to skip, any key to Continue\n")
    if k!="s":
        SlowControl.SelfTest(alcttype)

def ReadIDCodes():
    print("\t Slow Control Firmware ID: 0x%X" % SlowControl.ReadIDCode(0))
    print("\t Fast Control Firmware ID: 0x%X" % SlowControl.ReadIDCode(1))
    print("\t Board Serial Number:      0x%X" % SlowControl.ReadBoardSN(0x2))
    print("\t Mezz. Serial Number:      0x%X" % SlowControl.ReadBoardSN(0x3))

def CheckTemperature():
    print("\n%s> Check Board Temperature" % Now())
    print("\t  Board Temperature=%0.2fF" % ReadTemperature())

def Now():
    ts = time.time()
    st = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')
    return(st)

def Day():
    ts = time.time()
    st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
    return(st)

if __name__ == "__main__":
    main()
