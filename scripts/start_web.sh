#!/bin/bash


APP="Zoom"
LOGDATE=`date +%C%y%m%d`
LOGTIME=`date +%H%M%S`
APPPATH="/opt/spot/zoom/server"
VENV_PATH="/opt/spot/zoom/venv"
STARTCMD="python $APPPATH/zoom.py"
TIMEOUT=30
RUNLOG=$APPPATH/logs/web_stdout
#RUNLOG="/dev/null"

export PATH=$PATH:/bin
if [ -f /etc/profile.d/spotdev.sh ]; then
    source /etc/profile.d/spotdev.sh
fi

function die () {
    # There was an error, we should exit
    /bin/echo -e "ERROR: $* Aborting." >&2
    exit 1
}

function getpid()
{
    local pidnum=$(/usr/bin/pgrep "$APP");
    /bin/echo $pidnum;
}

function getstatus()
{
    pid=$(getpid);
    if [ -n "$pid" ]; then
        /bin/echo "$APP is running with pid $pid.";
    else
        /bin/echo "$APP is stopped.";
    fi;
}

function dostart()
{
    pid=$(getpid);
    if [ -n "$pid" ]; then
        die "$APP is already running with pid(s) $pid. \nEither stop the APP or run \"restart\" instead of \"start\".";
    fi;

    # check for virtual environment creation
    if [ ! -f ${VENV_PATH}/bin/activate ]; then
        die "Virtual Environment not found. Please create it first.";
    fi;

    if [ -f $RUNLOG ]; then
        mv $RUNLOG $RUNLOG.$LOGDATE.$LOGTIME
    fi;

    # check for log dir
    if [ ! -d $APPPATH/logs ]; then
        /bin/mkdir $APPPATH/logs;
        /bin/touch $RUNLOG;
    fi;

    COUNTER=0
    /bin/echo -n "Starting $APP.";
    cd $APPPATH; source ${VENV_PATH}/bin/activate; $STARTCMD > $RUNLOG 2>&1 &
    while [[ -z "$(getpid)" ]] && [[ $COUNTER -lt 10 ]]; do
        let COUNTER+=1
        /bin/echo -n " ."
        /bin/sleep 1
    done;

    pid=$(getpid);
    if [ -z "$pid" ]; then
        /bin/echo
        die "There was some issue starting $APP.";
    else
        /bin/echo
        /bin/echo "Started with pid $pid";
    fi;
}

function dostop()
{
    COUNTER=0
    /bin/echo -n "Stopping $APP.";
    /usr/bin/pkill -f $APP
    while [[ $(getpid) ]] && [[ $COUNTER -lt $TIMEOUT ]]; do
        /bin/sleep 5
        let COUNTER+=5
        /bin/echo -n " ."
    done
    echo
    pid=$(getpid);
    if [ -n "$pid" ]; then
        /bin/echo -n " Failed to kill! Sending SIGKILL..."
        /bin/kill -s 9 "$pid"
        /bin/sleep 5
    fi;
    /bin/echo "Killed $APP"
}


case "$1" in
    start)
	dostart
    ;;
    stop)
        dostop
    ;;
    restart)
        dostop
        dostart		
    ;;
    status)
        getstatus
    ;;
    *)
    echo $"Usage: $0 {start|stop|restart|status}"
    exit 1

esac

exit 0
