import cmd
import datetime
import time
import getopt
import os
import datetime
import sys
from random import randint as random
from server import Server

__version__ = '0.2.99.50'
__author__ = 'Steven McGrath'
__email__ = 'steve@chigeek.com'

class BaskitCLI(cmd.Cmd):
    prompt = 'baskit> '
    server = None
    
    def __init__(self):
        cmd.Cmd.__init__(self)
        self.server = Server()
        
        # This is some initialization stuff to make sure that the directory
        # structure that baskit expects is in place.
        for item in [self.server.env,
                     os.path.join(self.server.env, 'archive', 'backups'),
                     os.path.join(self.server.env, 'archive', 'snaps'),
                     os.path.join(self.server.env, 'persistent'),
                     os.path.join(self.server.env, 'env')]:
            if not os.path.exists(item):
                os.makedirs(item)


    def do_help(self, s):
        if s == '': self.onecmd('help help')
        else:
            cmd.Cmd.do_help(self, s) 

    

    def help_help(self):
        print '''Welcome to the Baskit Minecraft Server Manager!
        
        Baskit is designed to be a minimalistic, yet powerful server management
        system.  Baskit uses GNU-Screen at the heart of the application and
        simply wrap around that.  This means that you can perform in-place
        upgrades of Baskit, or even remove it completely without worry of it
        impacting the running server. There are a lot of functions available to 
        help assist you in managing the server as well, below is a high-level
        list of what is available.  For further detail (including avalable
        options) for any command, type help [COMMAND].

        start                       Starts the server.
        
        stop                        Stops the server.

        restart                     Restarts the server.

        server                      Returns the running state & server binary
                                    information that we have on-hand about
                                    the running server.

        cmd [COMMAND]               Sends the command specified to the server.
                                    There is no limit as to what can be sent
                                    here, and it is quite easy to script
                                    commands into the server with this.

        players                     Returns the list of players currently logged
                                    into the server.

        console                     Will drop you directly into the server
                                    console.  From here you are directly
                                    interacting with the server.  To detach from
                                    the server console, hit CNTRL+A,D to exit.

        update                      Allows you to update the server binary based
                                    on the conditions you had specified.  It's 
                                    highly recommended you run help update to
                                    get some more detail.

        backup                      All backup related functions are housed
                                    within the backup command.  Running "backup"
                                    will present it's help.

        snapshot                    All snapshot related functions are housed
                                    within the snapshot command.  Running
                                    "snapshot" will present it's help.

        sync                        Handles syncing to/from ramdisk and
                                    persistent storage if ramdisk support is
                                    enabled (disabled by default)
        '''
    

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
            print 'Players Online: %s' % ', '.join(self.server.players())
    

    def do_start(self, s):
        '''start
        Starts the Minecraft service instance.
        '''
        self.server.start()
        time.sleep(0.1)
        self.do_server(s)
    

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
    

    def do_server(self, s):
        '''server
        Returns the current server status as well as some known configuration
        information about the server.
        '''
        d1 = {True: 'running', False: 'stopped'}
        print 'Server Binary Information\n-------------------------'
        print 'Status : %s' % d1[self.server.running()]
        print 'Type   : %s' % self.server.server_type
        print 'Branch : %s' % self.server.server_branch
        print 'Build  : %s' % self.server.server_build
        print 'Worlds : %s' % ', '.join(self.server.worlds)


    def do_status(self, s):
        '''status
        Returns information about the health of the server.
        '''
        pass


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
        '''
        if self.server.running():
            print 'Cannot update while the server is running!'
            return None
        branch = 'stable'
        bin_type = None
        cmd_in = s.split()
        if len(cmd_in) > 0:
            branch = cmd_in[0]
        if len(cmd_in) > 1:
            bin_type = cmd_in[1]
        self.server.update(branch, bin_type)
        self.do_server('')
    

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
            Backup(self.server).onecmd('help')
    

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
            Snapshot(self.server).onecmd('help')


    def do_sync(self, s):
        '''sync [destination] [world1, [world2, world3]]
        Handles synchronization between the persistent and ramdisk storage.
        By default it will sync all of the configured worlds to the destination
        data store specified (e.g. specifying ramdisk will sync from persistent
        to ramdisk).  Optionally you can specify specific worlds that you would
        like to sync.  These are comma-deliited.

        destination                     This is the destination of the sync.
                                        Can either be ramdisk or persistent.
        '''
        opts = s.split()
        worlds = None
        if len(opts) > 1:
            worlds = [a.strip() for a in ''.join(opts[1:]).split(',')]
        if opts[0] == 'ramdisk': self.server.prsync(worlds)
        if opts[0] == 'persistent': self.server.rpsync(worlds)


class Backup(cmd.Cmd):
    server = None

    def __init__(self, server):
        cmd.Cmd.__init__(self)
        self.server = server
        self.backup_path = os.path.join(self.server.env, 'archive', 'backups')


    def do_help(self, s):
        if s == '': self.onecmd('help help')
        else:
            cmd.Cmd.do_help(self, s) 


    def help_help(self):
        print '''Backup Management Functions 

        Backups consist of only world data.  Worlds are backed up individually
        ands stored on disk as zip files.

        new [WORLD] [BACKUPNAME]        Creates a new backup of the world
                                        specified.  Optionally you can name the 
                                        backup as well.

        remove [name|age] [VAL]         Removes backups based on the condition
                                        sent.  If the condition is name, then
                                        it will remove the backup specified in
                                        the value.  If the condition is set to
                                        age, then it will remove backups older
                                        than the number of days specified in the
                                        value.

        restore [BACKUPNAME] [WORLD]    Restored the backup specified to the
                                        world specified.

        list                            Returns a list of the backups currently
                                        in the pool.
        '''
    

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
        print 'Starting world backup...'
        self.server.world_backup(world, name)
        print 'World backup complete.'
    

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
    server = None    

    def __init__(self, server):
        cmd.Cmd.__init__(self)
        self.server = server
        self.backup_path = os.path.join(self.server.env, 'archive', 'snaps')


    def do_help(self, s):
        if s == '': self.onecmd('help help')
        else:
            cmd.Cmd.do_help(self, s) 


    def help_help(self):
        print '''Snapshot Management Functions 

        Snapshots are point-in-time backups of the running binaries, plugins,
        configurations, and anything else that isnt world data.  These are very
        useful to run before performing either a server binary upgrade or
        upgrading some plugins that the server uses.

        new [SNAPNAME]          Generates a new snapshot.  The name is optional.

        remove [SNAPNAME]       Removed the specified snapshot from the pool.

        restore [SNAPNAME]      Restores a snapshot to disk.  The server must
                                be shut down prior to restoring a snapshot as
                                it overwites all binaries, plugins, and configs.

        list                    Returns a list of the snapshots in the pool.
        '''
    

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
Informational Page: http://bukget.org/pages/baskit.html

Baskit: %s
''' % (__version__, 
       __author__, 
       slogans[random(0,len(slogans)-1)])

def cli():
    if len(sys.argv) > 1:
        BaskitCLI().onecmd(' '.join(sys.argv[1:]))
    else:
        BaskitCLI().cmdloop(motd)