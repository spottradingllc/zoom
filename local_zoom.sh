#!/bin/sh
PROJ_PATH=/opt/spot/zoom/
APPPATH="${PROJ_PATH}/server"
VENV_PATH="${PROJ_PATH}/venv/"
STARTCMD="python $APPPATH/zoom.py -p 8889 -e Staging"
TIMEOUT=30
RUNLOG=$APPPATH/logs/web_stdout

echo "cd $APPPATH; . ${VENV_PATH}/bin/activate; $STARTCMD "
cd $APPPATH; . ${VENV_PATH}/bin/activate; $STARTCMD 
