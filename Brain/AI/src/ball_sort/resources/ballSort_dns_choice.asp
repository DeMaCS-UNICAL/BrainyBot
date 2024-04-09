%GUESS

{move(B, T, S):movable(B,T,S)}=1:-step(S).
%CHECK
movable(B,T1,S):- not ballMoved(B,S-1),onTheTop(B,T,S),onTheTop(B1,T1,S),T!=T1,ball(B,C),ball(B1,C),notFull(T1,S).
movable(B,T1,S):- not ballMoved(B,S-1),onTheTop(B,T,S),size(T1,S,0), notCompletedTube(T,S).


on(B1, B2, T, S + 1) :- move(B1, T, S), onTheTop(B2, T, S).
on(B1, 0, T, S + 1) :- move(B1, T, S), size(T,S,0).
on(B1, B2, T, S + 1) :- step(S), on(B1, B2, T, S), not ballMoved(B1,S).

atLeastOneDifferent(S,S1):-onTheTop(B,T,S),onTheTop(B1,T,S1), S1<S, S-S1<4, B!=B1.
notOk:- step(S), step(S1), S1<S, S-S1<4, not atLeastOneDifferent(S,S1).
:- notOk.

moveFrom(T,S):-move(B,_,S), on(B,_,T,S).
moveTo(T,S):-move(_,T,S).
ballMoved(B, S) :- move(B, _, S).

size(T,1,N):-tubeSize(N),on(_,_,T,1).
size(T,1,0):-tube(T),not notEmptyTube(T,1).
size(T,S+1,N):- size(T,S,N),not moveFrom(T,S), not moveTo(T,S), step(S).
size(T,S+1,N-1):-size(T,S,N), moveFrom(T,S).
size(T,S+1,N+1):-size(T,S,N), moveTo(T,S).

ballOnIt(B, S) :-on(_, B, _, S).

onTheTop(B, T, S) :- on(B, _, T, S), not ballOnIt(B,S).

notEmptyTube(T, S) :- on(_, _, T, S).


notSingleColor(T,S):-on(B,B1,T,S), ball(B,C), ball(B1,C1), C!=C1.

notCompletedTube(T,S):-notSingleColor(T,S).
notFull(T,S):-size(T,S,M),tubeSize(N), M<N.
notCompletedTube(T,S):-notFull(T,S).

completed(0,1).
newCompleted(S+1):-not notCompletedTube(T,S+1), notCompletedTube(T,S), move(_,_,S).
completed(N,S+1):-completed(N,S), not newCompleted(S+1),move(_,_,S).
completed(N+1,S+1):-completed(N,S), newCompleted(S+1).


gameOver(S) :- fullTube(N), completed(N, S).
:- #count{S : gameOver(S)}!=1.



#show move/3.
#show gameOver/1.
#show on/4.
%#show size/3.
%#show completedTube/2.
%#show completed/2.
%#show newCompleted/1.
%#show fullTube/1.