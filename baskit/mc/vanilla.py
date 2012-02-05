from urllib2 import urlopen
import re

def download(build_type='stable'):
    '''download [build_type]
    Downloads a vanilla minecraft server binary and returns the contents of
    the download.
    '''
    bin_url = 'MinecraftDownload/launcher/minecraft_server.jar?'
    vrex = re.compile(r'Minecraft (\d\.\d{1,3})</a>')
    versions = vrex.findall(urlopen('http://mcupdate.tumblr.com/').read())
    contents = urlopen('https://s3.amazonaws.com/' + bin_url).read()
    return {
        'server_type': 'vanilla',
        'branch': 'stable',
        'build': versions[0],
        'binary': contents
    }