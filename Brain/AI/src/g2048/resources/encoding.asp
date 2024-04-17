% Il nodo ha un valore
valued(Node) :- value(Node, _).

% connessioni indirette 
upper(Node1, Node2) :- superior(Node1, Node2).
upper(Node1, Node2) :- superior(Node1, Node3), upper(Node3, Node2).

% il nodo non ha nodi superiori
firstUpper(Node1) :- node(Node1), #count{Node2: superior(Node2, Node1)} = 0.


% connessioni indirette
lefter(Node1, Node2) :- left(Node1, Node2).
lefter(Node1, Node2) :- left(Node1, Node3), lefter(Node3, Node2).

% I due nodi sono sulla stessa colonna
inCol(Node1, Node2) :- upper(Node1, Node2).
inCol(Node1, Node2) :- upper(Node2, Node1).
inCol(Node1, Node1) :- node(Node1).

% I due nodi sono sulla stessa riga
inRow(Node1, Node2) :- lefter(Node1, Node2).
inRow(Node1, Node2) :- lefter(Node2, Node1).
inRow(Node1, Node1) :- node(Node1).

% Il nodo non ha nodi a sinistra
firstLefter(Node1) :- node(Node1), #count{Node2: left(Node2, Node1)} = 0.

% N = 1, S = 2, E = 3, W = 4
direction(1) | direction(2) | direction(3) | direction(4).

% Nodi direttamente raggiungibili
reachable(Node1, Node2):- direction(D), superior(Node1, Node2), D < 3.
reachable(Node1, Node2):- direction(D), left(Node1, Node2), D > 2.

% Il nodo Node1 e Node2 sono raggiungibili e non hanno valori nel mezzo
reachable(Node1, Node2) :- reachable(Node1, Node3), reachable(Node3, Node2), not valued(Node3).

% Il primo valore (superiore o sinistro) è uguale al secondo e può essere mergeato
mergeable(Node1, Node2) :- reachable(Node1, Node2), value(Node1, Value), value(Node2, Value). 

% Il nodo è in merge con un altro nodo
merged(Node) :- inMerge(Node, _).
merged(Node) :- inMerge(_, Node).

% Guess dei Merge
inMerge(Node1, Node2) | outMerge(Node1, Node2) :- mergeable(Node1, Node2).

% Check dei Merge
:- outMerge(Node1, Node2), not merged(Node1), not merged(Node2).
:- inMerge(_, Node), inMerge(Node, _).

:- direction(1), outMerge(Node1, Node2), inMerge(Node2, Node3), upper(Node1, Node3). 
:- direction(2), outMerge(Node1, Node2), inMerge(Node3, Node1), upper(Node3, Node1). 

:- direction(3), outMerge(Node1, Node2), inMerge(Node2, Node3), lefter(Node1, Node3).
:- direction(4), outMerge(Node1, Node2), inMerge(Node3, Node1), lefter(Node3, Node1).

% Il nodo non è in merge
notMerged(Node) :- node(Node), not merged(Node).

% Valore dei nodi dopo il merge
partialOutput(Node, Value) :- notMerged(Node), value(Node, Value).
partialOutput(Node, Value) :- inMerge(Node, _), value(Node, Value1), Value = Value1 * 2.

% Nodi con valori dopo il primo merge
tempValuated(Node) :- partialOutput(Node, _).

% Nodi raggiungibili anche con valori nel mezzo
indirectReachable(Node1, Node2) :- reachable(Node1, Node2).
indirectReachable(Node1, Node2) :- reachable(Node1, Node3), indirectReachable(Node3, Node2).

% Ordinamento delle righe
sorted(Node, Pos):- direction(D), D < 3, firstUpper(Node), Pos = 1.
sorted(Node, Pos):- direction(D), D < 3, superior(Node2, Node), sorted(Node2, Pos1), Pos = Pos1 + 1.

% Ordinamento delle colonne
sorted(Node, Pos):- direction(D), D > 2, firstLefter(Node), Pos = 1.
sorted(Node, Pos):- direction(D), D > 2, left(Node2, Node), sorted(Node2, Pos1), Pos = Pos1 + 1.

% Offset per spostarsi durante il riposizionamento dopo il merge
blank(Node, N):- direction(1), partialOutput(Node, _), #count{Node2: indirectReachable(Node2, Node), not tempValuated(Node2)} = N.
blank(Node, N):- direction(2), partialOutput(Node, _), #count{Node2: indirectReachable(Node, Node2), not tempValuated(Node2)} = N.
blank(Node, N):- direction(3), partialOutput(Node, _), #count{Node2: indirectReachable(Node2, Node), not tempValuated(Node2)} = N.
blank(Node, N):- direction(4), partialOutput(Node, _), #count{Node2: indirectReachable(Node, Node2), not tempValuated(Node2)} = N.

% Mappatura dei nodi da prima a dopo il riposizionamento
mapping(Node1, Node2) :- direction(1), sorted(Node1, Pos1), sorted(Node2, Pos2), blank(Node1, Offset), partialOutput(Node1, _), Pos2 = Pos1 - Offset, inCol(Node1, Node2).
mapping(Node1, Node2) :- direction(2), sorted(Node1, Pos1), sorted(Node2, Pos2), blank(Node1, Offset), partialOutput(Node1, _), Pos2 = Pos1 + Offset, inCol(Node1, Node2).
mapping(Node1, Node2) :- direction(3), sorted(Node1, Pos1), sorted(Node2, Pos2), blank(Node1, Offset), partialOutput(Node1, _), Pos2 = Pos1 - Offset, inRow(Node1, Node2).
mapping(Node1, Node2) :- direction(4), sorted(Node1, Pos1), sorted(Node2, Pos2), blank(Node1, Offset), partialOutput(Node1, _), Pos2 = Pos1 + Offset, inRow(Node1, Node2).

% Output finale
output(Node2, Value) :- mapping(Node1, Node2), partialOutput(Node1, Value).

% Non è possibile fare mosse che non modifichino la griglia
mapChanged :- mapping(Node1, Node2), Node1 != Node2.
mapChanged :- inMerge(_, _).
:- not mapChanged.

% Weak Constraints
%% Preferisco le mosse che aumentino il numero di celle vuote
:~ output(Node, Value). [1@2, Node]

%% In caso di pareggio, preferisco le mosse che contribuiscono alla monotonicità della griglia
:~ output(Node1, Value1), output(Node2, Value2), superior(Node1, Node2), Value1 > Value2. [1@1, Node1, Node2]
:~ output(Node1, Value1), output(Node2, Value2), left(Node1, Node2), Value1 > Value2. [1@1, Node1, Node2]
