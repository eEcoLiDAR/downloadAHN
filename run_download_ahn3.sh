#!/bin/bash

#This script is executed on 'master' server eecolidar0 and runs downlaod accross all VMs

#inputs
# $1  download configuration file
# $2 cluster configuration file


#source configuration files
. $1
. $2

vm_max=$(($NUMBERVMS -1))

for s in $(seq 0 $vm_max)
do
  echo "running download on server $s"

  ssh -i $CLUSTERKEYPATH $USER@$BASESERVERNAME$s.$SERVEREXTENSION "/bin/bash -c \"nohup $DOWNLOADCODEPATH/run_download_ahn3_vmj.sh $s $LOCALREPOSITORY $OUTPUTDIRECTORY $NUMBERVMS $NUMBERPROC $COPYLOCAL $DOWNLOADCODEPATH $INPUTLIST > $DOWNLOADCODEPATH/dlahn3_VM$s.out & \""
  #ssh -i $CLUSTERKEYPATH $USER@$BASESERVERNAME$s.$SERVEREXTENSION "/bin/bash -c \"((nohup $DOWNLOADCODEPATH/run_download_ahn3_vmj.sh $s $LOCALREPOSITORY $OUTPUTDIRECTORY $NUMBERVMS $NUMBERPROC $COPYLOCAL $DOWNLOADCODEPATH $INPUTLIST > $DOWNLOADCODEPATH/dlahn3_VM$s.out) &)\""
done
