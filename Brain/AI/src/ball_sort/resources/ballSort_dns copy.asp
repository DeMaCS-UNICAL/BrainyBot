%on(Color,Tube,Pos,1)
%tube(Tube)
%color(C)
%maxTubeSize(N)
color(C):-on(C,_,_,_).
step(1..2).
{move(Tube1,Tube2) : compatible(Tube1,Tube2,1)}=1.

:-allSameColor(T,C,1),allSameColor(T1,C,1),T<T1, not move(T,T1).

lower(C,T,S):-on(C,T,P,S), on(_,T,P1,S), P1>P.
onTop(C,T,S):-on(C,T,_,S), not lower(C,T,S).
maxTubeSize(N):-#count{T,P : original_on(C,T,P)}=N, color(C).

not_empty(T,S):-on(_,T,_,S).
empty(T,S):-tube(T),step(S), not not_empty(T,S).
size(T,N,1):-#count{C,P : original_on(C,T,P)}=N, tube(T),step(S).
size(T,N,2):-size(T,N,1), not move(T,T1), tube(T), tube(T1).
size(T,N-1,2):-size(T,N,1), move(T,T1).
size(T1,N+1,2):-size(T1,N,1), move(T,T1).
size(T,0,S):- empty(T,S).
full(T,S):-size(T,N,S),size(N).

compatible(T1,T2,S):-tube(T1),tube(T2),empty(T2,S), not empty(T1,S).
compatible(T1,T2,S):-onTop(C,T1,S),onTop(C,T2,S),T1!=T2, not full(T2,S).

differentColors(T,S):-on(C,T,_,S),on(C1,T,_,S), C!=C1.
allSameColor(T,C,S):-not differentColors(T,S), on(C,T,_,S).
allSameColor(T,S):-allSameColor(T,C,S).
completed(T,S):-full(T,S),allSameColor(T,_,S).


on(C,T,P,2):-on(C,T,P,1), not move(T,T1), tube(T1),tube(T2).
on(C,T,P,2):-move(T,_), P<N, size(T,N,1), on(C,T,P,1).
on(C,T,N+1,2):-move(T1,T),onTop(C,T1,1),size(T,N,1).

movable(N):-#count{C,T : onTop(C,T,2),onTop(C,T1,2),T!=T1, not full(T1,2), not completed(T,2)}=N.

:~ tube(T), not completed(T,2). [T@4]
:~ tube(T), not allSameColor(T,2). [T@3]
:~ movable(N). [20-N@2]
