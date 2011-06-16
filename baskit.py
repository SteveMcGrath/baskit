#!/usr/bin/env python
import cmd
import urllib2
import shutil
import os
import datetime
import time
import sys
import re
import getopt
from ConfigParser import ConfigParser
from commands import getoutput as run

global config
global conf_loc

def get_config():
  global config
  global conf_loc
  config = ConfigParser()
  cf_locs = ['/etc/baskit.ini', '~/.baskit.ini', 'baskit.ini']
  for cf_loc in cf_locs:
    if os.path.exists(cf_loc) and not config.has_section('Settings'):
      conf_loc = cf_loc
      config.read(cf_loc)
  if not config.has_section('Settings'):
    print ''.join(['No Config File found.  Creating a default configuration',
                   'in\nthe current location.  This file may exist in any of',
                   'the\nfollowing locations:\n',
                   '  /etc/baskit.ini\n',
                   '  ~/.baskit.ini\n',
                   '  ./baskit.ini'
                    ])
    config.add_section('Settings')
    config.set('Settings', 'environment', os.getcwd())
    config.set('Settings', 'build', '0')
    config.set('Settings', 'branch', 'stable')
    config.set('Settings', 'memory', '1024')
    config.set('Settings', 'flags', '')
    conf_loc = 'baskit.ini'
    update_config()

def update_config():
  global conf_loc
  with open(conf_loc, 'wb') as configfile:
    config.write(configfile)

def alive():
  output = run('screen -wipe bukkit_server')
  if output[:20] == 'There is a screen on':
    return True
  else:
    return False

def console(command):
  if alive():
    run('screen -S bukkit_server -p0 -X stuff \'%s\n\'' % command)

class Baskit(cmd.Cmd):
  prompt = 'baskit> '
  def __init__(self):
    cmd.Cmd.__init__(self)
    get_config()
    self.env = config.get('Settings', 'environment')
    # Create any needed folders if they do not already exist.
    if not os.path.exists(self.env):
      os.makedirs(self.env)
    if not os.path.exists(os.path.join(self.env, 'env')):
      os.makedirs(os.path.join(self.env, 'env'))
    if not os.path.exists(os.path.join(self.env, 'backup')):
      os.makedirs(os.path.join(self.env, 'backup', 'worlds'))
      os.makedirs(os.path.join(self.env, 'backup', 'snapshots'))
    
    # Check to see if java and screen is installed
    need_deps = False
    for package in ['java', 'screen']:
      output = run('which %s' % package)
      chk = re.compile(r'which:\sno\s%s' % package)
      if len(chk.findall(output)) > 0:
        need_deps = True
      if output == '':
        need_deps = True
      
      # If there were any issues, then we need to warn the user.
      if sys.platform != 'win32':
        if need_deps:
          print ''.join(['\nWARNING\n-------\n',
                         'Before you continue, please perform the following ',
                         'operations\nto install the needed software to get ',
                         'baskit working.  We\ndepend on this software in ',
                         'order to properly background and\nrun the bukkit ',
                         'server.  As it is expected for this\nscript to be ',
                         'run as a non-privileged user, we should not\nbe ',
                         'able to run these commands on our own.\n'])
          if sys.platform == 'linux2':
            if run('which apt-get') == '/usr/bin/apt-get':
              print 'sudo apt-get -y install openjdk-6-jre screen\n'
            elif run('which yum') == '/usr/bin/yum' :
              print 'yum -y install java-1.6.0-openjdk screen\n'
            else:
              print 'Please install java & screen.\n'
  
  def do_exit(self, s):
    '''exit
    Exits the Interactive CLI'''
    return True
  
  def do_c(self, s):
    '''c [COMMAND]
    Sends all data after the c to the bukkit console
    '''
    console(s)
    print 'Sent to console: %s' % s
  
  def do_players(self, s, silent=False):
    '''players
    Returns the list of currently connected players.
    '''
    players = []
    replayers = re.compile(r'Connected players: (.+)')
    lfname = os.path.join(self.env, 'env', 'server.log')
    logfile = open(lfname, 'r')
    size = os.stat(lfname)[6]
    logfile.seek(size)
    console('list')
    need_players = True
    while need_players:
      where = logfile.tell()
      line = logfile.readline()
      if not line:
        time.sleep(0.1)
        logfile.seek(where)
      else:
        plist = replayers.findall(line)
        if len(plist) > 0:
          need_players = False
          players = plist[0].split(', ')
    logfile.close()
    if silent:
      return players
    else:
      print 'Players Online: %s' % ', '.join(players)
    
  
  def do_console(self, s):
    '''console
    Opens the Bukkit console  To exit the console type Cntrl+A D
    '''
    os.system('screen -DRS bukkit_server')
  
  def do_update(self, s):
    '''update [OPTIONS]
    Updates the Craftbukkit binary based on the options provided.
    
    -b (--build) [BUILD_NUMBER]   Updates the binary to a specific build.
    -d (--dev)                    Sets the branch flag to dev.
    -t (--test)                   Sets the branch flag to test.
    -s (--stable)                 Sets the branch flag to stable.
    -f (--force)                  Forces the update, even if the build is
                                  older than the current binary.
    '''
    global config
    force = False
    env = config.get('Settings', 'environment')
    branch = config.get('Settings', 'branch')
    cbuild = config.getint('Settings', 'build')
    build = 0
    artifact = '/artifact/target/craftbukkit-0.0.1-SNAPSHOT.jar'
    ci = 'http://ci.bukkit.org/job/dev-CraftBukkit'
    branches = {
     'stable': '%s/promotion/latest/Recommended' % ci,
     'test': '%s/lastStableBuild' % ci,
     'dev': '%s/lastSuccessfulBuild' % ci,
     'build': '%s/' % ci
    }
    opts, args  = getopt.getopt(s.split(), 'b:dtsf',
                                ['build=','dev', 'test', 'stable', 'force'])
    for opt, val in opts:
      if opt in ('-b', '--build'):
        branch = 'build'
        build = int(val)
      if opt in ('-d', '--dev'):
        branch = 'dev'
      if opt in ('-t', '--test'):
        branch = 'test'
      if opt in ('-s', '--stable'):
        branch = 'stable'
      if opt in ('-f', '--force'):
        force = True
    url = branches[branch].replace('{BUILD}', build)
    if branch == 'build':
      branch = 'dev'
    try:
      print 'Parsing ci page for version information...'
      title = re.compile(r'<title>.*#(\d+).*<\/title>',re.DOTALL|re.M)
      page = urllib2.urlopen(url).read()
      build = int(title.findall(page)[0])
    except:
      print 'ERROR: Webpage does not contain version number!'
      return False
    if build > cbuild or force:
      try:
        print 'Downloading craftbukkit to temporary location...'
        cb_bin = urllib2.urlopen(url + artifact).read()
        cb_tmp = open(os.path.join(env, '.craftbukkit.jar'), 'wb')
        cb_tmp.write(cb_bin)
        cb_tmp.close()
      except:
        print 'ERROR: Could not successfully save binary!'
        return False
      print 'Moving new binary into place...'
      shutil.move(os.path.join(env, '.craftbukkit.jar'),
                  os.path.join(env, 'craftbukkit.jar'))
      print 'Updating configuration...'
      config.set('Settings', 'build', build)
      config.set('Settings', 'branch', branch)
      update_config()
      print 'Success! Craftbukkit binary now build %s.' % build
    else:
      print 'Existing binary current. No update needed.'
  
  def do_stop(self, s):
    '''stop [OPTIONS]
    Stops the bukkit binary based on the options provided.
    
    -t (--timer) [SECONDS]        Shuts the server down after the timer
                                  expires.
    --no-players                  Will wait until the server has no players
                                  online before shutting down.
    -n (--notify)                 Notifys the players that the server is in
                                  a shutdown period.
    '''
    players = False
    notify = False
    wait = datetime.datetime.now()
    opts, args  = getopt.getopt(s.split(), 't:n',
                                ['timer=','no-players', 'notify'])
    for opt, val in opts:
      if opt in ('-t', '--timer'):
        wait = datetime.datetime.now() + datetime.timedelta(seconds=int(val))
      if opt in ('--no-players'):
        players = True
      if opt in ('-n', '--notify'):
        notify = True
    while wait > datetime.datetime.now() and not players:
      if players:
        if len(self.do_players('',silent=True)) < 1:
          players = False
      if notify:
        command = 'say SERVER WILL SHUT DOWN '
        countdown = (wait - datetime.datetime.now())
        if countdown.days > -1:
          command += 'IN %s SECONDS ' % countdown.seconds
        if players:
          command += 'WHEN ALL PLAYERS HAVE LEFT'
        console(command)
      time.sleep(30)
    console('stop')
    print 'Server has been told to shutdown.'
  
  def do_start(self, s):
    '''start
    Starts the bukkit server.
    '''
    java = run('which java')
    startup = '%s %s -Xms%sm -Xmx%sm -jar craftbukkit.jar' % (java, 
              config.get('Settings', 'flags'),
              config.get('Settings', 'memory'),
              config.get('Settings', 'memory'))
    screen = 'screen -dmLS bukkit_server bash -c \'%s\'' % startup
    command = 'cd %s;%s' % (config.get('Settings', 'environment'), screen)
    run(command)
    if alive():
      print 'Server startup initiated.'
    else:
      print 'Server startup failed.'
  
  def do_status(self, s):
    '''status
    Returns the running status and basic information about the server.
    '''
    sts = {True: 'ALIVE', False: 'DOWN'}
    print 'Craftbukkit Build %s' % config.get('Settings', 'build')
    print 'Server Status is %s.' % sts[alive()]
  
  def do_snapshot(self, s):
    '''snapshot [OPTIONS]
    Creates, displays, and manages server snapshots.  A server snapshot
    contains the completely functional state of the bukkit server environment.
    Snapshots can only be taken when the server is shit down, so please keep
    this in mind before using.  Snapshots are most useful in making a restore
    point before an upgrade.  Sapshots do NOT contain map or world data.
    
    -l (--list)                   Lists the available snapshots.
    -n (--name) [NAME]            Sets the name of the snapshot.  Default is:
                                    bukkit-[DATE]-[BUILD].snap
    -r (--restore) [NAME]         Restores a snapshot.
    '''
    global config
    env = config.get('Settings', 'environment')
    worlds = []
    desc = None
    cur = datetime.datetime.now()
    name = 'bukkit-%s-%s' % (config.get('Settings', 'build'), 
                             cur.strftime('%Y-%m-%d_%H.%M'))
    opts, args  = getopt.getopt(s.split(), 'ln:r:',
                                ['list', 'name=', 'recover='])
    for opt, val in opts:
      if opt in ('-l', '--list'):
        files = os.listdir(os.path.join(env, 'backup', 'snapshots'))
        backups = []
        for fname in files:
          timestamp = os.stat(os.path.join(env, 'backup', 'snapshots', 
                              fname)).st_mtime
          backups.add((fname.strip('.snap'), 
                       datetime.datetime.fromtimestamp(timestamp)))
        for item in backups:
          print '%-30s %15s' % (item[0], item[1].strftime('%Y-%m-%d %H:%M'))
        return True
      
      if opt in ('-r', '--restore'):
        if alive():
          print 'ERROR: Server cannot be running during snapshot restore!'
          return False
        else:
          snap = os.path.join(env, 'backups', 'snapshots', '%s.snap' % val)
          print 'Starting Snapshot Restoration Process...'
          out = run('tar xzvf %s -C %s' % (snap, env))
          conf = ConfigParser()
          conf.read(os.path.join(env, 'env', 'config.ini'))
          print 'Updating settings based on snapshot...'
          config.set('Settings', 'build', conf.get('Settings', 'build'))
          config.set('Settings', 'branch', conf.get('Settings', 'branch'))
          update_config()
          print 'Cleaning up...'
          os.remove(os.path.join(env, 'env', 'config.ini'))
          print 'Snapshot restore complete.'
          return True

      if opt in ('-n', '--name'):
        name = val
    
    if alive():
      print 'ERROR: Server cannot be running during snapshot!'
      return False
    else:
      print 'Building world exclusions...'
      for item in os.listdir(os.path.join(env, 'env')):
        if os.path.exists(os.path.join(env, 'env', item, 'level.dat')):
          worlds.add('--exclude="env/%s"' % item)
      print 'Copying config into snapshot path...'
      shutil.copyfile(conf_loc, os.path.join(env, 'env', 'config.ini'))
      snap = os.path.join(env, 'backups', 'snapshots', '%s.snap' % name)
      print 'Generating snapshot %s...' % name
      out = run('tar czvf %s -C %s %s' % (snap, env, ' '.join(worlds)))
      print 'Snapshot generation complete.'
      return True
  
  def do_backup(self, s):
    '''backup [OPTIONS] [WORLD]
    Creates, displays, and recovers world backups.
    
    -l (--list)                   Lists the available backups.
    -n (--name) [NAME]            Sets the name of the backup.  Default is:
                                    [WORLD]-[DATE].bck
    -r (--recover) [NAME]         Recovers a backup.
    '''
    name = None
    env = config.get('Settings', 'environment')
    opts, args  = getopt.getopt(s.split(), 'ln:r:',
                                ['list', 'name=', 'recover='])
    world = args[-1]
    for opt, val in opts:
      if opt in ('-l', '--list'):
        files = os.listdir(os.path.join(env, 'backup', 'worlds'))
        backups = []
        for fname in files:
          timestamp = os.stat(os.path.join(env, 'backup', 'worlds', 
                              fname)).st_mtime
          backups.add((fname.strip('.bck'), 
                       datetime.datetime.fromtimestamp(timestamp)))
        for item in backups:
          print '%-30s %15s' % (item[0], item[1].strftime('%Y-%m-%d %H:%M'))
        return True
      if opt in ('-r', '--recover'):
        if alive():
          print 'ERROR: Server cannot be running during restore!'
        else:
          if not os.path.exists(os.path.join(env, 'env', world)):
            os.makedirs(os.path.join(env, 'env', world))
          backup = os.path.join(env, 'backup', 'worlds', '%s.bck' % val)
          path = os.path.join(env, 'env', world)
          print 'Restoring backup %s to %s...' % (val, world)
          run('tar xzvf %s -C %s' % (backup, path))
          print 'Restore complete.'
        return
      if opt in ('-n', '--name'):
        name = val
      
      if name is None:
        cur = datetime.datetime.now()
        name = '%s-%s' % (world, cur.strftime('%Y-%m-%d_%H.%M'))
      backup = os.path.join(env, 'backup', 'worlds', '%s.bck' % name)
      path = os.path.join(env, 'env', world)
      print 'Generating Backup of %s named %s...' % (world, name)
      console('save-all')
      console('save-off')
      run('tar czvf %s -C %s' % (backup, path))
      console('save-on')
      print 'Backup created.'

if __name__ == '__main__':
  if len(sys.argv) > 1:
    Baskit().onecmd(' '.join(sys.argv[1:]))
  else:
    Baskit().cmdloop()