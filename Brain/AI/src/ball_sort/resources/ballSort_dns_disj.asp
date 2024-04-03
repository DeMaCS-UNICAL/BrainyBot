%GUESS

%{move(B, T, S):movable(B,T,S)}=1:-step(S), not gameOver(S).
move(B,T,S) | nMove(B,T,S) :- movable(B,T,S), not gameOver(S).
:- #count{B,T : move(B,T,S)}!=1, step(S), not gameOver(S). 
%CHECK
movable(B,T1,S):- not ballMoved(B,S-1),onTheTop(B,T,S),onTheTop(B1,T1,S),T!=T1,ball(B,C),ball(B1,C),size(T1, S, N), tubeSize(M), N < M.
movable(B,T1,S):-not ballMoved(B,S-1),onTheTop(B,T,S),tube(T1),not notEmptyTube(T1, S).
%PREDICATI AUSILIARI 
%Nuovo stato delle boccette dopo una mossa allo step S
on(B1, B2, T, S + 1) :- step(S), move(B1, T, S), onTheTop(B2, T, S).
on(B1, 0, T, S + 1) :- step(S), move(B1, T, S), not notEmptyTube(T, S).
on(B1, B2, T, S + 1) :- step(S), on(B1, B2, T, S), not ballMoved(B1,S).

atLeastOneDifferent(S,S1):-onTheTop(B,T,S),onTheTop(B1,T,S1), S1<S, B!=B1, not gameOver(S).
notOk:- step(S), not gameOver(S), step(S1), S1<S, not atLeastOneDifferent(S,S1).
:- notOk.
%Numero di palline contenute nella boccetta T allo step S
moveFrom(T,S):-move(B,_,S), on(B,_,T,S).
moveTo(T,S):-move(_,T,S).
size(T,1,N):-tubeSize(N),on(_,_,T,1).
size(T,1,0):-tube(T),not notEmptyTube(T,1).
size(T,S+1,N):- size(T,S,N),not moveFrom(T,S), not moveTo(T,S), step(S).
size(T,S+1,N-1):-size(T,S,N), moveFrom(T,S).
size(T,S+1,N+1):-size(T,S,N), moveTo(T,S).

%La pallina B ha un'altra pallina sopra allo step S
ballOnIt(B, S) :- step(S), on(_, B, _, S), B != 0.

%La pallina B � in cima alla boccetta T allo step S
onTheTop(B, T, S) :- step(S), on(B, _, T, S), not ballOnIt(B,S), not completedTube(T,S).


%La boccetta T non � vuota allo step S
notEmptyTube(T, S) :- step(S), on(_, _, T, S).


%La pallina B � stata mossa allo step S
ballMoved(B, S) :- step(S), move(B, _, S).

notSingleColor(T,S):-on(B,B1,T,S), ball(B,C), ball(B1,C1), C!=C1.
completedTube(T,S):-not notSingleColor(T,S),size(T,S,N),tubeSize(N).

completed(0,1).
newCompleted(S):-completedTube(T,S), not completedTube(T,S-1), move(_,_,S-1).
completed(N,S):-completed(N,S-1), not newCompleted(S),move(_,_,S).
completed(N+1,S):-completed(N,S-1), newCompleted(S).



%Il gioco � finito allo step S se tutte le boccette sono state completate a tale step
gameOver(S1) :- fullTube(N), completed(N, S), step(S1), S1>=S.
gameOver:-gameOver(S).
:-not gameOver.
%CONSTRAINTS
%OPTIMIZE
%:~ move(B,T,S). [S@6,S]
%:~ not newCompleted(S),step(S), not gameOver(S). [5@S]
%:~ on(B,_,T,S),on(B1,_,T1,S),T!=T1,ball(B,C),ball(B1,C). [4@B,B1,T,T1,S,C]
%:~ on(B,B1,T,S),ball(B,C),ball(B1,C1),C!=C1. [4@B,B1,T,S,C,C1]
%:~ #count{S:ballMoved(B,S)}=N, ball(B,_). [3@N,B]

#show move/3.
#show gameOver/1.
#show on/4.
%#show size/3.
%#show completedTube/2.
%#show completed/2.
%#show newCompleted/1.
%#show fullTube/1.