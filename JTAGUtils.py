def BitToHexLen(size):
    result = ((size - 1) // 4) + 1
    return(result)

def BitToByteLen(size):
    result = ((size - 1) // 8)+1;
    return(result)

#def AdjustStrSize(instream, size):
#    hexsize = BitToHexLen(size);
#    result = instream;
#    while (len(result) < hexsize)
#        result = '0' + result
#
#    if (length(result) > hexsize):
#        Delete(result, 0, len(result)-hexsize);
#        SetLength(Result,hexsize);
#
#    mask := Trunc(IntPower(2, 4-(hexsize*4-size)))-1;
#    SetLength(tmp,1);
#    tmp := IntToHex(StrToInt('$'+Copy(Result,0,1)) and mask,1);
#    Result := UpperCase(tmp + Copy(Result, 2, Length(Result)-1));

#def ReverseStream(instream, size):
#var
#    tmpstr := AdjustStrSize(instream, size);
#    SetLength(arBit,size);
#    for j in range(size): 
#        for i:=BitToHexLen(size) downto 1 do
#        begin
#            tmp := Copy(tmpstr, i ,1);
#            tmp := IntToHex(RevHexDigit(StrToInt('$'+tmp)),1);
#            result = result + tmp ;

def RevHexDigit(digit):
    FlipHalfByte(digit)

def FlipByte(value): 
    result = 0;
    for i in range(8): 
        result = result | (((value >> i) & 0x1) << (7-i))
    return(result)

def FlipHalfByte(value):
    result = 0
    for i in range(4): 
        result = result | (((value  >> i) & 0x1) << (3-i))
    return(result)

def FlipWord(word):
    result = 0
    for i in range(16): 
        result = result | (((word >> i) & 0x1) << (15-i));
    return(result)

def FlipLongword(longword):
    result = 0
    for i in range(32): 
        result = result | (((word >> i) & 0x1) << (31-i));
    return(result)

#function FirstDelimiter(const Delimiters, S: string): Integer;
#var
#    P: PChar;
#begin
#    //  Result := Length(S);
#    Result := 1;
#    P := PChar(Delimiters);
#    while Result <= Length(S) do
#    begin
#        if (S[Result] <> #0) and (StrScan(P, S[Result]) <> nil) then
#{$IFDEF MSWINDOWS}
#            if (ByteType(S, Result) = mbTrailByte) then
#            begin
#                Dec(Result);
#                Exit;
#            end
#            else
#                Exit;
#{$ENDIF}
#{$IFDEF LINUX}
#            begin
#                if (ByteType(S, Result) <> mbTrailByte) then
#                    Exit;
#                //	  Dec(Result);
#                while ByteType(S, Result) = mbTrailByte do Dec(Result);
#                Exit;
#            end;
#{$ENDIF}
#            Inc(Result);
#        end;
#        Result := 0;
#    end;

