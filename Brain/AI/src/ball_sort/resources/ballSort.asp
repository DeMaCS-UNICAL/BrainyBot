%GUESS
%move(B, T, S) | notMove(B, T, S) :- ball(B, _), tube(T), step(S), not gameOver(S).
{move(B,T,S):movable(B,T,S)}=1:-step(S), not gameOver(S).

movable(B,T,S):-onTop(B,T1,S), not ballMoved(B,S-1), onTop(B1,T,S),T!=T1, ball(B,C), ball(B1,C).
movable(B,T,S):-onTop(B,T1,S), not ballMoved(B,S-1), tube(T),T!=T1, not notEmptyTube(T,S).

fullTube(N):-#count{C : ball(_,C)}=N.
tubeSize(N):-#count{B : ball(B,C)}=N,  ball(_,C).
%CHECK

%PREDICATI AUSILIARI

%Nuovo stato delle boccette dopo una mossa allo step S
on(B1, B2, T, S + 1) :- step(S), move(B1, T, S), onTop(B2, T, S).
on(B1, 0, T, S + 1) :- step(S), move(B1, T, S), not notEmptyTube(T, S).
on(B1, B2, T, S + 1) :- step(S), on(B1, B2, T, S), not ballMoved(B1,S).

%Numero di palline contenute nella boccetta T allo step S
size(T, S, N) :- on(_,_,_,S),tube(T), #count{B: on(B, _, T, S)} = N.

%La pallina B ha un'altra pallina sopra allo step S
ballOnIt(B, S) :- step(S), on(_, B, _, S), B != 0.
nextBallOnIt(B,S+1):- step(S), on(_, B, _, S+1), B != 0.
%La pallina B � in cima alla boccetta T allo step S
onTop(B, T, S) :- step(S), on(B, _, T, S), not ballOnIt(B,S).
nextOnTop(B,T,S+1):-step(S), on(B, _, T, S+1), not nextBallOnIt(B,S+1).

%Numero di palline di un certo colore in cima alle boccette allo step S
ballOnTopOfColor(C, N, S) :- step(S), color(C), #count{B : onTop(B, _, S), ball(B, C)} = N.

%La pallina B � nel tubo T allo step S
inTube(B, T, S) :- step(S), on(B, _, T, S).

%E' stata effettuata una mossa allo step S
existMove(S) :- step(S), move(_,_,S).

%La boccetta T non � vuota allo step S
notEmptyTube(T, S) :- step(S), on(_, _, T, S).

%Allo step S la boccetta T � vuota
existEmptyTube(T, S) :- tube(T), step(S), not notEmptyTube(T,S).

%La pallina B � stata mossa allo step S
ballMoved(B, S) :- move(B, _, S).

%Allo step S la boccetta T � completa
completedTube(T, S) :- tube(T), #count{C : on(B, _, T, S), ball(B, C)} = 1, size(T, S, N), tubeSize(M), N = M.

%Numero di boccette completate allo step S
completed(N, S) :- completedTube(_, S), #count{T: completedTube(T, S)} = N.

%La boccetta T contiene palline di un solo colore C allo step S
singleColorTube(T, S) :- on(_, _, T, S), #count{C : on(B, _, T, S), ball(B, C)} = 1.
singleColorTubeWithColor(T, C, S) :- singleColorTube(T, S), on(B,_,T,S), ball(B,C).
singleColorTubeWithColorMax(T, C, S) :- singleColorTubeWithColor(T, C, S), #max{N : singleColorTubeWithColor(T1, C, S), size(T1, S, N)} = MAX, size(T, S, MAX).

%Il gioco � finito allo step S se tutte le boccette sono state completate a tale step
gameOver(S) :- fullTube(N), completed(N, S).

%CONSTRAINTS

%Non � possibile spostare una pallina in una boccetta piena allo step S
:- step(S), move(B, T, S), size(T, S, N), tubeSize(M), N = M.
:- step(S), move(B, T, S), completedTube(T1,S), onTop(B,T1,S).



wrongPlace(B):-step(S), on(B,_,T,S+1), ball(B,C), not singleColorTubeWithColorMax(T, C, S+1).
%wrongPlace(B):-step(S), on(B,B1,_,S+1), ball(B,C), ball(B1,C1), C!=C1.
%wrongPlace(B):-wrongPlace(B1), on(B,B1,_,S+1), step(S).
%wrongPlace(B):-step(S), on(B,_,T,S+1), ball(B,C), singleColorTubeWithColorMax(T1, C, S+1), T!=T1.

%:-move(B,T,S), B!=22.
wrongs(N):- #count{B : wrongPlace(B)}=N.
next_movable(B):-nextOnTop(B,T,S),nextOnTop(B1,T1,S), B!=B1, ball(B,C), ball(B1,C), size(T1,S,N), not tubeSize(N).
next_movable(B):- nextOnTop(B,T,S), size(T1,S,0).
freeToMove(N):- #count{B : next_movable(B)}=N.
%OPTIMIZE
:~ #count{T:singleColorTubeWithColorMax(T, C, S)}=N,color(C), N>1. [N@10, N,C]
:~ wrongs(N). [N@9,N]
:~ freeToMove(N),tubeSize(M),fullTube(T). [T*M-N@8, N,M,T]



%%%%%%%%%%%:~ move(B,T,S), move(B1,T1,S-1), T!=T1. [1@7, B,B1,T,T1,S]


%%%%%%%%%:~ step(S), move(B, _, S), ball(B, C), ballOnTopOfColor(C, N, S), ballOnTopOfColor(C1, M, S),  N < M. [M-N@6, B, S]

%%%%%%%%%:~ step(S), move(B, _, S), onTop(B1, T, S), not singleColorTube(T, S), on(B1, B2, T, S), ball(B2, C), singleColorTubeWithColor(_, C, S), B != B1. [1@5, B, S]

%Pago se NON sposto una pallina di colore C in una boccetta che contiene solo palline di colore C
%:~ step(S), not move(B, T1, S), ball(B,C), not inTube(B, T1, S), onTop(B, _, S), singleColorTubeWithColorMax(T1, C, S). [1@7, B,S]

%Pago se sposto una pallina in una boccetta con colori diversi e c'� una boccetta vuota in cui spostare tale pallina
%:~ step(S), move(B,T1,S), not singleColorTube(T1,S), notEmptyTube(T1,S), existEmptyTube(T2,S), T1 != T2. [1@7, B, S]

%Pago se ci sono tante palline di colore C in cima alle boccette e sposto una pallina di colore C1

%Pago se sposto una pallina che si trova gi� in una boccetta con un solo colore uguale a quello della pallina e tale boccetta � la pi� piena tra le boccette che contengono palline di quel colore
%:~ step(S), inTube(B, T1, S), ball(B,C), singleColorTubeWithColorMax(T1,C,S), move(B, T2, S), not singleColorTubeWithColorMax(T2, C, S). [1@7, B, S]

%Pago se NON preferisco le mosse che 'liberano' palline di colore C ed esiste gi� un tubo che contiene solo il colore C

%Spostare preferibilmente una pallina che sta su una una pallina dello stesso colore
%:~ step(S), move(B, _, S), on(B, B1, T, S), not singleColorTube(T, S), ball(B, C), ball(B1, C1), C != C1. [1@7, B, S]

%Preferire le mosse che rendono un tubo di un solo colore
%:~ step(S), move(B, _, S), on(B, _, T, S), not singleColorTube(T, S + 1). [1@7, B,S]


ignore_tube(T):-tube(T), step(S), #count{C : on(B,_,T,S+1),ball(B,C)}=1, #count{B: on(B,_,T,S+1)}=M, tubeSize(M).
feedback(B,0,T,1) :- step(S), on(B,0,T,S+1), not ignore_tube(T).
feedback(B,P+1,T,1):- step(S), on(B,B1,T,S+1), feedback(B1,P,T,1).

feedback_on_color(C,P,T,1):-feedback(B,P,T,1), ball(B,C).

