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
    Downloads a bukkit java binary based on either the keywords 'stable',
    'test', or 'dev', or by specifying a build number.  The script will return
    the file contents if successful or will throw an exception if the download
    fails.
    '''
    
    # This is the URL dictionary information for the build_types.  This will
    # likely need to be updated as CI changes or is retired.
    artifact = '/artifact/*zip*/archive.zip'
    ci = 'http://ci.bukkit.org/job/dev-CraftBukkit'
    branches = {
      'stable': '%s/Recommended' % ci,
      'test': '%s/lastStableBuild' % ci,
      'dev': '%s/lastSuccessfulBuild' % ci,
    }
    
    # One of the first things that we will need to do is build the URL for the
    # build page.  This URL will be our starting point for this whole process.
    if build_type in ['stable', 'test', 'dev']:
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
    
    # Now we will download the zip file that we are requesting from CI
    data = StringIO()
    data.write(urlopen(url + artifact).read())
    zfile = ZipFile(data)
    
    # Now we will check for the JAR file and return the contents if we find
    # them.
    contents = None
    for filename in zfile.namelist():
        if filename[-3:].lower() == 'jar':
            contents = zfile.read(filename)
    return {
        'server_type': 'bukkit',
        'branch': branch,
        'build': build,
        'binary': contents
    }