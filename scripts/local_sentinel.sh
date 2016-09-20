#!/bin/sh
APP="ZKagent"
LOGDATE=`date +%C%y%m%d`
LOGTIME=`date +%H%M%S`

PROJ_PATH="/opt/spot/zoom/"

echo $(git rev-parse --short --verify HEAD) > $PROJ_PATH/version.txt

APPPATH="${PROJ_PATH}/server"
VENV_PATH="/opt/spot/zoom/venv"
STARTCMD="python sentinel.py -v"
RUNLOG=$APPPATH/logs/stdout

export PATH=$PATH:/bin
if [ -f /etc/profile.d/spotdev.sh ]; then source /etc/profile.d/spotdev.sh; fi


if [ -f $RUNLOG ]; then
    mv $RUNLOG $RUNLOG.$LOGDATE.$LOGTIME
fi;

# check for log dir
if [ ! -d $APPPATH/logs ]; then
    /bin/mkdir $APPPATH/logs;
    /bin/touch $RUNLOG;
fi;

 cd $APPPATH; source ${VENV_PATH}/bin/activate; $STARTCMD # > $RUNLOG 2>&1
