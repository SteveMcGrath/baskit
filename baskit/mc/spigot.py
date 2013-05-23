from urllib2 import urlopen
from StringIO import StringIO
from zipfile import ZipFile
import re

class Error(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

def download(build_type='stable'):
    '''download [build name/number]
    Downloads a bukkit java binary based on either the keywords 'stable', or
    'dev', or by specifying a build number.  The script will return the file 
    contents if successful or will throw an exception if the download fails.
    '''
    
    # This is the URL dictionary information for the build_types.  This will
    # likely need to be updated as CI changes or is retired.
    artifact = '/artifact/Spigot-Server/target/spigot.jar'
    ci = 'http://ci.md-5.net/job/Spigot/'
    branches = {
      'stable': '%s/lastStableBuild' % ci,
      'dev': '%s/lastSuccessfulBuild' % ci,
    }
    
    # One of the first things that we will need to do is build the URL for the
    # build page.  This URL will be our starting point for this whole process.
    if build_type in ['stable', 'dev']:
        url = branches[build_type]
        branch = build_type
    else:
        branch = 'dev'
        build = int(build_type)
        url = '%s/%s' % (ci, build)
    
    # Yes I know this is ugly as we are using a try block that is accepting
    # any error and handling it, however I admit my laziness and simply want
    # to get this module running.
    try:
        title = re.compile(r'<title>.*#(\d+).*<\/title>',re.DOTALL|re.M)
        build = int(title.findall(urlopen(url).read())[0])
    except:
        raise Error('Webpage does not contain version number!')

    contents = urlopen(url + artifact).read()
    return {
        'server_type': 'spigot',
        'branch': branch,
        'build': build,
        'binary': contents
    }