#!/usr/bin/env python
import baskit
import sys
from random import randint as random

slogans = [
    'Managing Minecraft so you dont have to.',
    'Helping minecraft admins since 2011.',
    'Wrapping the wrapper(s)',
    'Open Sourced for your enjoyment. (Open Source responsibly)',
    'Pythonically awesome!',
    'Repository on github!',
    'Helps ease Notchian headaches!',
    'I ran out of catchy slogans. :(',
    '42.',
    'killall -9 everyone and let root@localhost sort \'em out',
    'What does this do?',
    'All your minecraft are belong to us',
    'Ni!',
    'We want a shrubbery!',
    '%>what_girls_say.mp3 > /dev/null',
    '#: cat pay_check > beer',
    'caffeine | brain > minecraft',
    'chown -R us ./base',
    'Keep staring ... I may do a trick.',
    'Occupy Minecraft',
    'NG isn\'t just for StarTrek anymore',
    
]

_motd = '''Baskit v%s
Written by: %s
Please report any bugs or problems to the #bukget IRC channel on irc.esper.net
as well as filing them on out github page.

GitHub Repository: https://github.com/SteveMcGrath/baskit
Informational Page: http://bukget.org/baskit

Baskit: %s
''' % (baskit.__version__, 
       baskit.__author__, 
       slogans[random(0,len(slogans)-1)])

if __name__ == '__main__':
    if len(sys.argv) > 1:
        BaskitCLI().onecmd(' '.join(sys.argv[1:]))
    else:
        BaskitCLI().cmdloop(motd)