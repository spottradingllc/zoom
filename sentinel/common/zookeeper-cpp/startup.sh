#!/bin/bash

APP="service.cpp"
LOGDATE=`date +%C%y%m%d`
DIRPATH="~/development/devops/service-registration-poc/service-cpp/build"
SERVICEUSER="david.shrader"
STARTCMD="./$APP"
TIMEOUT=10

function getpid()
{
    local pidnum=$(/usr/bin/pgrep -fx $STARTCMD);
    echo $pidnum;
}

function getstatus()
{
    pid=$(getpid);
    if [ -n "$pid" ]; then
        echo "$APP is running with pid $pid.";
		exit 0;
    else
        echo "$APP is stopped.";
		exit 1;
    fi;
}

function dostart()
{
    pid=$(getpid);
    if [ -n "$pid" ]; then
        echo "$APP is already running with pid $pid.";
        echo "Either stop the application or run \"restart\" instead of \"start\".";
        exit 1;
    fi;
    echo "Starting $APP";
    /bin/su - $SERVICEUSER -c "cd $DIRPATH; $STARTCMD > /dev/null 2>&1 &";
    pid=$(getpid);
    echo "Started with pid $pid";
}

function dostop()
{
    echo "Stopping $APP";
    pid=$(getpid);
    kill -TERM $pid
    while [[ $(getpid) ]] && [[ $COUNTER -lt $TIMEOUT ]]; do
        /bin/sleep 5
        let COUNTER+=5
        echo -n "."
    done
	pid=$(getpid) 
    if [ -n "$pid" ]; then
        echo -n " Failed to kill! Sending SIGKILL..."
        kill -s 9 $(getpid)
        /bin/sleep 5
    fi;
	echo "Killed $APP";
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
    echo $"Usage: $0 {start|stop|status|restart}"
    exit 1

esac

exit 0

