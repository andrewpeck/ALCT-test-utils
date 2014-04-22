def BitToHexLen(size):
    result = ((size - 1) // 4) + 1
    return(result)

def BitToByteLen(size):
    result = ((size - 1) // 8)+1;
    return(result)

def AdjustStrSize(instream, size):
    hexsize = BitToHexLen(size);
    result = instream;
    while (len(result) < hexsize)
        result = '0' + result

    if (length(result) > hexsize):
        Delete(result, 0, len(result)-hexsize);
        SetLength(Result,hexsize);

    mask := Trunc(IntPower(2, 4-(hexsize*4-size)))-1;
    SetLength(tmp,1);
    tmp := IntToHex(StrToInt('$'+Copy(Result,0,1)) and mask,1);
    Result := UpperCase(tmp + Copy(Result, 2, Length(Result)-1));

def ReverseStream(instream, size):
var
    tmpstr := AdjustStrSize(instream, size);
    SetLength(arBit,size);
    for j in range(size): 
        for i:=BitToHexLen(size) downto 1 do
        begin
            tmp := Copy(tmpstr, i ,1);
            tmp := IntToHex(RevHexDigit(StrToInt('$'+tmp)),1);
            result = result + tmp ;

function RevHexDigit(const digit: integer): integer;
var
    i	: integer;
begin
    Result := 0;
    for i:=0 to 3 do Result := Result or (((digit shr i) and $1) shl (3-i));
end;

function FlipByte(const value: byte):byte;
var
    i : byte;
begin
    Result := 0;
    for i:=0 to 7 do
        Result := Result or (((value  shr i) and $1) shl (7-i));
end;

function FlipHalfByte(const value: byte):byte;
var
    i : byte;
begin
    Result := 0;
    for i:=0 to 3 do
        Result := Result or (((value  shr i) and $1) shl (3-i));
end;

function FlipWord(const value: word): word;
var
    i : byte;
begin
    Result := 0;
    for i:=0 to 15 do
        Result := Result or (((value  shr i) and $1) shl (15-i));
end;

function Flip(const value: longword): longword;
var
    i : byte;
begin
    Result := 0;
    for i:=0 to 31 do
        Result := Result or (((value  shr i) and $1) shl (31-i));
end;

function FirstDelimiter(const Delimiters, S: string): Integer;
var
    P: PChar;
begin
    //  Result := Length(S);
    Result := 1;
    P := PChar(Delimiters);
    while Result <= Length(S) do
    begin
        if (S[Result] <> #0) and (StrScan(P, S[Result]) <> nil) then
{$IFDEF MSWINDOWS}
            if (ByteType(S, Result) = mbTrailByte) then
            begin
                Dec(Result);
                Exit;
            end
            else
                Exit;
{$ENDIF}
{$IFDEF LINUX}
            begin
                if (ByteType(S, Result) <> mbTrailByte) then
                    Exit;
                //	  Dec(Result);
                while ByteType(S, Result) = mbTrailByte do Dec(Result);
                Exit;
            end;
{$ENDIF}
            Inc(Result);
        end;
        Result := 0;
    end;


end.


