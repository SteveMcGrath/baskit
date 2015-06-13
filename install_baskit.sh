1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51
52
53
54
55
56
57
58
59
60
61
62
63
64
65
66
67
68
69
70
71
72
73
74
75
76
77
78
79
80
81
82
83
84
85
86
87
88
89
90
91
92
93
94
95
96
97
98
99
#!/bin/bash
 
PKG_INST=''
PKG_SEARCH=''
JVM=''
 
# The first thing we need to 
if [ "$(which yum >> /dev/null;echo $?)" == "0" ];then
    PKG_INST="yum -y install"
    PKG_SEARCH="yum search"
    JVM="java-1.8.0-openjdk"
elif [ "$(which apt-get >> /dev/null;echo $?)" == "0" ];then
    apt-get -y update
    PKG_INST="apt-get -y install"
    PKG_SEARCH="apt-cache search"
    JVM="openjdk-7-jre"
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
if [ "$(which java >> /dev/null;echo $?)" == "1" ];then
    echo "NOTE: Installing OpenJDK 8.  While this is not Oracle's JVM, it"
    echo "      is stable and we havent seen any issues with it running"
    echo "      minecraft servers."
    $PKG_INST $JVM
fi
 
# Setup a Systemd service if systemd is being used...
if [[ -d "/usr/lib/systemd/system" && ! -f "/usr/lib/systemd/system/baskit.service" ]];then
    echo "NOTE: Systemd Installation detected.  We will be installing"
    echo "      a Systemd service called 'baskit'."
    cat << EOF > /usr/lib/systemd/system/baskit.service
[Unit]
Description=Minecraft Server
 
[Service]
ExecStart=/usr/bin/baskit start
ExecStop=/usr/bin/baskit stop
 
[Install]
WantedBy=multi-user.target
EOF
    systemctl daemon-reload
fi
 
 
# If Screen isnt installed, then go ahead and install it ;)
if [ "$(which screen;echo $?)" == "1" ];then
    $PKG_INST screen
fi
 
 
 
if [ $UID != 0 ];then
    echo "WARNING: It's entirely possible that this script may fail."
    echo "         This is mostly due to the fact that you are running"
    echo "         it as a non-root user.  If you wish to continue"
    echo "         anyway, just hit the enter key and rock-n-roll!"
    read yes_please
fi
 
# One of the things we can do here is install pip automatically for the
# user if they don't have it.  We can safely assume that generally this
# will be running...
if [ "$(which pip >> /dev/null;echo $?)" == "1" ];then
    if [ "$(which curl >> /dev/null;echo $?)" == "0" ];then
        CURL="curl"
    elif [ "$(which wget >> /dev/null;echo $?)" == "0" ];then
        CURL="wget -qO-"
    else
        echo "Could not find either curl or wget so we couldn't automatically"
        echo "install pip for you.  Please lookup 'install pip' online to"
        echo "manually install (it shouldn't be difficult)"
        exit
    fi
    $CURL https://bootstrap.pypa.io/get-pip.py | python
fi
 
# Now to actually install baskit ;)
if [ "$(pip list | grep Baskit > /dev/null;echo $?)" == "1" ];then
    pip install baskit
fi
 
if [ "$1" == "global" ];then
    echo "Installing the Baskit Environment to work in a global context..."
    mkdir /opt/minecraft
    cd /opt/minecraft
    baskit help > /dev/null
    mv ./baskit.conf /etc/baskit.conf
    sed -i 's/environment.*$/environment = \/opt\/minecraft/g' /etc/baskit.conf
    echo "eula=true" > /opt/minecraft/env/eula.txt
fi
