from urllib2 import urlopen
import json

def download(build_type='rb'):
    '''download [build name/number]
    Downloads a bukkit java binary based on either the keywords 'stable',
    'test', or 'dev', or by specifying a build number.  The script will return
    the file contents if successful or will throw an exception if the download
    fails.
    '''
    
    if build_type == 'stable':
        build_type = 'rb'

    # Thanks to the new API to talk to for CB versions, we no longer need to
    # web scrape.
    base = 'http://dl.bukkit.org/api/1.0/downloads/projects/craftbukkit/view'
    if build_type in ['rb', 'beta', 'dev']:
        url = '%s/latest-%s/' % (base, build_type)
    else:
        url = '%s/build-%s/' % (base, build_type)

    # Look at that, it's all pretty json now, no more 100 lines of code ^_^
    ci = json.loads(urlopen(url).read())

    return {
        'server_type': 'bukkit',
        'branch': ci['channel']['slug'],
        'build': ci['build_number'],
        'binary': urlopen(ci['file']['url']).read()
    }