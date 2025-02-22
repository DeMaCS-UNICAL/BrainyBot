% ================================
% Costanti
#const max_steps = 20.

% ================================
% Fatti per le palle
% ball(B,Type) dove Type ∈ {solid, striped, eight, cue}
ball(1, solid).  ball(2, solid).  ball(3, solid).  ball(4, solid).
ball(5, solid).  ball(6, solid).  ball(7, solid).
ball(8, eight).
ball(9, striped). ball(10, striped). ball(11, striped). ball(12, striped).
ball(13, striped). ball(14, striped). ball(15, striped).
ball(cue, cue).

% ================================
% Fatti per le pocket (identificate astrattamente)
pocket(p1). pocket(p2). pocket(p3). pocket(p4). pocket(p5). pocket(p6).

% ================================
% I passi (tiro)
shot(1..max_steps).

% ================================
% Assegnazione del target
% Per semplicità, predeterminata: il giocatore gioca "solid" (oppure "striped")
target(player, solid).

% ================================
% Guesses: ad ogni tiro, se il gioco non è terminato, viene eseguita esattamente una mossa.
% La mossa è del tipo moveandshoot(B,P,S) che indica che, allo step S, la palla B viene imbucata nella pocket P.
% NOTA: La cue ball non viene mai imbucata e l’8 ball può essere imbucata solo se tutte le palle target sono state imbucate.
{ moveandshoot(B, P, S) : ball(B, T), T != cue, pocket(P) } = 1 :- shot(S), not gameOver(S).

% ================================
% Vincoli per rendere le mosse legali:
% 1. Se il target è assegnato, allora (per step S) si ammettono mosse solo su:
%    - Palle dell’oggetto target, oppure
%    - L’8 ball (solo se tutte le palle del target sono già imbucate).
:- shot(S), target(player, T0), moveandshoot(B, P, S), ball(B, T), T != T0, T != eight, not gameOver(S).

:- shot(S), moveandshoot(8, P, S), not allObjectCleared(S), not gameOver(S).

% 2. Non è possibile imbucare una palla già imbucata.
:- shot(S), moveandshoot(B, P, S), pocketed(B, S).

% ================================
% Stato del gioco: definizione dei predicati per le palle imbucate.
% Inizialmente nessuna palla (tranne la cue ball) è imbucata.
pocketed(B, 0) :- ball(B, _), B != cue.

% Transizione di stato:
pocketed(B, S+1) :- shot(S), moveandshoot(B, P, S).
pocketed(B, S+1) :- pocketed(B, S), shot(S).

% Una palla non è imbucata se non compare in pocketed/2.
notPocketed(B, S) :- ball(B, _), not pocketed(B, S).

% ================================
% Definizione ausiliaria:
% allObjectCleared(S) è vero se, per il target assegnato, tutte le palle di quel tipo sono imbucate.
allObjectCleared(S) :- target(player, T), not ball(B, T) : not pocketed(B, S).

% ================================
% Condizione di fine gioco:
% Il gioco termina quando, ad uno step S, tutte le palle target sono imbucate e l’8 ball è imbucata.
gameOver(S) :- shot(S), target(player, T), allObjectCleared(S), pocketed(8, S).

% ================================
% Vincoli addizionali (opzionali):
% Non si deve effettuare alcuna mossa se il gioco è terminato.
:- gameOver(S), moveandshoot(B, P, S).

% ================================
% Ottimizzazione: minimizzare il numero totale di tiri
#minimize { 1,S : moveandshoot(_,_,S) }.

% ================================
% Direttive di output: mostra le mosse
#show moveandshoot/3.
