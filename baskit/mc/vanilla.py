from urllib2 import urlopen
import re

def download(build_type='stable'):
    # https://s3.amazonaws.com/Minecraft.Download/versions/1.7.4/minecraft_server.1.7.4.jar
    '''download [build_type]
    Downloads a vanilla minecraft server binary and returns the contents of
    the download.
    '''
    if build_type == 'stable':
        bin_url = 'MinecraftDownload/launcher/minecraft_server.jar?'
        vrex = re.compile(r'Minecraft (\d(?:\.\d{1,3}){1,3})</a>')
        versions = vrex.findall(urlopen('http://mcupdate.tumblr.com/').read())
        version = versions[0]
    else:
        version = build_type
    contents = urlopen('https://s3.amazonaws.com/Minecraft.Download/versions/'+\
                       '%s/minecraft_server.%s.jar' % (version, version)).read()
    return {
        'server_type': 'vanilla',
        'branch': 'vanilla',
        'build': version,
        'binary': contents
    }