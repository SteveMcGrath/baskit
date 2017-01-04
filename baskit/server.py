import os
import sys
import re
import time
import datetime
from zipfile import ZipFile
from commands import getoutput as run
from ConfigParser import ConfigParser
import mc
import screen
import config


def compress_folder(zip_filename, location, from_loc=None, excludes=[]):
    zfile = ZipFile(zip_filename, 'a')
    for dirpath, dirs, files in os.walk(location):
        for f in files:
            excluded = False
            fn = os.path.join(dirpath, f)
            arc_name = fn.replace(from_loc, '')
            if fn in excludes:
                continue
            zfile.write(fn, arc_name)
    zfile.close()


class Server(object):
    name = 'default'
    java_args = ''
    env = './'
    binary = 'server.jar'
    server_type = 'vanilla'
    server_branch = 'stable'
    server_build = '1.0'
    worlds = []
    _config_file = 'baskit.conf'
    

    def __init__(self):
        '''Baskit server initialization
        '''
        self._config_file = config.get_config_file()
        self.get_config()
    

    def running(self):
        '''running
        Returns True/False whether the server is running or not.
        '''
        return screen.exists('mc_%s' % self.name)
    

    def get_config(self, config_file=None):
        '''get_config
        Fetches the configuration for the server and adjusts the variables
        within the server object to match the configuration.
        '''
        
        # Initializing the configration parser and reading the config file.
        conf = ConfigParser()
        if config_file == None:
            config_file = self._config_file
        conf.read(config_file)
        
        # Setting the section name and fetching the information from the
        # configuration file and applying those values to the appropriate
        # object variable.
        section = 'Server'
        self.name = conf.get(section, 'name')
        self.java_args = conf.get(section, 'java_args')
        self.binary = conf.get(section, 'binary')
        self.env = conf.get(section, 'environment')
        self.server_type = conf.get(section, 'server_type')
        self.server_branch = conf.get(section, 'server_branch')
        self.server_build = conf.get(section, 'server_build')
        self.min_mem = conf.get(section, 'min_mem')
        self.max_mem = conf.get(section, 'max_mem')
        self.logging = conf.getboolean(section, 'screen_log')
        self.termout = conf.getboolean(section, 'terminal_out')
        self.ramdisk = conf.getboolean(section, 'ramdisk')
        
        # Linking in the worlds that we are aware of to the server
        # configuration.  This is normally entirely optional unless you would
        # like to use the backup & restore functions, or if you would like to
        # use ramdisks.
        for world_name in conf.get(section, 'worlds').split(','):
            world_name = world_name.strip()
            self.worlds.append(world_name)
    

    def set_config(self):
        '''set_config
        Commits the current configuration of the server object to the config
        file.  This i also useful in generating a new configuration
        declaration if this is a new installation or if you will be running
        multiple servers.
        '''
        
        # Initializing the configuration parser and reading in the existing
        # data if there is any.
        conf = ConfigParser()
        if os.path.exists(self._config_file):
            conf.read(self._config_file)
        
        # Setting the section name and commiting the variables to the config
        # file.
        section = 'Server'
        conf.set(section, 'name', self.name)
        conf.set(section, 'binary', self.binary)
        conf.set(section, 'environment', self.env)
        conf.set(section, 'server_type', self.server_type)
        conf.set(section, 'server_branch', self.server_branch)
        conf.set(section, 'server_build', self.server_build)
        conf.set(section, 'min_mem', self.min_mem)
        conf.set(section, 'max_mem', self.max_mem)
        conf.set(section, 'java_args', self.java_args)
        conf.set(section, 'screen_log', self.logging)
        conf.set(section, 'terminal_out', self.termout)
        conf.set(section, 'ramdisk', self.ramdisk)
        conf.set(section, 'worlds', ', '.join(self.worlds))
        
        # Lastly, we need to write the config file to disk.
        with open(self._config_file, 'wb') as configfile:
            conf.write(configfile)
        
    
    def command(self, command, *restring):
        '''command [command]
        Sends the specified command to the server console and will optionally
        wait for a given regex to return a match from the server.log before
        returning.
        '''
        
        if len(restring) > 0:
            # If a regex was specified for interactivity, then we will need
            # to open the server.log file and seek to the end of the file
            # before we actually do anything.  Once we send the command that
            # was specified we will use the end of the file as a starting
            # point for the parsing.
            logfile = open(os.path.join(self.env, 'env/logs', 'latest.log'), 'r')
            size = os.stat(os.path.join(self.env, 'env/logs', 'latest.log'))[6]
            logfile.seek(size)
        
        # Sending the command to the screen session
        screen.send('mc_%s' % self.name, command)
        
        if len(restring) > 0:
            # Now we will start parsing through all of the log data that the
            # server is returning, using the now old EOF as a starting point.
            # We will run the regex that we had compiled to the relog variable
            # on every line until we get a match, then return those matches.
            found = 0
            relog = re.compile(restring[found])
            while found < len(restring):
                where = logfile.tell()
                line = logfile.readline()
                if not line:
                    time.sleep(0.1)
                    logfile.seek(where)
                else:
                    data = re.compile(restring[found]).findall(line)
                    if len(data) > 0:
                        found += 1
            logfile.close()
            return data
        
        # If there was no regex specified, then there is nothing to return.
        return None
    

    def msg(self, message):
        '''msg [Message]
        Sends the specified message to all players.
        '''
        self.command('say %s' % message)
    

    def console(self):
        '''console
        shortcut to open the screen session directly.
        '''
        screen.console('mc_%s' % self.name)
    

    def start(self):
        '''start
        Starts the Minecraft server and runs any per-world initialization.
        '''
        
        # First thing, we need to check to make sure the server isnt running,
        # we don't want to create any oddness as a result of running two
        # identically configured servers.
        if not self.running():
            
            # Next we will run the per-world initialization.  Normally this
            # shouldn't do anything, however if the worlds are stored on
            # ramdisks then there will be some useful setup stuff happening.
            self.prsync()
            
            # Now just to setup all the variables, determine which java we
            # will be running, and to build the bash command that we will send
            # to screen to startup the server.
            renv = os.path.join(self.env, 'env')
            java = run('which java')
            startup = 'cd %s;%s %s -Xms%sm -Xmx%sm -jar %s nogui' % (renv,
                                                               java,
                                                               self.java_args,
                                                               self.min_mem,
                                                               self.max_mem, 
                                                               self.binary)
            # And here we go, startup time!
            screen.new('mc_%s' % self.name, startup, self.logging)
    

    def stop(self):
        '''stop
        Tells the minecraft server to stop.
        '''
        # First thing we will need to is tell the server to stop and wait for
        # the server to finish shutting down.
        self.command('stop')
        while self.running():
            time.sleep(0.1)
        
        # Then we will run the cleanup on every world.  Just like world inits,
        # generally there shouldn't be much going on here, however if there
        # are ramdisk worlds, then we will be performing some actions here in
        # order to properly cleanup and make sure all the ramdisk data is
        # synced.
        self.rpsync()
    

    def players(self):
        '''players
        Returns the list of currently commected players
        '''
        strings = {
            'vanilla': [r'players online:', r'INFO\](.*)$'],
            'bukkit': [r'players online:', r'(.*)$'],
            'spigot': [r'players online:', r'INFO\](.*)$'],
        }
        line = self.command('list', *strings[self.server_type])[0]
        line = line.strip('\n').strip('\x1b[m')
        players = [a.strip() for a in line.split(',')]
        if players[0] == '': players = []
        return players
    

    def update(self, build_type='stable', bin_type=None):
        if self.running():
            return False
        
        if bin_type == None:
            bin_type = self.server_type
        
        # Download the new server binary
        binary = mc.download(bin_type, build_type)
        
        if binary['binary'] == None:
            return False
        
        # Setting the new variable definitions...
        self.server_type = binary['server_type']
        self.server_branch = binary['branch']
        self.server_build = binary['build']
        
        # Lastly, write the new data to disk and commit the config changes.
        with open(os.path.join(self.env, 'env', self.binary), 'wb') as bin:
            bin.write(binary['binary'])
        self.set_config()
        
        return True # We have to return something so that we know it worked ;)
        

    def world_backup(self, world_name, backup_name=None):
        '''backup [world name], [backup_name]
        Runs the backup procedure for the specified world.
        '''
        # If there is no name specified, then go ahead and create one using
        # the current date & time.
        if backup_name == None:
            backup_name = '%s_%s' % (world_name, 
                            datetime.datetime.now().strftime('%Y-%m-%d_%H%M'))
        
        # Perform a save-all & save-off before we run the backup to write all
        # changes to disk.
        self.command('save-all')
        self.command('save-off')
        
        # Now walk through the worlds until we find a name match and run the
        # compress_folder function to generate the zip file archive.
        compress_folder(os.path.join(self.env, 'archive', 'backups', 
                                     '%s.zip' % backup_name), 
                        os.path.join(self.env, 'env', world_name),
                        os.path.join(self.env, 'env', world_name))
    

    def env_snapshot(self, snap_name=None):
        '''snapshot [snapshot name]
        Generates a Snapshot zip file
        '''
        # If there is no name specified, then go ahead and create one using
        # the current date & time.
        if snap_name == None:
            snap_name = '%s_%s' % (self.name,
                            datetime.datetime.now().strftime('%Y-%m-%d_%H%M'))
        
        # Now we need to build the exclusion list.  This list will contain all
        # of the files for each world.  This is needed as we do not want to
        # archive the world data as part of a snapshot.
        excludes = []
        worlds = []
        for dirname, dirs, files in os.walk(os.path.join(self.env, 'env')):
            for f in files:
                exclude = False
                if f in ['level.dat', 'level.dat_old']:
                    worlds.append(dirname)
        for dirname, dirs, files in os.walk(os.path.join(self.env, 'env')):
            for f in files:
                exclude = False
                for world in worlds:
                    if world in dirname:
                        exclude = True
                if exclude:
                    excludes.append(os.path.join(dirname, f))
        
        # And now we run the compress_folder function to generate the archive.
        compress_folder(os.path.join(self.env, 'archive', 'snaps',
                                     '%s.zip' % snap_name),
                        os.path.join(self.env, 'env'),
                        os.path.join(self.env, 'env'),
                        excludes)
                        
        # Now we need to add the baskit configuration file to the snapshot.
        zfile = ZipFile(os.path.join(self.env, 'archive', 'snaps',
                        '%s.zip' % snap_name), 'a')
        zfile.write(self._config_file, 'baskit.config')
        zfile.close()
    

    def env_snap_restore(self, snap_name):
        '''snap_restore [snapshot name]
        Restores a snapshot zipfile.
        '''
        if not self.running():
            # If the server isn't running, then we will extract the contents
            # of the zipfile in place of the current environment.  This means
            # that we will first be deleting all of the existing data
            # associated with this environment before laying the backup into
            # it's place.
            
            # World exclusion list.  We love our worlds and don't wanna see
            # them die ^_^
            exclusion_list = []
            for world in self.worlds:
                world_path = os.path.join(self.env, 'env', world.name)
                for dirname, dirs, files in os.walk(world_path):
                    for f in files:
                        exclusion_list.append(os.path.join(dirname, f))
            
            # And here comes the deleting ;)
            for dirname, dirs, files, in os.walk(os.path.join(self.env, 
                                                              'env')):
                for f in files:
                    fn = os.path.join(dirname, f)
                    if fn not in exclusion_list:
                        os.remove(fn)
                for d in dirs:
                    dn = os.path.join(dirname, d)
                    if dn not in exclusion_list:
                        os.rmdir(dn)
            
            # Now we extract the snapshot into our nice clean environment ;)
            zfile = ZipFile(os.path.join(self.env, 'archive', 'snaps', 
                                         '%s.zip' % snap_name))
            zfile.extractall(os.path.join(self.env, 'env'))
            
            # Now that all of the data is extracted, we need to tell the
            # environment to read it's configuration back in.  Please note
            # that the environment names MUST match for this import to
            # properly work.
            self.get_config(os.path.join(self.env, 'baskit.config'))
            self.set_config()
            
            # Lastly we will remove the now un-needed baskit.config file.
            os.remove(os.path.join(self.env, 'baskit.config'))
            return True
        else:
            return False
    

    def world_restore(self, backup_name, world_name):
        '''world_restore [backup name]
        Restores a world backup.  If restoring to a new world, then the
        associated world object will be created.
        '''
        if not self.running():
            # If the server isn't running, then we will extract the world
            # backup to the world name that was provided.  We will first clean
            # out all of the existing data to make sure that we are applying
            # the backup cleanly.
            
            # Lets clean out the current world data to make way for a nice
            # new world.  As we are doing this the quick-n-dirty way, we will
            # simply delete the while directory tree if it exists and create
            # a new directory.
            world_path = os.path.join(self.env, 'env', world_name)
            try:
                for dirname, dirs, files, in os.walk(world_path):
                    for f in files:
                        fn = os.path.join(dirname, f)
                        os.remove(os.path.join(dirname, f))
                    for d in dirs:
                        dn = os.path.join(dirname, d)
                        os.rmdir(os.path.join(dirname, d))
            except OSError:
                pass
            try:
                os.mkdir(world_path)
            except OSError:
                pass
            
            # Now lets unzip the backup...
            zfile = ZipFile(os.path.join(self.env, 'archive', 'backups',
                                         '%s.zip' % backup_name))
            zfile.extractall(world_path)
            return True
        else:
            return False


    def prsync(self, worlds=None):
        '''prsync
        Performs a sync from the persistent data to the ramdisk
        '''
        if worlds == None:
            worlds = self.worlds
        if self.ramdisk:
            for world in worlds:
                self._check_path(os.path.join(self.env, 'env', world))
                self._check_path(os.path.join(self.env, 'persistent', world))
                self._sync(os.path.join(self.env, 'persistent', world),
                           os.path.join(self.env, 'env', world))
    

    def rpsync(self, worlds=None):
        '''rpsync
        Performs a sync from the ramdisk to the persistent data
        '''
        if worlds == None:
            worlds = self.worlds
        if self.ramdisk:
            for world in worlds:
                self._check_path(os.path.join(self.env, 'env', world))
                self._check_path(os.path.join(self.env, 'persistent', world))
                self._sync(os.path.join(self.env, 'env', world),
                           os.path.join(self.env, 'persistent', world))
    

    def _check_path(self, path):
        if not os.path.exists(path):
            os.makedirs(path)

    def _sync(self, from_path, to_path):
        '''Internal Function
        Convenience function for rsyncing.  Will use a lockfile with the
        world name to prevent multipe syncs from occuring at the same time to
        the same files.
        '''
        rsync_cmd = 'rsync -r -t %s/ %s/' % (from_path, to_path)
        world = os.path.split(from_path)[1]
        lockfile = os.path.join(self.env, 'persistent', '%s.lock' % world)
        
        # Wait for the lockfile to be released if one exists
        while os.path.exists(lockfile):
            time.sleep(0.1)
        
        # Create the lockfile
        lf = open(lockfile, 'w').close()
        
        # Run the Rsync
        run(rsync_cmd)
        
        # Remove the lockfile
        os.remove(lockfile)
