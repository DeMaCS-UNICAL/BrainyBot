$fs = 0.5;

module hole(s) cylinder(h=10,d=s, center=true);
module m5hole() { hole(5); };
module m3hole() { hole(3); };
scubeSize = 7;
module scube() { cube([scubeSize,scubeSize,6], center = true); };

module dscube() { difference() { scube(); m3hole(); }}


x = 65;
y = 80;

/*
standardCoordinates = [[-x/2+scubeSize/2,-y/2+scubeSize/2,+1.5],
                      [x/2-scubeSize/2,-y/2+scubeSize/2,+1.5],
                      [x/2-scubeSize/2,y/2-scubeSize/2,+1.5],
                      [-x/2+scubeSize/2,y/2-scubeSize/2,+1.5]
                     ];
*/
yunOffX = -x/2+5;
yunOffY = -y/2;
yunHoles = [
  [  2.54+yunOffX, 15.24+yunOffY, 1.5 ],
  [  17.78+yunOffX, 66.04+yunOffY,  1.5 ],
  [  45.72+yunOffX, 66.04+yunOffY, 1.5 ],
  [  50.8+yunOffX, 13.97+yunOffY, 1.5 ]
  ];

// in Pi2B holes form a rectangle of 58x49
piOffX = -x/2+7.5;
piOffY = -y/2+10;
pi2modelBholes = [ [0+piOffX,0+piOffY,1.5], 
                   [49+piOffX,0+piOffY,1.5], 
                   [0+piOffX,58+piOffY,1.5], 
                   [49+piOffX,58+piOffY,1.5] 
];


supportCoordinates = yunHoles;

vslotHoles = [[10,45,0],[-10,45,0],[10,-45,0],[-10,-45,0]];


module base(scale) { difference()  {union() {cube([x,y,3], center = true); 
                                             cube([40,100,3], center = true);
                                             for (i = supportCoordinates) {                                                
                                                 translate(i) scube();  } 
                                   }; 
                                    for (i = vslotHoles)
                                    {
                                        translate(i) m5hole();
                                    }
                                    for ( i = supportCoordinates) {
                                        translate(i) m3hole();
                                    }
                                    }; }
translate([0,0,1.5]) base(1);