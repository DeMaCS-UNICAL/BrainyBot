$cont=0;
while(<STDIN>){
	qx(adb exec-out screencap -p > "screen$cont.png");
	print("screen$cont.png saved");
	$cont+=1;
}
