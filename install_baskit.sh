#!/bin/bash

# The first thing we need to 
if [ "$(which yum;echo $?)" == "0" ];then
    PKG_INST="yum -y install"
    PKG_SEARCH="yum search"
    JVM="java-1.6.0-openjdk"
elif [ "$(which apt-get;echo $?)" == "0" ];then
    PKG_INST="apt-get -y update;apt-get -y install"
    PKG_SEARCH="apt-cache search"
    JVM="openjdk-6-jre"
else
    echo "WARNING: Could not determine the package management system"
    echo "         that this linux/unix box uses.  Because of this,"
    echo "         we need you to make sure that java and screen are"
    echo "         installed on the box before we continue.  If you"
    echo "         are sure that these components are installed, then"
    echo "         hit continue to keep the script moving."
    read yes_please
fi

# Install Java if it isnt already installed on the host.
if [ "$(which java;echo $?)" == "1" ];then
    echo "NOTE: Installing OpenJDK 6.  While this is a older JVM, it"
    echo "      is stable and we havent seen any issues with it running"
    echo "      minecraft servers.  If you want more speed however you"
    echo "      may want to install the Oracle 7 JVM or OpenJDK 7."
    $PKG_INST $JVM
fi


# If Screen isnt installed, then go ahead and install it ;)
if [ "$(which screen;echo $?)" == "1" ];then
    $PKG_INST screen
fi



if [ $UID != 0];then
    echo "WARNING: It's entirely possible that this script may fail."
    echo "         This is mostly due to the fact that you are running"
    echo "         it as a non-root user.  If you wish to continue"
    echo "         anyway, just hit the enter key and rock-n-roll!"
    read yes_please
fi

# One of the things we can do here is install pip automatically for the
# user if they don't have it.  We can safely assume that generally this
# will be running...
if [ "$(which pip;echo $?)" == "1" ];then
    if [ "$(which curl;echo $?)" == "0" ];then
        CURL="curl"
    elif [ "$(which wget;echo $?)" == "0" ];then
        CURL="wget -qO-"
    else:
        echo "Could not find either curl or wget so we couldn't automatically"
        echo "install pip for you.  Please lookup \'install pip\' online to"
        echo "manually install (it shouldn\'t be difficult)"
        exit
    fi
    $CURL http://python-distribute.org/distribute_setup.py | python
    $CURL https://raw.github.com/pypa/pip/master/contrib/get-pip.py | python
fi

# Now to actually install baskit ;)
pip install baskit