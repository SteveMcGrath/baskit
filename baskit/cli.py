import cmd
import datetime
import time
import getopt
import os
import datetime
import sys
from random import randint as random
from server import Server

__version__ = '0.2.1'
__author__ = 'Steven McGrath'
__email__ = 'steve@chigeek.com'

class BaskitCLI(cmd.Cmd):
    prompt = 'baskit_ng>'
    server = None
    
    def __init__(self):
        cmd.Cmd.__init__(self)
        self.server = Server()
        
        # This is some initialization stuff to make sure that the directory
        # structure that baskit expects is in place.
        for item in [self.server.env,
                     os.path.join(self.server.env, 'archive', 'backups'),
                     os.path.join(self.server.env, 'archive', 'snaps'),
                     os.path.join(self.server.env, 'env')]:
            if not os.path.exists(item):
                os.makedirs(item)
    
    def help_help(self, s):
        print 'help [COMMAND]'
    
    def do_exit(self, s):
        '''exit
        Exits the interactive CLI
        '''
        return True
    
    def do_cmd(self, s):
        '''cmd [COMMAND]
        Sends the specified command to the Minecraft server console
        '''
        self.server.command(s)
        print 'Sent to console: %s' % s
    
    def do_players(self, s):
        '''players
        Retuns a list of the currently connected players
        '''
        if not self.server.running():
            print 'Server must be running for this command to function'
        else:
            print 'Players Online: %s' % self.server.players()
    
    def do_start(self, s):
        '''start
        Starts the Minecraft service instance.
        '''
        self.server.start()
        time.sleep(0.1)
        self.do_status(s)
    
    def do_stop(self, s):
        '''stop [OPTIONS]
        Stops the Minecraft service instance.
        
        -t/--timer [SECONDS]        Wait X seconds before shutting the service
                                    down.  If the notify flag is set as well
                                    the server will notify users of the
                                    impending server outage.
        
        -p/--no-players             Wait to stop server until no players are
                                    online.  Please note that this will cause
                                    baskit to wait a potentially long period
                                    of time.
        
        -n/--notify                 Notifies the players of the current wait
                                    status for the server shutdown.
        '''
        if not self.server.running():
            print 'Minecraft service already stopped.'
            return
        
        notify = False
        pwait = False
        wait = datetime.datetime.now()
        opts, args = getopt.getopt(s.split(), 'npt:', 
                                   ['timer=', 'no-players', 'notify'])
        for opt, val in opts:
            if opt in ('-t', '--timer'):
                wait = wait + datetime.timedelta(seconds=int(val))
            if opt in ('-p', '--no-players'):
                players = True
            if opt in ('-n', '--notify'):
                notify = True
        
        # Here is the wait loop for shutting down the server.
        while wait > datetime.datetime.now() and not players:
            if players:
                if len(self.server.players) < 1:
                    players = False
            if notify:
                msg = 'SERVER WILL SHUT DOWN IN %s SECONDS' %\
                      (wait - datetime.datetime.now()).seconds
                if players:
                    msg += ' WHEN ALL PLAYERS HAVE LEFT'
                self.server.msg(msg)
            time.sleep(10)
        self.server.stop()
        print 'Minecraft service has been stopped'
    
    def do_restart(self, s):
        '''restart
        Convenience function to restart the server.  No options are provided.
        '''
        self.server.stop()
        self.server.start()
    
    def do_status(self, s):
        '''status
        Returns the current server status as well as some known configuration
        information about the server.
        '''
        if self.server.running():
            print 'Minecraft service is running'
        else:
            print 'Minecraft service is stopped'
        print '\nServer Binary Information\n-------------------------'
        print 'Type   : %s' % self.server.server_type
        print 'Branch : %s' % self.server.server_branch
        print 'Build  : %s' % self.server.server_build
        print 'Worlds : %s' % ', '.join([world.name for world in\
                                         self.server.worlds])
    
    def do_console(self, s):
        '''console
        Opens the Minecraft service console.  To exit the console 
        type Cntrl+A, D.
        '''
        self.server.console()
    
    def do_update(self, s):
        '''update [server_branch/build] [server_type]
        Updates the minecraft server binary to the specified information.
        
        Valid Server Types:
            vanilla
            bukkit
            spout
            canary
        '''
        branch = 'stable'
        bin_type= None
        cmd_in = s.split()
        print cmd_in
        if len(cmd_in) > 0:
            branch = cmd_in[0]
        if len(cmd_in) > 1:
            bin_type = cmd_in[1]
        self.server.update(branch, bin_type)
    
    def do_backup(self, s):
        '''backup
        Handles all backup functions including management of backups.
        For more information run:
        
        backup help
        '''
        msg = 'type exit to return the main console'
        if len(s) > 1:
            Backup(self.server).onecmd(s)
        else:
            Backup(self.server).cmdloop(msg)
    
    def do_snapshot(self, s):
        '''snapshot
        Handles all snapshot functions including management of all snapshots.
        For more information run:
        
        snapshot help
        '''
        msg = 'type exit to return the main console'
        if len(s) > 1:
            Snapshot(self.server).onecmd(s)
        else:
            Snapshot(self.server).cmdloop(msg)
    
    def do_world(self, s):
        '''world
        Handles all world management functions for the server.  For more
        information run:
        
        world help
        '''
        msg = 'type exit to return the main console'
        if len(s) > 1:
            WorldCLI(self.server).onecmd(s)
        else:
            WorldCLI(self.server).cmdloop(msg)

class Backup(cmd.Cmd):
    prompt = 'baskit_ng [backup]>'
    server = None
    
    def __init__(self, server):
        cmd.Cmd.__init__(self)
        self.server = server
        self.backup_path = os.path.join(self.server.env, 'archive', 'backups')
    
    def do_new(self, s):
        '''new [world_name] [backup_name]
        Creates a new world backup from the world specified, optionally a
        backup name can be specified.
        '''
        cmd_in = s.split()
        world = cmd_in[0]
        if len(cmd_in) > 1:
            name = cmd_in[1]
        else:
            name = None
        
        if any(world == witems.name for witems in self.server.worlds):
            print 'Starting world backup...'
            self.server.world_backup(world, name)
            print 'World backup complete.'
        else:
            print ('Not a configured world.  If this world exists,\n',
                   ' please add it to the configuration with world add')
    
    def do_remove(self, s):
        '''remove [name|age] [value]
        Removes backups
        '''
        try:
            option, value = s.split()
        except:
            print 'invalid command.'
            return
        
        if option == 'name':
            if '%s.zip' % value in os.listdir(self.backup_path):
                os.remove(self.backup_path)
                print 'Backup %s deleted.' % value
        if option == 'age':
            try:
                oldie = time.time() - (int(value) * 86400)
            except:
                print 'Age declaration was not an integer.'
                return
            for filename in os.listdir(self.backup_path):
                mtime = os.stat(filename).st_mtime
                if mtime < oldie:
                    os.remove(filename)
                    print 'Backup %s Deleted' % filename[:-4]
    
    def do_restore(self, s):
        '''restore [backup name] [world name]
        Restores the defined backup to the defined world name.
        '''
        try:
            backup, world = s.split()
        except:
            print 'invalid command'
            return
        if not self.server.running():
            if self.server.world_restore(backup, world):
                print 'World restored.'
            else:
                print 'Restore failed.'
        else:
            print 'Server must not be running during a restore'
    
    def do_list(self, s):
        '''list
        Returns the list of backups available.
        '''
        for filename in os.listdir(self.backup_path):
            print filename[:-4]

class Snapshot(cmd.Cmd):
    prompt = 'baskit_ng [snapshot]>'
    server = None
    
    def __init__(self, server):
        cmd.Cmd.__init__(self)
        self.server = server
        self.backup_path = os.path.join(self.server.env, 'archive', 'snaps')
    
    def do_new(self, s):
        '''new [snapshot_name]
        Creates a new snapshot with optionally a specified name.
        '''
        if len(s) < 1:
            name = None
        else:
            name = s
        print 'Starting world snapshot...'
        self.server.env_snapshot(name)
        print 'Snapshot completed.'
    
    def do_remove(self, s):
        '''remove [name|age] [value]
        Removes snapshots
        '''
        try:
            option, value = s.split()
        except:
            print 'invalid command.'
            return
        
        if option == 'name':
            if '%s.zip' % value in os.listdir(self.backup_path):
                os.remove(self.backup_path)
                print 'Snapshot %s deleted.' % value
        if option == 'age':
            try:
                oldie = time.time() - (int(value) * 86400)
            except:
                print 'Age declaration was not an integer.'
                return
            for filename in os.listdir(self.backup_path):
                mtime = os.stat(filename).st_mtime
                if mtime < oldie:
                    os.remove(filename)
                    print 'Snapshot %s Deleted' % filename[:-4]
    
    def do_restore(self, s):
        '''restore [snapshot name]
        Restores the defined snapshot.
        '''
        if os.path.exists(os.path.join(self.backup_path, '%s.zip' % s)):
            if not self.server.running():
                if self.server.env_snap_restore(s):
                    print 'Environment restored.'
                else:
                    print 'Environment restore failed.'
            else:
                print 'Server must not be running during a restore'
        else:
            print 'Snapshot does not exist.'
    
    def do_list(self, s):
        '''list
        Returns the list of snapshots available.
        '''
        for filename in os.listdir(self.backup_path):
            print filename[:-4]

class WorldCLI(cmd.Cmd):
    prompt = 'baskit_ng [snapshot]>'
    server = None
    
    def __init__(self, server):
        cmd.Cmd.__init__(self)
        self.server = server
    
    def do_add(self, s):
        '''add [world_name]
        Adds the world name specified to the baskit coonfiguration.  This is
        needed in order for baskit to be able to backup and restore world
        backups & manage ramdisks.
        '''
        self.server.world_add(s)
    
    def do_rm(self, s):
        '''rm [world name]
        Removes the world name specified from the list of worlds that the
        current server configuration can see.  Configuration artifacts may
        still exist, however are no longer needed in the configuration file.
        '''
        self.server.world_rm(s)


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

motd = '''Baskit v%s
Written by: %s
Please report any bugs or problems to the #bukget IRC channel on irc.esper.net
as well as filing them on out github page.

GitHub Repository: https://github.com/SteveMcGrath/baskit
Informational Page: http://bukget.org/baskit

Baskit: %s
''' % (__version__, 
       __author__, 
       slogans[random(0,len(slogans)-1)])

def cli():
    if len(sys.argv) > 1:
        BaskitCLI().onecmd(' '.join(sys.argv[1:]))
    else:
        BaskitCLI().cmdloop(motd)