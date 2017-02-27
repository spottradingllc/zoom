#!/bin/bash

# chkconfig: 2345 20 80
# description: zoom

. /etc/rc.d/init.d/functions

APP="Zoom"
LOGDATE=`date +%C%y%m%d`
LOGTIME=`date +%H%M%S`

if [ -d /opt/spot/zoom/server ]; then
    PROJ_PATH="/opt/spot/zoom";
elif [ -d /opt/spot/zoom/current/server ]; then
    PROJ_PATH="/opt/spot/zoom/current";
fi

APPPATH="${PROJ_PATH}/server"
VENV_PATH="/opt/spot/zoom/venv"
STARTCMD="python $APPPATH/zoom.py"
PROCESS_START_TIMEOUT=10
PROCESS_STOP_TIMEOUT=30
WEB_AVAILABLE_TIMEOUT=90
TEST_URI="http://localhost:8889/ruok"
RUNLOG="$APPPATH/logs/web_stdout"
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
    /usr/bin/pgrep "$APP";
}

function is_running() {
    [ -n "$(getpid)" ]
}

function getstatus()
{
    if is_running; then
        /bin/echo "$APP is running with pid $(getpid).";
    else
        /bin/echo "$APP is stopped.";
        exit 1
    fi;
}

function check_api_availability()
{
    /bin/echo -n "Waiting $WEB_AVAILABLE_TIMEOUT seconds for API availability."
    code=1
    counter=0
    while [[ $code -ne 0 ]] && [[ $counter -lt $WEB_AVAILABLE_TIMEOUT ]] && is_running; do
        /usr/bin/curl $TEST_URI > /dev/null 2>&1
        code=$?
        /bin/sleep 5
        let counter+=5
        /bin/echo -n " ."
    done

    if [ $code -ne 0 ]; then
        echo "Fail!"
        echo "API not available after $WEB_AVAILABLE_TIMEOUT seconds, or the process has died."
        exit 1
    else
        echo "UP!"
    fi
}

function dostart()
{
    if is_running; then
        die "$APP is already running with pid(s) $(getpid). \nEither stop the APP or run \"restart\" instead of \"start\".";
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
    while [[ -z "$(getpid)" ]] && [[ $COUNTER -lt $PROCESS_START_TIMEOUT ]]; do
        let COUNTER+=1
        /bin/echo -n " ."
        /bin/sleep 1
    done;

    if is_running; then
        /bin/echo
        /bin/echo "Started with pid $(getpid)";
    else
        die "There was some issue starting $APP.";
        /bin/echo

    fi;

    # Check that web server is available
    check_api_availability
}

function dostop()
{
    COUNTER=0
    /bin/echo -n "Stopping $APP.";
    /usr/bin/pkill -f $APP
    while is_running && [[ $COUNTER -lt $PROCESS_STOP_TIMEOUT ]]; do
        /bin/sleep 5
        let COUNTER+=5
        /bin/echo -n " ."
    done
    echo
    if is_running; then
        /bin/echo -n " Failed to kill! Sending SIGKILL..."
        /bin/kill -s 9 "$(getpid)"
        /bin/sleep 5
    fi;
    /bin/echo "Killed $APP"
}

function getversion () {
    if [ -f ${PROJ_PATH}/version.txt ];
    then
        /usr/bin/head -n1 ${PROJ_PATH}/version.txt;
    else
        /bin/echo "0-Unknown";
    fi;
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
    version)
        getversion
    ;;
    *)
    echo $"Usage: $0 {start|stop|restart|status|version}"
    exit 1

esac

exit 0
