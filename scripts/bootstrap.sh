#!/bin/sh

# allow for where we're setting the virtual environment
if [[ $# -eq 0 ]] ;
then
    echo 'No arguments detected. Setting default VENV_DIR.'
    VENV_DIR=/opt/spot/zoom/venv
else
    VENV_DIR=$1
fi
echo "VENV_DIR=$VENV_DIR"

WEB_SERVER=http://spotpypi01.spottrading.com/pypi
PY_3RDPARTY=${WEB_SERVER}/3rdparty/python

# if exists, delete virtual environment
if [ -d ${VENV_DIR} ]; then
    rm -rf ${VENV_DIR} || exit 1
fi

/opt/python-2.7.3/bin/virtualenv ${VENV_DIR} || exit 1

source ${VENV_DIR}/bin/activate || exit 1

if [ -f /usr/bin/lsb_release ]; then
    linux_version=$(lsb_release -a | awk '/^Release/ {print $NF}')
else
    linux_version=$(awk 'NR==1{print $(NF-1)}' /etc/issue)
fi

function install_package () {
# $1 = package name
    FULLPATH=${PY_3RDPARTY}/$1
    /bin/echo -n "Installing ${FULLPATH}...";
    easy_install ${FULLPATH} > /dev/null 2>&1 || exit 2;
    /bin/echo "Done";
}

for PACKAGE in tornado-3.1.1.tar.gz \
        six-1.9.0.tar.gz \
        kazoo-2.2.1.tar.gz \
        setproctitle-1.1.8.tar.gz \
        requests-2.2.1.tar.gz \
        nose-1.3.0.tar.gz \
        mox-0.5.3.tar.gz \
        coverage-3.6.tar.gz \
        psutil-1.2.1.tar.gz \
        zope.interface-4.0.5.tar.gz \
        pygerduty-0.23-py2.7.egg

    do
        install_package ${PACKAGE};
    done

# these packages do not install correctly on CentOS 5.x machines
if [ $(echo "${linux_version:0:3} >= 6" | bc) -eq 1 ]; then
    echo
    echo 'Linux version equal or greater than 6. Installing additional packages.'

    for PACKAGE in python-ldap-2.4.10.tar.gz \
        pyodbc-3.0.6-py2.7-linux-x86_64.egg

    do
        install_package ${PACKAGE};
    done

fi

pip install grequests
