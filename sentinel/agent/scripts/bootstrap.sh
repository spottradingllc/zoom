#!/bin/bash

CONF=~/.pip/pip.conf
/bin/mkdir -p "$(/usr/bin/dirname "$CONF")" && /bin/cat > "$CONF" << EOF
[global]
timeout = 60
index-url = http://spotpypi01.spottrading.com/pypi/3rdparty/python/simple
EOF

/bin/cat >  ~/.pydistutils.cfg << EOF
[easy_install]
index-url = http://spotpypi01.spottrading.com/pypi/3rdparty/python/simple

[global]
index-url = http://spotpypi01.spottrading.com/pypi/3rdparty/python/simple
EOF

VENV=/opt/spot/zoom/sentinel/agent/venv
if [ -d $VENV ]; then
    /bin/rm -rf $VENV >> bootstrap_log.txt 2>&1|| exit 2
fi


/opt/python-2.7.3/bin/virtualenv $VENV >> bootstrap_log.txt 2>&1|| exit 2

source $VENV/bin/activate || exit 2

for PACKAGE in zope.interface \
               kazoo \
               psutil \
               tornado \
               setproctitle \
               requests \
               nose \
               mox \
               coverage
do
	/bin/echo "## Installing $PACKAGE ##" >> bootstrap_log.txt 2>&1;	
    pip install $PACKAGE >> bootstrap_log.txt 2>&1 || exit 2; 
	/bin/echo "## Done with $PACKAGE ##" >> bootstrap_log.txt 2>&1;
done
