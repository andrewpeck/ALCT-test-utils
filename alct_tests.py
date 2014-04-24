from JTAGLib     import *
from ALCT        import *
from LPTJTAGLib  import *
from SlowControl import *

import datetime

def main():
    ActiveHW = 1
    #enable_jtag()
    #resetLPTJTAG()
    NUM_AFEB=24
    #jtagioLPTJTAG(1,1)
    #set_chain(1)
    #WriteDR(0xFF,8)
    #ReadDR()
    #WriteDR(0xFF,8)
    #jtagioLPTJTAG(0,1)
    WriteAllThresholds(0)
    ReadAllThresholds()
    #SetThreshold(0, 0xFF)
    #SetThreshold(0,0)
    #IOExchange(0xFA,6,IR_REG)
    #print(ReadThreshold(0))
    
    
def Now():
    ts = time.time()
    st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
    return(st)
 
def ReadAllThresholds(): 
    NUM_AFEB=24
    print("%s > === Read All Thresholds (Ref %.0f V)" % (Now(), ADC_REF))
    for j in range (NUM_AFEB): 
        thresh = ReadThreshold(j)
        print("    AFEB # %i: \tThreshold = %.3f V, ADC=%i" % (j, (ADC_REF/1023)*thresh, thresh))

def WriteAllThresholds(thresh):
    print("%s > === Write All Thresholds to %i" % (Now(), thresh))
    for i in range(NUM_AFEB): 
        SetThreshold(i, thresh);

def SetALCTType(alct_type):
    NUM_AFEB = ALCTBoard.chips * ALCTBoard.groups;
    Wires    = ALCTBoard.channels
    #lbAFEBn.Caption := 'AFEB # (0..'+IntToStr(NUM_AFEB-1)+')';
    #seAFEBn.Max := NUM_AFEB-1;
    #seTCH.Max := NUM_AFEB-1;
    #seChanNum.Max := NUM_AFEB-1;
    #seChartCh1.Max := NUM_AFEB-1;
    #seChartCh2.Max := NUM_AFEB-1;
    #seFIFOCh.Max := NUM_AFEB-1;
    #seSingleCableChan.Max := NUM_AFEB-1;
    #        SetLength(dataFIFOwrite, NUM_AFEB);
    #        SetLength(dataFIFOread, NUM_AFEB);
    #parlen := ALCTBoard.groups + 2;

    #for i:= 0 to ALCTBoard.groups - 1 do
    #begin
    #    for j:=0 to ALCTBoard.chips -1 do
    #    begin
    #    arDelays[i][j].Value := 0;
    #    arDelays[i][j].Pattern := 0;
    #    end;
    #end;
    #for i:=0 to MAX_DELAY_GROUPS - 1 do
    #begin
    #    (FindComponent('DG'+IntToStr(i)) as TCheckBox).Enabled := false;
    #    (FindComponent('edStndby'+IntToStr(i+1)) as TEdit).Enabled := false;
    #    (FindComponent('edStndby'+IntToStr(i+1)) as TEdit).Text := '00';
    #end;
    #for i:=0 to ALCTBoard.groups - 1 do
    #begin
    #    (FindComponent('DG'+IntToStr(i)) as TCheckBox).Enabled := true;
    #    (FindComponent('edStndby'+IntToStr(i+1)) as TEdit).Enabled := true;
    #end;
    #CurrChart.BottomAxis.Minimum := 0;
    #CurrChart.BottomAxis.Maximum := NUM_AFEB;
    #end;

if __name__ == "__main__":
    main()
