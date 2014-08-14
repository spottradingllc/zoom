#!/bin/sh

WEB_SERVER=http://spotpypi01.spottrading.com/pypi
PY_3RDPARTY=${WEB_SERVER}/3rdparty/python
VENV_DIR=/opt/spot/zoom/venv


/bin/cat >  ~/.pydistutils.cfg << EOF
[easy_install]
index-url = http://spotpypi01.spottrading.com/pypi/3rdparty/python/simple

[global]
index-url = http://spotpypi01.spottrading.com/pypi/3rdparty/python/simple
EOF


# if exists, delete virtual environment
if [ -d ${VENV_DIR} ]; then
    rm -rf ${VENV_DIR} || exit 1
fi

/opt/python-2.7.3/bin/virtualenv ${VENV_DIR} || exit 1

source ${VENV_DIR}/bin/activate || exit 1

for PACKAGE in python-ldap-2.4.10.tar.gz \
            tornado-3.1.1.tar.gz \
            kazoo-1.3.1dev.tar.gz \
            setproctitle-1.1.8.tar.gz \
            requests-2.2.1.tar.gz \
            pyodbc-3.0.6-py2.7-linux-x86_64.egg \
            nose-1.3.0.tar.gz \
            mox-0.5.3.tar.gz \
            coverage-3.6.tar.gz \
            psutil-1.2.1.tar.gz \
            zope.interface-4.0.5.tar.gz

do
    FULLPATH=${PY_3RDPARTY}/${PACKAGE}
	/bin/echo "## Installing ${FULLPATH} ##";
    easy_install ${FULLPATH} || exit 2;
	/bin/echo "## Done with $PACKAGE ##";
done
