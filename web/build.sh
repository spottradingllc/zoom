#!/bin/bash
umask 000
set -e
PRODUCT_NAME=Zoom
PRODUCT_PATH=DEVOPS
BuildNumber=$2
BranchName=$3
DEV_SHARED=/spot/dev
source $DEV_SHARED/Production/Build/Latest/Spot.Build.Targets.LX.sh

#################################################################

if [[ $1 == $RELEASE_ARG && $2 != '' ]]; then
	echo "Arg1 = "$1"; BuildNumber = "$2"; BranchName = "$BranchName"; JiraVersion = "$JiraVersion

	echo "*** Copy binaries and dependencies to drop folder"
	mkdir -pv $SHARED_DRIVE_PRODUCTION_FOLDER_VERSION
	cp -rv * $SHARED_DRIVE_PRODUCTION_FOLDER_VERSION
	rm -v $SHARED_DRIVE_PRODUCTION_FOLDER_VERSION/build.*

	create_release_notes

	echo "*** $1 Completed ***"
else
	echo "*** ERROR: Argument Required ('./build.sh release 1') ***"
	exit 1
fi
