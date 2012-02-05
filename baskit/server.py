import os
import sys
from commands import getoutput as run
from ConfigParser import ConfigParser

from world import World
import mc
import screen

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
    
    def __init__(self, name, config_file='baskit.conf'):
        '''Baskit server initialization
        '''
        self.name = name
        if not os.path.exists(config_file):
            config_file = '%s/.baskit.conf' % sys.env['HOME']
        if not os.path.exists(config_file):
            config_file = '/etc/baskit.conf'
        if not os.path.exists(config_file):
            self.set_config()
        self._config_file = config_file
        self.get_config()
    
    def running(self):
        '''running
        Returns True/False whether the server is running or not.
        '''
        return screen.exists('mc_%s' % self.name):
    
    def get_config(self):
        '''get_config
        Fetches the configuration for the server and adjusts the variables
        within the server object to match the configuration.
        '''
        
        # Initializing the configration parser and reading the config file.
        config = ConfigParser()
        config.read(self._config_file)
        
        # Setting the section name and fetching the information from the
        # configuration file and applying those values to the appropriate
        # object variable.
        section = 'Server: %s' % self.name
        self.java_args = config.get(section, 'java_args')
        self.binary = config.get(section, 'binary')
        self.env = config.get(section, 'environment')
        self.server_type = config.get(section, 'server_type')
        self.server_branch = config.get(section, 'server_branch')
        self.server_build = config.get(section, 'server_build')
        self.min_mem = config.get(section, 'min_mem')
        self.max_mem = config.get(section, 'max_mem')
        
        # Linking in the worlds that we are aware of to the server
        # configuration.  This is normally entirely optional unless you would
        # like to use the backup & restore functions, or if you would like to
        # use ramdisks.
        for world_name in config.get(section, 'worlds').split(','):
            world_name = world_name.strip()
            self.worlds.append(World(world_name))
    
    def set_config(self):
        '''set_config
        Commits the current configuration of the server object to the config
        file.  This i also useful in generating a new configuration
        declaration if this is a new installation or if you will be running
        multiple servers.
        '''
        
        # Initializing the configuration parser and reading in the existing
        # data if there is any.
        config = ConfigParser()
        if os.path.exists(self._config_file):
            config.read(self._config_file)
        
        # Setting the section name and commiting the variables to the config
        # file.
        section = 'Server: %s' % self.name
        config.set(section, 'binary', self.binary)
        config.set(section, 'environment', self.env)
        config.set(section, 'server_type', self.server_type)
        config.set(section, 'server_branch', self.server_branch)
        config.set(section, 'server_build', self.server_build)
        config.set(section, 'min_memory', self.min_mem)
        config.set(section, 'max_memory', self.max_mem)
        config.set(section, 'java_args', self.java_args)
        
        # Now to get the list of world names that are configured with this
        # server and add them to the 'worlds' option in the configuration
        # stanza.
        wnames = []
        for world in self.worlds:
            wnames.append(world.name)
        config.set(section, 'worlds', ', '.join(wnames))
        
        # Lastly, we need to write the config file to disk.
        with open(self._config_file, 'wb') as configfile:
            config.write(configfile)
        
    
    def command(self, command, restring=None):
        '''command [command]
        Sends the specified command to the server console and will optionally
        wait for a given regex to return a match from the server.log before
        returning.
        '''
        
        if restring is not None:
            # If a regex was specified for interactivity, then we will need
            # to open the server.log file and seek to the end of the file
            # before we actually do anything.  Once we send the command that
            # was specified we will use the end of the file as a starting
            # point for the parsing.
            relog = re.compile(restring)
            logfile = open(os.path.join(self.env, 'env', 'server.log'), 'r')
            size = os.stat(os.path.join(self.env, 'env', 'server.log'))[6]
            logfile.seek(size)
        
        # Sending the command to the screen session
        screen.send('mc_%s' % self.name, command)
        
        if restring is not None:
            # Now we will start parsing through all of the log data that the
            # server is returning, using the now old EOF as a starting point.
            # We will run the regex that we had compiled to the relog variable
            # on every line until we get a match, then return those matches.
            found = False
            while not found:
                where = logfile.tell()
                line - logfile.readline()
                if not line:
                    time.sleep(0.1)
                    logfile.seek(where)
                else:
                    if len(relog.findall(line)) > 0:
                        found = True
            logfile.close()
            return relog.findall(line)
        
        # If there was no regex specified, then there is nothing to return.
        return None  
    
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
            for world in self.worlds:
                world.init()
            
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
            screen.new('mc_%s' % self.name, startup)
    
    def stop(self):
        '''stop
        Tells the minecraft server to stop.
        '''
        # First thing we will need to is tell the server to stop and wait for
        # the server to finish shutting down.
        self.console('stop')
        while self.running():
            time.sleep(0.1)
        
        # Then we will run the cleanup on every world.  Just like world inits,
        # generally there shouldn't be much going on here, however if there
        # are ramdisk worlds, then we will be performing some actions here in
        # order to properly cleanup and make sure all the ramdisk data is
        # synced.
        for world in self.worlds:
            world.cleanup()
    
    def players(self):
        '''players
        Returns the list of currently commected players
        '''
        repl = re.compile(r' ([^,]*)')
        line = console('listt', r'Connected players:(.*)').strip('\n')
        players = repl.findall(line)
        return players
    
    def update(self, build_type='stable', bin_type=None):
        if self.running():
            return False
        
        if bin_type == None:
            bin_type = self.server_type
        
        # Download the new server binary
        binary = mc.download(bin_type, build_type)
        
        # Setting the new variable definitions...
        self.server_type = binary['server_type']
        self.server_branch = binary['branch']
        self.server_build = binary['build']
        
        # Lastly, write the new data to disk and commit the config changes.
        with open(os.path.join(self.env, 'env', self.binary), 'wb') as bin:
            bin.write(binary['binary'])
        self.set_config()
        
        return True # We have to return something so that we know it worked ;)
        
        