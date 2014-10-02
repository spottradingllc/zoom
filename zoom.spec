# Below are global defined variables, this will allow 6.4 built packages to install/function on 5.6
# this is an rpm compatability issue and nothing to do with the software.
%global _binary_filedigest_algorithm 1
%global _source_filedigest_algorithm 1
%global _source_payload w9.gzdio
%global _binary_payload w9.gzdio

# Variables
%define DATE    %(date "+ %a %b %d %Y")
%define USER    svc.python
%define GROUP   LinuxDevelopers
%define EMAIL   serviceregistration@spottrading.com
%define SYMLNK  /opt/spot/zoom
%define SNAME   %{name}-%{version}
%define PKGHOME /opt/spot/%{SNAME}

%define ZOOM_STARTUP %{PKGHOME}/scripts/start_web.sh
%define ZOOM_INITD /etc/init.d/zoom
%define SENTINEL_STARTUP %{PKGHOME}/scripts/start_agent.sh
%define SENTINEL_INITD /etc/init.d/sentinel

%define debug_package %{nil}


# Application info
Name:           Zoom
Version:
Release:        1%{?dist}.
Summary:        A web frontend for Sentinel
Group:          Applications
License:        Spot Trading
URL:            www.spottradingllc.com
Source0:
BuildRoot:      %(mktemp -ud %{_tmppath}/%{SNAME}-%{release}-XXXXXX)
BuildArch:      x86_64
AutoReqProv:    no

%description
Application Name: %{name} Branch: %{version} Zoom is a web frontend.


%prep
%setup -c %{SNAME}
tar -ztf %{SOURCE0} >> contents.txt
# remove beginning dots
sed -i 's/^\.//g' contents.txt
# Append correct root to all files
sed -i 's|^|/opt/spot/%{name}-%{version}|' contents.txt
# remove .git files and directories from contents list
sed -i '/.git/d' contents.txt
# add quotes around files, this is to test if we can deal with files with spaces
sed -i 's/^.*$/"&"/g' contents.txt
echo "**************Contents*******************"
cat contents.txt
echo "**************Contents*******************"


%build
# This is the build section, with most rpms the software is compiled here, however since our compilation is done within bamboo, we dont make much use of this section.
# $RPM_BUILD_ROOT: /home/bamboo/rpmbuild/BUILDROOT/{app}
# $RPM_BUILD_DIR: /home/bamboo/rpmbuild/BUILD
echo $RPM_BUILD_ROOT
echo $RPM_BUILD_DIR


%install
# The install section creates build directoires and copies filles from the build directory to build root. While this seems needless we need to adhear to at least "some" of the rpm
# best practices, so here we move files to the build root. the variables commented out in the build section match with the ones below.
# Create build directories
install -d $RPM_BUILD_ROOT/opt/spot/%{SNAME}
cp -R $RPM_BUILD_DIR/%{SNAME}/ $RPM_BUILD_ROOT/opt/spot/


%clean
rm -rf $RPM_BUILD_ROOT
%files -f contents.txt
%defattr(-,%{USER},root,-)


# Below are the pre/post/preun/postun sections of the spec file, these are present to allow you to run bash at different points of a build:
#
# pre: before your rpm is installed, as you can see below, we're removing a symlink this is so if branches change your symlink will be recreated to follow that new package name.
# You can add any sort of bash shell below which will allow you to do things you need to do. This will only run once however, before your rpm is installed.
#
# post: you guessed it. this is after the package is installed, i've been using this section to set ownership or permissions on files, move init scripts check for users avalibility etc.
#
# preun: pre-uninstall, before a package is removed, you can do things, clean up logs, etc.
#
# postun: post-uninstall, its rare that this is used, however is still present within spec files.


%pre
logger -t %{name} "Entering pre section for build: %{SNAME}"
# Pre install section ( before your application is installed on the server )
# Install the first time:          1
# Upgrade:                         2 or higher
# Remove last version of package:  0
if [ -h %{SYMLNK} ]
  then
    logger -t %{name} "Removing symlink for package %{SNAME}"
    rm -f %{SYMLNK}
  else
    logger -t %{name} "No Symlink to remove for package %{SNAME}"
fi

logger -t %{name} "Exiting pre section for build: %{SNAME}"
%post


# Post Install Section, After your application is installed
logger -t %{name} "Entering post section for build: %{SNAME}"

getent passwd %{USER} > /dev/null 2>&1

if [ $? -eq 0 ]
then
  logger -t %{name}  "%{USER} for application %{SNAME} was found!"
else
  logger -t %{name}  "%{USER} Cannot be found! for application %{SNAME}"
fi


# Create soft link to web startup script
if [ -f %{ZOOM_STARTUP} ]
then
    logger -t %{name} "$script found, setting up ln/chmod"
    chmod 755 %{ZOOM_STARTUP}
    if [ ! -h %{ZOOM_INITD} ]
    then
        ln -s %{ZOOM_STARTUP} %{ZOOM_INITD}
    else
        logger -t %{name} "soft link for $script already exists"
    fi
else
    logger -t %{name} "$script NOT found! for build: %{SNAME}"
fi


# Create soft link to agent startup script
if [ -f %{SENTINEL_STARTUP} ]
then
    logger -t %{name} "$script found, setting up ln/chmod"
    chmod 755 %{SENTINEL_STARTUP}
    if [ ! -h %{SENTINEL_INITD} ]
    then
        ln -s %{SENTINEL_STARTUP} %{SENTINEL_INITD}
    else
        logger -t %{name} "soft link for $script already exists"
    fi
else
    logger -t %{name} "$script NOT found! for build: %{SNAME}"
fi


# Create soft link to project name (/opt/spot/{project name})
if [ -h %{SYMLNK} ]
then
  logger -t %{name} "ln already set for %{SNAME} no need to add."
else
  logger -t %{name} "setting ln for application %{SNAME}"
  ln -s /opt/spot/%{SNAME} %{SYMLNK}
fi


# Bootstrap stuff
cd %{PKGHOME}/scripts/
if [[ -f bootstrap.sh ]]
then
  logger -t %{name}  "Running bootstrap..."
  chmod a+x bootstrap.sh
  /bin/bash bootstrap.sh
else
  logger -t %{name}  "boostrap did not install! was not found."
fi

# ownership changes
chown -R %{USER}:%{GROUP} /opt/spot/%{SNAME}

logger -t %{name} "Exiting pre section for build: %{SNAME}"


%preun
logger -t %{name} "Entering preun section for build: %{SNAME}"
# Pre Uninstall ( before your package is removed/upgraded )
logger -t %{name} "Exiting preun section for build: %{SNAME}"


%postun
logger -t %{name} "Entering postun section for build: %{SNAME}"
# Post Uninstall ( After your package is removed/upgraded )
logger -t %{name} "Exiting postun section for build: %{SNAME}"


# Changelog, this is filled in automaticly from stash, no need to deal with this area at all.
%changelog
* %{DATE}  <%{EMAIL}> - %{version}
- TEST COMMIT
