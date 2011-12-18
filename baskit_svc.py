#!/usr/bin/env python
from SimpleXMLRPCServer import SimpleXMLRPCServer
from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler
from commands import getoutput
import json
import datetime
import os
import re
import time
import subprocess
import threaded

config = {}

def load_config():
    '''
    Loads the configuration file into memory.  Yes we are using a JSON file
    for the configuration.  This is needed as we needed the maximum amount
    of flexibility to support running multiple servers off of a singular
    service.
    '''
    global config
    conf = open('baskit_svc.json', 'r')
    config = json.load(conf.read())
    conf.close()

def save_config():
    '''
    Writes the current JSON dictionary to disk.  This should be done every
    time there is a change to the config.
    '''
    global config
    conf = open('baskit_svc.json', 'w')
    conf.write(json.dumps(config, indent=4, sort_keys=True))
    conf.close()
    

class MCWorld(object):
    '''
    This object handles all of the logic related to world management.  This
    includes the heavy lifting for backing up, restoring, ramdisk activities,
    etc.
    
    NOTE: RamDisks are a Linux ONLY Feature.
    '''
    name = None
    enabled = False
    is_ram = False
    auto_mount = False
    disk_path = None

class MCPlugin(object):
    '''
    This object handles all of the plugin installation, management, and
    uninstallation.
    '''

class WebSVC(threaded.Thread):
    '''
    This object houses the bottle web-app for baskit.  The web-app is designed
    to handle all of the management that the CLI can, as well provide a
    generic web server for use in running a minecraft web page as well.
    '''
    enabled = False
    

class MCServer(threaded.Thread):
    '''
    The MCServer object is a per-server thread that handles all communication
    between the XMLRPC service and the minecraft server.  Keep in mind that
    this object has to handle communication for both bukkit and vanila types
    of servers.
    '''
    server = None       # This is the variable that will house the MC proccess
    name = None         # The name of this server instance.  This is specified
                        # incase there are multiple servers launched from a
                        # single baskit server instance.
    bin = None          # Denotes the type of server we are running.  This is
                        # needed to know where we will pull updates from and
                        # if plugins are supported.  Supported types right now
                        # are 'vanilla' and 'bukkit'
    path = None         # Location on disk for the server environment.
    conf = None         # The ConfigParser object that we will be using to
                        # know what we are doing.
    worlds = []         # This is the list of worlds that the minecraft server
                        # will be working with.
    
    def run(self):
        '''
        '''
    
    def get_conf(self, name):
        '''
        Simply gets the configuration options from the config file.
        '''
        self.name = name
        self.path = self.config('path')
        self.bin = self.config('type')
    
    def mc_start(self):
        '''
        Starts the minecraft server
        '''
    
    def mc_stop(self):
        '''
        Stops the minecraft server
        '''
    
    def mc_running(self):
        '''
        Checks to see if the process is still running.  Returns True if the
        server is running and False if not.
        '''
    
    def mc_send(self, msg):
        '''
        Sends a command to the standard input of the minecraft server.
        '''
        self.server.stdin.write('%s\n' % msg)
    
    def mc_snapshot(self, name):
        '''
        Generates a snapshot of the current server configuration, binaries,
        and plugins if there are any
        '''
    
    def mc_backup(self, world, name):
        '''
        Generates a backup of the provided world name and saves it to a new
        archive with the specified name.
        '''
    
    def mc_world_restore(self, world, name):
        '''
        Restores a world backup file to the specified world
        '''
    
    def mc_snap_restore(self, name):
        '''
        Restores a snapshot.
        '''
    
    def mc_update(self, btype='vanilla', build=None):
        '''
        Updates the binary to the specified version.  This action will also
        automatically perfoprm a snapshot before the update starts.
        '''