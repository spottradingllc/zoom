all:
	sh docker/zoom/build.sh
	sh docker/sentinel/build.sh

zoom:
	sh docker/zoom/build.sh

sentinel:
	sh docker/sentinel/build.sh
