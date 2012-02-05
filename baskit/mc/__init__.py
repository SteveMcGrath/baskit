import bukkit
import vanilla
import spout
import canary

def download(server_type='vanilla', build_type='stable'):
    '''download [server_type], [build_type]
    An abstraction layer to the various server binaries that are supported.
    By default will download the latest stable vanilla server, however can be
    told to download any of the server binaries below:
    
    vanilla (stable)
    bukkit (stable, test, dev, [build_no])
    spout (NA)
    canary (NA)
    '''
    
    if server_type == 'vanilla':
        return vanilla.download(build_type)
    if server_type == 'bukkit':
        return bukkit.download(build_type)
    if server_type == 'spout':
        return spout.download(build_type)
    #if server_type == 'canary':
    #    return canary.download(build_type)
    else:
        return None