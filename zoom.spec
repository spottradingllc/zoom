# Template RPM spec file!
# This is a templated file that will go over some of options/configurations that need to be set in order to utilize the new salt deployment methods.
# If you have any questions or concerns, please speak with a member of the IT staff!

# Below are global defined variables, this will allow 6.4 built packages to install/function on 5.6
# this is an rpm compatability issue and nothing to do with the software.
%global _binary_filedigest_algorithm 1
%global _source_filedigest_algorithm 1
%global _source_payload w9.gzdio
%global _binary_payload w9.gzdio


# Name, this is the most important bit of the spec file. This name must match the name of this file, as well as any grains used for targeting. the name will also be the name of your application rpm.
Name:           Zoom
# Version, this will be filled in automaticly from the jiraversion.txt file, or the branch you have in bamboo.
Version: 
# Release is also appended with the build numbner ( from bamboo ) and the word spot, this is for easy tracking of packages across the board
Release:        1%{?dist}.
# Summary, Group, License, URL are all filled out by the user, please add a summary of the application, you can leave everything else as it is, or change it depending on how you feel.
Summary:        A web frontend for Sentinel
Group:          Applications
License:        Spot Trading
URL:            www.spottradingllc.com
# Source is filled out using an external script, please leave this blank, if you have multiple sources ( i.e brining in drivers or libraries from say the shared drive, please work with IT as there will be changes to this section to facilitate this.
Source0:        
# BuildRoot and BuildArch can be left the way they are currently, if we being to create non x86_64 applications we can change that. 
BuildRoot:      %(mktemp -ud %{_tmppath}/%{name}-%{version}-%{release}-XXXXXX)
BuildArch:      x86_64 
# This is set so rpmbuild doesnt pickup interperter paths and forces them to be required, crashing the build.
AutoReqProv: no
# This requires is for building, since we're not doing any building in this file, do not use BuildRequires!
# Requires a package, this is before installing use this requires. 
# requires is a special variable within the spec file. it allows an rpm to require (ha ha) another rpm package before this package can be installed. 
# only rpm packaged applications ( both spot and non spot ) can be required. there is also an inverse of requires, conflicts. 

# Define variables within spec file
# Below are variables that can be used in a spec file. they are mostly self explanatory, you can add as many as you wish, they can be called using the syntax below
# the last define, debug package should be left alone, unless you're looking to use debug packages.
%define DATE  %(date "+ %a %b %d %Y")
%define USER  svc.python
%define GROUP "domain users"
%define EMAIL serviceregistration@spottrading.com
%define SYMLNK "/opt/spot/zoom"
%define SNAME "%{name}-%{version}"
%define PKGHOME "/opt/spot/%{name}-%{version}/"
%define debug_package %{nil}


%description
# Please update with a more descriptive description:
Application Name: %{name} Branch: %{version} Zoom is a web frontend.

# The prep section below makes changes on the contents.txt file, removing dots appending roots, etc. This can be edited if needed. however care must be taken as misstepping here will produce
# "unintended" results...
%prep
%setup -c %{name}-%{version}
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
install -d $RPM_BUILD_ROOT/opt/spot/%{name}-%{version}
install -d $RPM_BUILD_ROOT/opt/spot/%{name}-%{version}/logs
cp -R $RPM_BUILD_DIR/%{name}-%{version}/ $RPM_BUILD_ROOT/opt/spot/


# Clean, well cleans some of the rpmbuild directories, no need to muck about here.
%clean
rm -rf $RPM_BUILD_ROOT
%files -f contents.txt
%defattr(-,%{USER},root,-)
#%dir /opt/spot/%{name}-%{version}


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
    rm %{SYMLNK}
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

# this is for future log location standardization. Currently unused.
if [ ! -d /opt/spot/logs ]
  then
    mkdir /opt/spot/logs
fi


# Create soft links to web startup script
cd %{PKGHOME}scripts/
script="start_web.sh"
sym_path="/etc/init.d/zoom"

if [[ -f ${script} ]]
then
    logger -t %{name} "$script found, setting up ln/chmod"
    chmod 755 ${script}
    if [ ! ${sym_path} ]
    then
        ln -s %{PKGHOME}scripts/${script} ${sym_path}
    else
        logger -t %{name} "soft link for $script already exists"
    fi
else
    logger -t %{name} "$script NOT found! for build: %{SNAME}"
fi


# Create soft link to agent startup script
cd %{PKGHOME}scripts/
script="start_agent.sh"
sym_path="/etc/init.d/sentinel"

if [[ -f ${script} ]]
then
    logger -t %{name} "$script found, setting up ln/chmod"
    chmod 755 ${script}
    if [ ! ${sym_path} ]
    then
        ln -s %{PKGHOME}scripts/${script} ${sym_path}
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
  ln -s /opt/spot/%{name}-%{version} %{SYMLNK}
fi


# Bootstrap stuff
cd %{PKGHOME}scripts/
if [[ -f bootstrap.sh ]]
then
  logger -t %{name}  "Running bootstrap..."
  chmod a+x bootstrap.sh
  /bin/bash bootstrap.sh 
else
  logger -t %{name}  "boostrap did not install! was not found."
fi  

# ownership changes
chown -R %{USER}:"%{GROUP}" /opt/spot/%{name}-%{version}

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
