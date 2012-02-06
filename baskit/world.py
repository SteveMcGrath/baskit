import os
import sys
import config
from ConfigParser import ConfigParser
from commands import getoutput as run

class World(object):
    name = None
    env = None
    ramdisk = False
    automount = True
    _config_file = 'baskit.conf'
    
    def __init__(self, name):
        self.name = name
        self._config_file = config.get_config_file()
        try:
            self.get_config()
        except:
            self.set_config()
    
    def get_config(self):
        '''get_config
        Gets the stored configuration from the config file applies those
        settings to the object.
        '''
        section = 'World: %s' % self.name
        conf = ConfigParser()
        conf.read(self._config_file)
        if not conf.has_section(section):
            self.set_config()
        self.env = conf.get('Server', 'environment')
        self.ramdisk = conf.getboolean(section, 'ramdisk')
        self.automount = conf.getboolean(section, 'automount')
    
    def set_config(self):
        '''set_config
        Sets the values in the config file to the values in the object.
        '''
        section = 'World: %s' % self.name
        conf = ConfigParser()
        if os.path.exists(self._config_file):
            conf.read(self._config_file)
        if not conf.has_section(section):
            conf.add_section(section)
        conf.set(section, 'ramdisk', self.ramdisk)
        conf.set(section, 'automount', self.automount)
        with open(self._config_file, 'wb') as configfile:
            conf.write(configfile)
    
    def _tmpfs_size(self):
        '''Internal Function
        Returns the calculated size for the ramdisk.  This is calculated to
        be (current_world_size + 10%).  This function will return kilobytes.
        '''
        total_size = 0
        world_path = os.path.join(self.env, 'persistant', self.name)
        for dirpath, dirs, files in os.walk(world_path):
            for f in filenames:
                total_size = os.path.getsize(os.path.join(dirpath, f))
        return int(float(total_size) * 1.1 / 1024)
    
    def init(self):
        '''init
        Initializes the world for the server to load.  This function mainly
        handles ramdisk setup like mounting the worlds and setting the disk
        sizing.
        '''
        world_path = os.path.join(self.env, 'env', self.name)
        if self.ramdisk:
            if self.automount:
                mountcmd = 'mount -t tmpfs -o size=%sk tmpfs %s' %\
                            (self._tmpfs_size(), world_path)
                if os.environ['USER'] != 'root':
                    mountcmd = 'sudo ' + mountcmd
                run(mountcmd)
                if not os.path.ismount(world_path):
                    raise Exception('World Mount Failed')
            self.prsync()
    
    def cleanup(self):
        '''cleanup
        Handles any housekeeping that may need to be done with the world as
        part of the server shutdown process.
        '''
        world_path = os.path.join(self.env, 'env', self.name)
        if self.ramdisk:
            self.rpsync()
            if self.automount:
                umountcmd = 'umount %s' % world_path
                if os.environ['USER'] != 'root':
                    umountcmd = 'sudo ' + umountcmd
                run(umountcmd)
                if os.path.ismounted(world_path):
                    raise Exception('Would UnMount Failed')
    
    def prsync(self):
        '''prsync
        Performs a sync from the persistant data to the ramdisk
        '''
        if self.ramdisk:
            return self._sync(os.path.join(self.env, 'persistant', self.name),
                              os.path.join(self.env, 'env', self.name))
    
    def rpsync(self):
        '''rpsync
        Performs a sync from the ramdisk to the persistant data
        '''
        if self.ramdisk:
            return self._sync(os.path.join(self.env, 'env', self.name),
                              os.path.join(self.env, 'persistant', self.name))
    
    def _sync(self, from_path, to_path):
        '''Internal Function
        Convenience function for rsyncing.  Will use a lockfile with the
        world name to prevent multipe syncs from occuring at the same time to
        the same files.
        '''
        rsync_cmd = 'rsync -r -t -v %s %s' % (from_path, to_path)
        lockfile = os.path.join(self.env, 'persistant', '%s.lock' % self.name)
        
        # Wait for the lockfile to be released if one exists
        while os.path.exists(lockfile):
            time.sleep(0.1)
        
        # Create the lockfile
        lf = open(lockfile, 'w').close()
        
        # Run the Rsync
        run(rsync_cmd)
        
        # Remove the lockfile
        os.remove(lockfile)
    
    def resize_tmpfs(self):
        '''resize_tmpfs
        Resizes the tmpfs mount to maintain the +10 percent space requirement
        '''
        world_path = os.path.join(self.env, 'env', self.name)
        if self.ramdisk:
            if self.automount:
                mountcmd = 'mount -o remount -o size=%sk %s' %\
                            (self._tmpfs_size(), world_path)
                if os.environ['USER'] != 'root':
                    mountcmd = 'sudo ' + mountcmd
                run(mountcmd)