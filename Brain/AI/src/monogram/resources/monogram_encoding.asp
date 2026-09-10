% on row R, there is a block with length L that is the idx-th block on the row
% same reasoning for column
% block(R,L,Idx,col)
% block(R,L,Idx,row)

%generate integers from 0 to gridSize-1
num(0).
num(X+1) :- num(X), size(S), X!=S-1.



%guess start cell of each block for rows and cols
{start(R,C,R,Length,IdxBlock,row) : cell(CellIdx,R,C,empty), size(S), C+Length <= S}=1 :- block(R,Length,IdxBlock,row).
{start(R,C,C,Length,IdxBlock,col) : cell(CellIdx,R,C,empty), size(S), R+Length <= S}=1 :- block(C,Length,IdxBlock,col).

%blocks cannot share the same start
:-start(R,C,R,L,IdxBlock1,row), start(R,C,R,L,IdxBlock2,row), IdxBlock1 != IdxBlock2.
:-start(R,C,C,L,IdxBlock1,col), start(R,C,C,L,IdxBlock2,col), IdxBlock1 != IdxBlock2. 

%deterministaclly compute fillded cells given the starting position of blocks
filled(R,C,IdxRowCol,Length,IdxBlock,Type) :- start(R,C,IdxRowCol,Length,IdxBlock,Type).
filled(R,C+N,IdxRowCol,Length,IdxBlock,row) :- start(R,C,IdxRowCol,Length,IdxBlock,row), cell(CellIdx,R,C+N,empty), num(N), N<Length.
filled(R+N,C,IdxRowCol,Length,IdxBlock,col) :- start(R,C,IdxRowCol,Length,IdxBlock,col), cell(CellIdx,R+N,C,empty), num(N), N<Length.


% it is not possible to fill a cell which contains a cross in the input
:- filled(R,C,_,_,_,_), cell(IdxCell, R, C, cross).

%No cell of segment Idx+1 after any of Idx - row
:- block(IdxRowColBlock,Length1,IdxBlock,row), block(IdxRowColBlock,Length2,IdxBlock+1,row), filled(R,C,IdxRowColBlock,Length2,IdxBlock+1,row), filled(R,C+N,IdxRowColBlock,Length1,IdxBlock,row), num(N), N>0.
%No cell of segment Idx+1 after any of Idx - col
:- block(IdxRowColBlock,Length1,IdxBlock,col), block(IdxRowColBlock,Length2,IdxBlock+1,col), filled(R,C,IdxRowColBlock,Length2,IdxBlock+1,col), filled(R+N,C,IdxRowColBlock,Length1,IdxBlock,col), num(N), N>0.



%no holes inside segment
%row
:- filled(R,C,IdxRowColBlock,Length,IdxBlock,row), not filled(R,C+1,IdxRowColBlock,Length,IdxBlock,row), filled(R,C+N,IdxRowColBlock,Length,IdxBlock,row) , N > 1, num(N), size(S), C < S-1.
%col
:- filled(R,C,IdxRowColBlock,Length,IdxBlock,col), not filled(R+1,C,IdxRowColBlock,Length,IdxBlock,col), filled(R+N,C,IdxRowColBlock,Length,IdxBlock,col) , N > 1, num(N), size(S), R < S-1.
 
%no adjacent segments
%row
:- filled(R,C,IdxRowColBlock,Length1,IdxBlock,row), filled(R,C+1,IdxRowColBlock,Length2,IdxBlock+1,row).
%col
:- filled(R,C,IdxRowColBlock,Length1,IdxBlock,col), filled(R+1,C,IdxRowColBlock,Length2,IdxBlock+1,col).


%no overlap
:- filled(R,C,X,Length1,IdxBlock1,Type), filled(R,C,X,Length2,IdxBlock2,Type), IdxBlock1 !=IdxBlock2.

%compute rows and cols
row(R) :- num(R).
col(C) :- num(C).

%number of cells to fill per row and per col
numToFillPerRow(R,N):- row(R), #sum{L,Idx : block(R,L,Idx,row)} = N.
numToFillPerCol(C,N):- col(C), #sum{L,Idx : block(C,L,Idx,col)} = N.

%num filled cells per row and col
numFilledPerRow(R,N) :- row(R), #count{C: filled(R,C,_,_,_,_)} = N.
numFilledPerCol(C,N) :- col(C), #count{R: filled(R,C,_,_,_,_)} = N.

%fill exactly as many as needed
:- numFilledPerRow(R,N), numToFillPerRow(R,N1), N != N1.
:- numFilledPerCol(C,N), numToFillPerCol(C,N1), N != N1.

%#show start/6.
