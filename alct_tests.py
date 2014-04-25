from JTAGLib     import *
from ALCT        import *
from LPTJTAGLib  import *
from SlowControl import *

import datetime

def main():
    #ActiveHW = 1
    SetALCTType(ALCT384)
    #NUM_AFEB=24
    ReadAllCurrents()
    ReadAllVoltages()
    WriteAllThresholds(0)
    ReadAllThresholds()
    print (ReadTemperature())

def ReadAllVoltages(): 
    print("\n%s > Read Power Supply Voltages" % Now()) 
    for i in range (4): 
        ADC     = ReadVoltageADC(i)
        voltage = ADC * arVoltages[i].coef
        print ("\t %s\tExpect=%.2fV   Read=%2.2fV  (ADC=0x%03X)" % (arVoltages[i].ref, arVoltages[i].refval, voltage, ADC))
    
def ReadAllVoltages(): 
    print("\n%s > Read Power Supply Voltages" % Now()) 
    for i in range (4): 
        ADC     = ReadVoltageADC(i)
        voltage = ADC * arVoltages[i].coef
        print ("\t %s\tExpect=%.2fV   Read=%2.2fV  (ADC=0x%03X)" % (arVoltages[i].ref, arVoltages[i].refval, voltage, ADC))

def ReadAllCurrents(): 
    print("\n%s > Read Power Supply Currents" % Now()) 
    for i in range (4): 
        ADC     = ReadCurrentADC(i)
        current = ADC * arCurrents[i].coef
        print ("\t %s\tExpect=%.2fA   Read=%2.2fA  (ADC=0x%03X)" % (arCurrents[i].ref, arCurrents[i].refval, current, ADC))
    
def ReadAllThresholds(): 
    NUM_AFEB=24
    print("%s > Read All Thresholds" % Now())
    for j in range (NUM_AFEB): 
        thresh = ReadThreshold(j)
        print("\t AFEB #%02i:  Threshold=%.3fV (ADC=0x%04X)" % (j, (ADC_REF/1023)*thresh, thresh))

def WriteAllThresholds(thresh):
    print("%s > Write All Thresholds to %i" % (Now(), thresh))
    for i in range(NUM_AFEB): 
        SetThreshold(i, thresh);
    print("\t All thresholds set to %i" % thresh)

def Now():
    ts = time.time()
    st = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')
    return(st)

def Day():
    ts = time.time()
    st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
    return(st)

def SetALCTType(alct_type):
    name        = alct_table[alct_type].name         
    alct        = alct_table[alct_type].alct         
    channels    = alct_table[alct_type].channels     
    groups      = alct_table[alct_type].groups       
    chips       = alct_table[alct_type].chips        
    delaylines  = alct_table[alct_type].delaylines   
    pwrchans    = alct_table[alct_type].pwrchans     

    global NUM_AFEB = chips * groups
    global Wires    = channels

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
