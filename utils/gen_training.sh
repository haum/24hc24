#!/bin/bash

E=0  # End
A=1  # Asteroid
N=2  # Nebula
M=3  # Magnetic cloud
C1=4 # Checkpoint 1
C2=5 # Checkpoint 2
C3=6 # Checkpoint 3
C4=7 # Checkpoint 4

########################################

PREFIX=maps/training1
echo TITLE Straight from one side to the other | tee $PREFIX.log
./mapBuilder.py \
	-d     6  4  3 \
	-i     0  0  0 \
	-b $E  5  3  2 \
	> $PREFIX.map
cat $PREFIX.map >> $PREFIX.log

########################################

PREFIX=maps/training2
echo TITLE With asteroid | tee $PREFIX.log
./mapBuilder.py \
	-d     6  4  3 \
	-i     0  0  0 \
	-b $A  3  1  1 \
	-b $A  3  2  1 \
	-b $A  3  1  2 \
	-b $A  3  2  2 \
	-b $E  5  3  2 \
	> $PREFIX.map
cat $PREFIX.map >> $PREFIX.log

########################################

PREFIX=maps/training3
echo TITLE With nebula | tee $PREFIX.log
./mapBuilder.py \
	-d     6  4  3 \
	-i     0  0  0 \
	-b $N  3  1  1 \
	-b $N  3  2  1 \
	-b $N  3  1  2 \
	-b $N  3  2  2 \
	-b $E  5  3  2 \
	> $PREFIX.map
cat $PREFIX.map >> $PREFIX.log

########################################

PREFIX=maps/training4
echo TITLE With magnetic cloud | tee $PREFIX.log
./mapBuilder.py \
	-d     6  4  3 \
	-i     0  0  0 \
	-b $M  3  1  1 \
	-b $M  3  2  1 \
	-b $M  3  1  2 \
	-b $M  3  2  2 \
	-b $E  5  3  2 \
	> $PREFIX.map
cat $PREFIX.map >> $PREFIX.log

########################################

PREFIX=maps/training5
echo TITLE With a unique checkpoint | tee $PREFIX.log
./mapBuilder.py \
	-d     6  4  3 \
	-i     0  0  0 \
	-b $C1 5  3  1 \
	-b $E  0  0  2 \
	> $PREFIX.map
cat $PREFIX.map >> $PREFIX.log

########################################

PREFIX=maps/training6
echo TITLE With two checkpoints | tee $PREFIX.log
./mapBuilder.py \
	-d     6  4  3 \
	-i     0  0  0 \
	-b $C1 5  3  1 \
	-b $C2 3  1  1 \
	-b $E  0  0  2 \
	> $PREFIX.map
cat $PREFIX.map >> $PREFIX.log

