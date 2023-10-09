@header= ("screen","red","blue","orange","purple","green","greenVertical","greenHorizontal","purpleVertical",
"purpleHorizontal","orangeVertical","orangeHorizontal","blueVertical","blueHorizontal","redVertical","redHorizontal","purpleBomb",
"orangeBomb","redBomb","blueBomb","greenBomb","notTouch","colourB");

@results = qx(cat candy_crush_output | sort -k 1 -n);
for(@header){
    print "$_\t";
}
shift @header;
print "\n";
for(@results){
    chomp;
    @res=split "\t";
    print "$res[0]\t";
    shift @res;
    for $val (@res){
        @temp = split ":",$val;
        $count{$temp[0]}=$temp[1];
    }

    for(@header){
        if(exists $count{$_}){
            print "$count{$_}\t";
        }
        else{
            print "0\t";
        }
    }
    print "\n";
    %count=();
}
