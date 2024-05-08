%cell(id,i,j,value)
%type_of(id,type)

{swap(C1,C2):can_swap(C1,C2)}=1.
:- swapped(C),cell(C,_,_,"notTouch.png").
swapped(C1,C2):-swap(C1,C2).
swapped(C2,C1):-swap(C1,C2).
swapped(C1):-swapped(C1,_).
swapped(C1):-swapped(_,C1).
can_swap(C1,C2):-cell(C1,I1,J,V1), cell(C2,I2,J,V2), I1-I2=1, V1!=V2, V1!="", V2!="".
can_swap(C1,C2):-cell(C1,I,J1,V1), cell(C2,I,J2,V2), J1-J2=1, V1!=V2, V1!="", V2!="".

new_cell(ID,I,J,V) :- cell(ID,I,J,V), not swapped(ID).
new_cell(ID1,I,J,V1) :- cell(ID,I,J,V), cell(ID1,I1,J1,V1), swapped(ID,ID1).

not_a_match_from_to(ID,ID1):- new_cell(ID,I,J,V),new_cell(ID1,I,J1,V), V!="", new_cell(ID2,I,J2,V1), V1!=V, J2>J, J2<J1.
not_a_match_from_to(ID,ID1):- new_cell(ID,I,J,V),new_cell(ID1,I1,J,V), V!="", new_cell(ID2,I2,J,V1), V1!=V, I2>I, I2<I1.
not_a_match_from_to(ID,ID1):- new_cell(ID2,I,J-1,V),new_cell(ID,I,J,V),new_cell(ID1,I,J1,V), V!="",J1>J.
not_a_match_from_to(ID,ID1):- new_cell(ID2,I,J1+1,V),new_cell(ID,I,J,V),new_cell(ID1,I,J1,V), V!="",J1>J.
not_a_match_from_to(ID,ID1):- new_cell(ID2,I-1,J,V),new_cell(ID,I,J,V),new_cell(ID1,I1,J,V), V!="",I1>I.
not_a_match_from_to(ID,ID1):- new_cell(ID2,I1+1,J,V),new_cell(ID,I,J,V),new_cell(ID1,I1,J,V), V!="",I1>I.

match(I,J1,I,J2,J2-J1+1):-V!="notTouch.png",V!="",new_cell(ID,I,J1,V), new_cell(ID1,I,J2,V), not not_a_match_from_to(ID,ID1), J2-J1>1.
%match("r",I,J2,J1):-V!="notTouch.png",V!="",new_cell(ID,I,J1,V),new_cell(ID1,I,J2,V), not not_a_match_from_to(ID,ID1), J2-J1>1.
match(I1,J,I2,J-I1+1):-V!="notTouch.png",V!="",new_cell(ID,I1,J,V),new_cell(ID1,I2,J,V), not not_a_match_from_to(ID,ID1), I2-I1>1.
%match("c",J,I2,I1):-V!="notTouch.png",V!="",new_cell(ID,I1,J,V),new_cell(ID1,I2,J,V), not not_a_match_from_to(ID,ID1), I2-I1>1.
%maximizing(5-N):-match(N), N>=3.
%:~ maximizing(N). [N@8]
%explode(I,J):- match(I1,J1,I2,J2,_),cell(ID,I,J,_), I>=I1,I<=I2,J>=J1,J<=J2.
new_cell(ID) :- match(I,J1,I,J2,_),cell(ID,I3,J3,"notTouch.png"), I3>=I-1,I3<=I+1,J3 >=J1-1,J3<=J2+1.
new_cell(ID) :- match(I1,J,I2,J,_),cell(ID,I3,J3,"notTouch.png"), J3>=J-1,J3<=J+1,I3 >=I1-1,I3<=I2+1.
in_match(ID):- match(I1,J1,I2,J2,_),cell(ID,I,J,_), I>=I1,I<=I2,J >=J1,J<=J2.

match(N):-match(_,_,_,_,N), N>=3.
match :- match(N).
:- not match.
:~ cell(ID,_,_,"notTouch.png"), not new_cell(ID). [1@8,ID]
:~ cell(ID,_,_,_), not in_match(ID). [1@7,ID]
#show swap/2.