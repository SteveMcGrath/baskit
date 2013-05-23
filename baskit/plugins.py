import cmd
import os
import config
import shutil
from bukget import api
from hashlib import md5
from ConfigParser import ConfigParser
from zipfile import ZipFile, BadZipfile
from StringIO import StringIO

class Plugins(cmd.Cmd):
    def __init__(self, server):
        overrides = {
            'spigot': 'bukkit',
        }
        cmd.Cmd.__init__(self)
        self.server = server
        self.plugin_path = os.path.join(self.server.env, 'env', 'plugins')
        if server.server_type in overrides:
            self.stype = overrides[server.server_type]
        else:
            self.stype = server.server_type


    def get_plugin(self, name):
        '''
        Returns a dictionary with the plugin information.
        '''
        stanza = 'Plugin: %s' % name.lower()
        conf = ConfigParser()
        conf.read(config.get_config_file())
        if conf.has_section(stanza):
            return {
                'name': conf.get(stanza, 'name'),
                'jar': conf.get(stanza, 'jar'),
                'bukget': conf.get(stanza, 'bukget'),
                'md5': conf.get(stanza, 'md5'),
                'version': conf.get(stanza, 'version'),
                'enabled': conf.getboolean(stanza, 'enabled'),
            }
        else:
            return None


    def delete_plugin(self, name):
        '''
        Removes the plugin from the server.
        '''
        plug = self.get_plugin(name)

        # We are setting these here as I'm lazy and we will be using these a
        # lot in this function.
        pjoin = os.path.join
        exists = os.path.exists

        if exists(pjoin(self.plugin_path, plug['jar'])):
            os.remove(pjoin(self.plugin_path, plug['jar']))
        if exists(pjoin(self.plugin_path, plug['jar'][:-4])):
            shutil.rmtree(pjoin(self.plugin_path, plug['jar'][:-4]))
        if exists(pjoin('%s_diabled' % self.plugin_path, plug['jar'])):
            os.remote(pjoin('%s_diabled' % self.plugin_path, plug['jar']))
        conf = ConfigParser()
        conf.read(config.get_config_file())
        conf.remove_section('Plugin: %s' % name.lower())
        with open(config.get_config_file(), 'w') as cfile:
            conf.write(cfile)
        print 'Plugin %s removed and (hopefully) all associated data.' % plug['name']



    def plugin_listing(self):
        '''
        Returns a list of dictionaries with the installed plugins that baskit
        is aware of.
        '''
        conf = ConfigParser()
        conf.read(config.get_config_file())
        plugins = []
        for section in conf.sections():
            if 'Plugin:' in section:
                plugins.append(self.get_plugin(conf.get(section, 'name')))
        return plugins


    def save_plugin(self, name, **settings):
        '''
        Saves any changes to the config file.
        '''
        stanza = 'Plugin: %s' % name.lower()
        conf = ConfigParser()
        conf.read(config.get_config_file())
        settings['name'] = name
        if not conf.has_section(stanza):
            conf.add_section(stanza)
        for item in settings:
            conf.set(stanza, item, settings[item])
        with open(config.get_config_file(), 'w') as cfile:
            conf.write(cfile)


    def get_plugin_info(self, filename):
        '''
        Will get the main & version information from the plugin and will
        query BukGet to look for a match.  If we do find a match we will add
        the plugin to your list of managed plugins within baskit.
        '''
        return api.search({
            'field': 'versions.md5', 
            'action': '=',
            'value': self.hash_file(filename)
        })


    def hash_file(self, filename):
        '''
        Returns the md5sum of a file.
        '''
        dataobj = open(filename)
        md5hash = md5()
        md5hash.update(dataobj.read())
        dataobj.close()
        return md5hash.hexdigest()


    def display_plugin(self, plugin, check=False, *opts):
        '''
        Outputs to Screen information about the plugin.
        '''
        opts = list(opts)
        conf = self.get_plugin(plugin)
        if check:
            ret = api.plugin_details(self.stype, conf['bukget'])
            if ret is not None:
                current = ret['versions'][0]
                for version in ret['versions']:
                    if conf['version'] == version['version']:
                        if current['date'] > version['date']:
                            opts.append('Current: %s' % current['version'])
        print '%-20s %-10s %s' % (conf['name'], conf['version'], ', '.join(opts))


    def install(self, plugin, version):
        '''
        Installs or Updates a Plugin.
        '''
        plug = api.plugin_details(self.stype, plugin, version)
        if plug == None:
            print 'Not a Valid BukGet Plugin Name...'
            return
        pname = plug['versions'][0]['filename']
        data = api.plugin_download(self.stype, plugin, version)
        if pname[-3:].lower() == 'jar':
            with open(os.path.join(self.plugin_path, 
                      pname[:-3] + 'jar'), 'wb') as jar:
                jar.write(data)
        if pname[-3:].lower() == 'zip':
            dataobj = StringIO()
            dataobj.write(data)
            try:
                zfile = ZipFile(dataobj)
            except BadZipfile:
                print 'ERROR: Corrupt Zip File.  Could Not Install'
                return
            zfile.extractall(self.plugin_path)
            print '\n'.join([
                'NOTE: As this plugin was bundled as a zip file, it\'s',
                '      impossible to determine if the plugin was installed',
                '      correctly.  Please check the plugin installtion to be',
                '      sure that everything is set up correctly.'])
            dataobj.close()
        self.save_plugin(plug['plugin_name'].lower(),
                         jar=pname[:-3] + 'jar',
                         bukget=plug['slug'],
                         md5=plug['versions'][0]['md5'],
                         version=plug['versions'][0]['version'],
                         enabled=True)
        print 'Plugin %s/%s installed' % (plug['plugin_name'], plug['versions'][0]['version'])



    def do_help(self, s):
        if s == '': self.onecmd('help help')
        else:
            cmd.Cmd.do_help(self, s) 


    def help_help(self):
        print '''Plugin Management Functions 

        Info will eventually go here.....
        '''
    

    def do_scan(self, s):
        '''scan
        Scans the currently installed plugins and will add any not currently
        being tracked into the baskit config as well as update any version
        numbers for plugins that have been updated manually.
        '''
        plugins = self.plugin_listing()
        for filename in os.listdir(self.plugin_path):
            filepath = os.path.join(self.plugin_path, filename)
            if 'jar' == filename[-3:].lower():
                p = False
                for plugin in plugins:
                    if plugin['jar'] == filename:
                        p = plugin
                if p:
                    plug = api.plugin_details(self.stype, p['bukget'])
                else:
                    plugs = self.get_plugin_info(filepath)
                    if len(plugs) == 0:
                        print 'Plugin %s does not exist in BukGet.' % filename
                        continue
                    elif len(plugs) == 1:
                        plug = plugs[0]
                    if len(plugs) > 1:
                        print 'Multiple Matches for %s.  Please Select One (default 0)' % filename
                        for item in plugs:
                            print '%2d: %-30s %s' % (plugs.index(item),
                                                     item['plugin_name'],
                                                     item['slug'])
                        try:
                            plug = plugs[int(raw_input('Plugin ID : '))]
                        except ValueError:
                            plug = plugs[0]
                filehash = self.hash_file(filepath)
                notes = []
                for version in plug['versions']:
                    if version['md5'] == filehash:
                        self.save_plugin(plug['plugin_name'].lower(),
                            jar=filename,
                            bukget=plug['slug'],
                            md5=filehash,
                            version=version['version'],
                            enabled=True)
                        if p and p['md5'] != version['md5']:
                            notes.append('Manually Updated')
                self.display_plugin(plug['plugin_name'].lower(), True, *notes)


    def do_search(self, s):
        '''search [search_string]
        Searches for a given plugin name.
        '''
        results = api.search({
            'field': 'plugin_name', 
            'action': 'like',
            'value': s
        })
        print '%-20s %-20s %s' % ('Plugin Name', 'Install Name', 'Description')
        print '%s %s %s' % ('-' * 20, '-' * 20, '-' * 38)
        print '\n'.join(['%-20s %-20s %s' % (p['plugin_name'], p['slug'], p['description']) for p in results])


    def do_list(self, s):
        '''list [check]
        Lists the currently installed plugins and their versions.  Will also 
        note which plugins have updates available.
        '''
        check = False
        if s == 'check': check = True
        for plugin in self.plugin_listing():
            self.display_plugin(plugin['name'], check=check)


    def do_update(self, s):
        '''update [plugin_name|all] [version]
        Will update a singular plugin (or all plugins if specified) to either
        current or the version specified
        '''
        dset = s.split()
        plugin = None
        version = 'latest'
        if len(dset) > 0: plugin = dset[0].lower()
        if len(dset) > 1: version = dset[1]
        if plugin:
            if plugin == 'all':
                for plug in self.plugin_listing():
                    self.install(plug['name'], version)
            else:
                self.install(plugin, version)
        else:
            print 'No Options Defined!'
    

    def do_install(self, s):
        '''install [plugin_name] [version]
        Installs either the latest version, or the version specified.
        '''
        dset = s.split()
        plugin = None
        version = 'latest'
        if len(dset) > 0: plugin = dset[0].lower()
        if len(dset) > 1: version = dset[1]
        if plugin:
            self.install(plugin, version)
    

    def do_remove(self, s):
        '''remove [plugin_name]
        Removes the specified plugin binary.  Please note that as many plugins
        will create data structures themselves, removing the plugin binary will
        NOT necessarially remove all fo the associated configuration and data 
        files.
        '''
        if self.server.running():
            print 'Please shutdown the server before permanently removing plugins.'
            return
        if self.get_plugin(s) is None:
            print 'Invalid Plugin Name...'
            return
        if raw_input('Delete %s ? (NO/yes) :' % s).lower() in ['y', 'yes']:
            self.delete_plugin(s)
    

    def do_enable(self, s):
        '''enable [plugin_name]
        Enables a disabled plugin.  This will simply move the plugin binary back
        into the plugin folder, effectively enabling the plugin.
        '''
        plugin = self.get_plugin(s)
        if plugin is not None and os.path.exists(os.path.join('%s_disabled' % self.plugin_path, plugin['jar'])):
            shutil.move(os.path.join('%s_disabled' % self.plugin_path, plugin['jar']), 
                        os.path.join(self.plugin_path, plugin['jar']))
            self.save_plugin(s, status='enabled')
            print '%s enabled.  Restart the servert to activate.' % plugin['name']
        else:
            print '%s is not disabled.' % plugin['name']


    def do_disable(self, s):
        '''disable [plugin_name]
        Disables a plugin.  This will move the plugin binary (not any of the 
        associated data) into the disabled-plugins folder.  This is designed to
        be a non-destructive way to troubleshoot potential issues.
        '''
        plugin = self.get_plugin(s)
        if not os.path.exists('%s_disabled' % self.plugin_path):
            os.makedirs('%s_disabled' % self.plugin_path)
        if plugin is not None and os.path.exists(os.path.join(self.plugin_path, plugin['jar'])):
            shutil.move(os.path.join(self.plugin_path, plugin['jar']), 
                        os.path.join('%s_disabled' % self.plugin_path, plugin['jar']))
            self.save_plugin(s, status='disabled')
            print '%s disabled.  Restart the server to deactivate.' % plugin['name']
        else:
            print '%s is not installed.' % plugin['name']
