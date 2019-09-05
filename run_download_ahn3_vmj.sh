#!/bin/bash

#script runs ahn3 download on VM. called by run_download?_ahn3.#!/bin/sh

#INPUT
# $1 VM number/id
# $2 LOCALREPOSITORY
# $3 OUTPUTDIRECTORY
# $4 NUMBERVMS
# $5 NUMBERPROC
# $6 COPYLOCAL
# $7 DOWNLOADCODEPATH
# $8 INPUTLIST use for testing!!


echo $8
echo $7
echo $6
echo $5
echo $4
echo $3
echo $2
echo $1


#/bin/bash -c "$7/download_ahn3.py -l $2 -o $3 -v $4 -j $1 -p $5 -c $6 -i $8 ; "
/bin/bash -c "$7/download_ahn3.py -l $2 -o $3 -v $4 -j $1 -p $5 -c $6 ; "
