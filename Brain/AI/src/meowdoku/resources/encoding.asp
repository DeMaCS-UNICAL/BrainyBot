% cell(x [int],y [int], colore[int] ,gatto[bool]).


assigned_cats(ID) :- cell(_,_, ID, true).
color(ID) :- cell(_,_,ID,false), not assinged_cats(ID).

placed_cat(X,Y,ID) :- cell(X,Y,ID,true).
placed_cat(X, Y, ID) : cell(X,Y,ID,_) :- color(ID).

:- placed_cat(X,Y,_), placed_cat(Z,Y,_), X!=Z.
:- placed_cat(X,Y,_), placed_cat(X,Z,_), Y!=Z.

:- placed_cat(X,Y,_), placed_cat(Z,W,_), | X - Z| = 1, |Y - W| = 1.

outcat(X,Y,ID) :- placed_cat(X,Y,ID), not cell(X,Y,ID,true).
#show outcat / 3.