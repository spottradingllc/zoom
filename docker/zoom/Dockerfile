FROM local/zoom-onbuild
MAINTAINER Jeremy Alons <jeremy.alons@spottradingllc.com>
EXPOSE 8889
ENTRYPOINT cd /opt/spot/zoom/server; EnvironmentToUse='Staging' sh /opt/spot/zoom/scripts/local_zoom.sh
