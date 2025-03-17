% ballPool_shot.asp
% Programma ASP minimalista per effettuare solo il tiro

% La regola genera un tiro (moveandshoot) per il passo 1 se:
% - esiste una ghost_ball, stick, aimline e una buca (pocket);
% - la palla mirata (ball) ha un tipo che coincide con il target assegnato (assigned_target).
% NOTA: I fatti (ball/2, pocket/1, ghost_ball/1, stick/1, aimline/1 e assigned_target/1)
% sono passati dinamicamente dall'input del tuo programma Python.

moveandshoot(P, S, G, A, L, 1) :-
    ghost_ball(G),
    stick(S),
    aimline(L),
    ball(A, T),
    assigned_target(T),
    pocket(P).
