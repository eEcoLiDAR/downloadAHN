#!/bin/bash

#script to setup cluster
#
#

#INPUT
# $1 localkeypath
# $2 cluster config file
# $3 download run config file
# $4 input list
#for ARGUMENT in "$@"
#do
#  KEY=$(echo $ARGUMENT | cut -f1 -d=)
#  VALUE=$(echo $ARGUMENT | cut -f2 -d=)

#  case "$KEY" in
#    LOCALKEYPATH)      LOCALKEYPATH=${VALUE} ;;
#    CLUSTERCONFIG)     CLUSTERCONFIG=${VALUE} ;;
#    DOWNLOADCONFIG)    DOWNLOADCONFIG=${VALUE} ;;
#    INLIST)            INLIST=${VALUE} ;;
#    *)
#  esac
#done

#. $CLUSTERCONFIG
#. $DOWNLOADCONFIG

. $2
. $3


echo '"REMEMBER TO CHECK THAT WEBDAV IS MOUNTED ON ALL VMS"'

#echo $LOCALKEYPATH

for s in $(seq 0 5)
do
  ssh -i $1 $USER@$BASESERVERNAME$s.$SERVEREXTENSION "/bin/bash -c \"mkdir -pv $DOWNLOADCODEPATH \""
  scp run_download_ahn3_vmj.sh $USER@$BASESERVERNAME$s.$SERVEREXTENSION:$DOWNLOADCODEPATH/
  scp download_ahn3.py $USER@$BASESERVERNAME$s.$SERVEREXTENSION:$DOWNLOADCODEPATH/

  if [ -n $4 ]
  then
    scp $4 $USER@$BASESERVERNAME$s.$SERVEREXTENSION:$INPUTLIST
  fi


  if [ $s -eq 0 ]
  then
    scp $1 $USER@$BASESERVERNAME$s.$SERVEREXTENSION:$CLUSTERKEYPATH
    scp $2 $USER@$BASESERVERNAME$s.$SERVEREXTENSION:$DOWNLOADCODEPATH/
    scp run_download_ahn3.sh $USER@$BASESERVERNAME$s.$SERVEREXTENSION:$DOWNLOADCODEPATH/
    scp $3 $USER@$BASESERVERNAME$s.$SERVEREXTENSION:$DOWNLOADCODEPATH/
  fi
done
