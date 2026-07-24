% domain of digits 1..9
num(1..9).

% one value 1..9 per cell, unless already given
{value(R,C,N): num(N)}=1 :- cell(R,C).

% a given value is fixed
value(R,C,N) :- given(R,C,N).
:- given(R,C,N), value(R,C,N2), N != N2.

% row uniqueness
:- value(R,C1,N), value(R,C2,N), C1 != C2, cell(R,C1), cell(R,C2).

% column uniqueness
:- value(R1,C,N), value(R2,C,N), R1 != R2, cell(R1,C), cell(R2,C).

% 3x3 box uniqueness (tuple inequality (R1,C1) != (R2,C2) is rejected by this
% DLV2 build with a parser error, so expressed as two separate rules instead)
:- value(R1,C1,N), value(R2,C2,N), box(R1,C1,B), box(R2,C2,B), R1 != R2, cell(R1,C1), cell(R2,C2).
:- value(R1,C1,N), value(R2,C2,N), box(R1,C1,B), box(R2,C2,B), C1 != C2, cell(R1,C1), cell(R2,C2).

#show value/3.
