from commands import getoutput as run
import os

def send(name, text, newline=True):
    '''send [screen name], [text]
    Send the specified text to the screen console of the name specified.
    '''
    if newline:
        text = text + '\n'
    run('screen -S %s -p0 -X stuff \'%s\n\'' % (name, text))
    
def exists(name):
    '''exists [screen name]
    Returns True/False wehther there is a screen of that name active.
    '''
    output = run('screen -wipe %s' % name)
    if output[:20] == 'There is a screen on':
        return True
    return False

def new(name, command):
    '''new [screen name], [shell command]
    Starts up a new screen console using the name and command specified.
    '''
    run('screen -dmLS %s bash -c \'%s\'' % (name, command))

def console(name):
    '''console [screen name]
    shortcut to directly open the screen terminal.
    '''
    os.system('screen -DRS %s' % name)

def kill(name):
    pass