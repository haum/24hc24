$fn = 60;

W = 40;
D = 50;
d = 70;
H = 8;
h = 3;

// base plate
color("white", alpha=.3) cube([W, D, H]);
color("white", alpha=.3) translate([0, 15, 2]) rotate([85, 0, 0]) cube([W, d, h]);