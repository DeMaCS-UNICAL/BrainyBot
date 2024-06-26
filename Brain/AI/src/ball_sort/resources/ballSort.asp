%GUESS
move(B, T, S) | notMove(B, T, S) :- ball(B, _), tube(T), step(S), not gameOver(S).


fullTube(N):-#count{C : ball(_,C)}=N.
tubeSize(N):-#count{B : ball(B,C)}=N,  ball(_,C).
%CHECK

%PREDICATI AUSILIARI

%Nuovo stato delle boccette dopo una mossa allo step S
on(B1, B2, T, S + 1) :- step(S), move(B1, T, S), onTheTop(B2, T, S).
on(B1, 0, T, S + 1) :- step(S), move(B1, T, S), not notEmptyTube(T, S).
on(B1, B2, T, S + 1) :- step(S), on(B1, B2, T, S), not ballMoved(B1,S).

%Numero di palline contenute nella boccetta T allo step S
size(T, S, N) :- step(S), tube(T), #count{B: on(B, _, T, S)} = N.

%La pallina B ha un'altra pallina sopra allo step S
ballOnIt(B, S) :- step(S), on(_, B, _, S), B != 0.

%La pallina B � in cima alla boccetta T allo step S
onTheTop(B, T, S) :- step(S), on(B, _, T, S), not ballOnIt(B,S).

%Numero di palline di un certo colore in cima alle boccette allo step S
ballOnTheTopOfColor(C, N, S) :- step(S), color(C), #count{B : onTheTop(B, _, S), ball(B, C)} = N.

%La pallina B � nel tubo T allo step S
onTheTube(B, T, S) :- step(S), on(B, _, T, S).

%E' stata effettuata una mossa allo step S
existMove(S) :- step(S), move(_,_,S).

%La boccetta T non � vuota allo step S
notEmptyTube(T, S) :- step(S), on(_, _, T, S).

%Allo step S la boccetta T � vuota
existEmptyTube(T, S) :- tube(T), step(S), not notEmptyTube(T,S).

%La pallina B � stata mossa allo step S
ballMoved(B, S) :- step(S), move(B, _, S).

%Allo step S la boccetta T � completa
completedTube(T, S) :- step(S), tube(T), #count{C : on(B, _, T, S), ball(B, C)} = 1, size(T, S, N), tubeSize(M), N = M.

%Numero di boccette completate allo step S
completed(N, S) :- completedTube(_, S), #count{T: completedTube(T, S)} = N.

%La boccetta T contiene palline di un solo colore C allo step S
singolColorTube(T, S) :- on(_, _, T, S), #count{C : on(B, _, T, S), ball(B, C)} = 1.
singolColorTubeWithColor(T, C, S) :- singolColorTube(T, S), on(B,_,T,S), ball(B,C).
singolColorTubeWithColorMax(T, C, S) :- singolColorTubeWithColor(T, C, S), #max{N : singolColorTubeWithColor(T1, C, S), size(T1, S, N)} = MAX, size(T, S, MAX).

%Il gioco � finito allo step S se tutte le boccette sono state completate a tale step
gameOver(S) :- fullTube(N), completed(N, S).

%CONSTRAINTS

%Non � possibile spostare una pallina che non � in cima allo step S
:- step(S), move(B,_,S), on(B1, B, _, S).

%Non � possibile spostare una pallina in una boccetta piena allo step S
:- step(S), move(B, T, S), size(T, S, N), tubeSize(M), N = M.

%Non � possibile spostare una pallina nella stessa boccetta in cui si trova
:- step(S), move(B, T, S), on(B,_,T,S).

%Non � possibile spostare una pallina su un'altra di colore diverso allo step S
:- step(S), move(B, T, S), onTheTop(B1, T, S), ball(B, C1), ball(B1, C2), C1 != C2.

%Non � possibile spostare due palline allo stesso step S
:- step(S), move(B1, _, S), move(B2, _, S), B1 != B2.

%Non � possibile spostare una pallina in due boccette diverse allo stesso step S
:- step(S), move(B, T1, S), move(B, T2, S), T1 != T2.

%Non � possibile spostare la stessa pallina in due step consecutivi
:- step(S), move(B, _, S), move(B, _, S - 1).

%Non � possibile spostare una pallina che si trova in un tubo gi� completo allo step S
:- step(S), move(B, _, S), on(B, _, T, S), completedTube(T, S).

%Non � possibile che ad uno step S non viene eseguita nessuna mossa se il gioco non � ancora stato completato
:- step(S), not existMove(S), not gameOver(S).

%OPTIMIZE

%Pago se NON sposto una pallina di colore C in una boccetta che contiene solo palline di colore C
:~ step(S), notMove(B, T1, S), ball(B,C), not onTheTube(B, T1, S), onTheTop(B, _, S), singolColorTubeWithColorMax(T1, C, S). [1@7, B,S]

%Pago se sposto una pallina in una boccetta con colori diversi e c'� una boccetta vuota in cui spostare tale pallina
:~ step(S), move(B,T1,S), not singolColorTube(T1,S), notEmptyTube(T1,S), existEmptyTube(T2,S), T1 != T2. [1@6, B, S]

%Pago se ci sono tante palline di colore C in cima alle boccette e sposto una pallina di colore C1
:~ step(S), move(B, _, S), ball(B, C), ballOnTheTopOfColor(C, N, S), ballOnTheTopOfColor(C1, M, S), C != C1, N < M. [1@5, B, S]

%Pago se sposto una pallina che si trova gi� in una boccetta con un solo colore uguale a quello della pallina e tale boccetta � la pi� piena tra le boccette che contengono palline di quel colore
:~ step(S), onTheTube(B, T1, S), ball(B,C), singolColorTubeWithColorMax(T1,C,S), move(B, T2, S), not singolColorTubeWithColorMax(T2, C, S). [1@4, B, S]

%Pago se NON preferisco le mosse che 'liberano' palline di colore C ed esiste gi� un tubo che contiene solo il colore C
:~ step(S), move(B, _, S), onTheTop(B1, T, S), not singolColorTube(T, S), on(B1, B2, T, S), ball(B2, C), singolColorTubeWithColor(_, C, S), B != B1. [1@3, B, S]

%Spostare preferibilmente una pallina che sta su una una pallina dello stesso colore
:~ step(S), move(B, _, S), on(B, B1, T, S), not singolColorTube(T, S), ball(B, C), ball(B1, C1), C != C1. [1@2, B, S]

%Preferire le mosse che rendono un tubo di un solo colore
:~ step(S), move(B, _, S), on(B, _, T, S), not singolColorTube(T, S + 1). [1@1, B,S]