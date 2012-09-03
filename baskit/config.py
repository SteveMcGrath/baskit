import os

def get_config_file():
    config_file = 'baskit.conf'
    if not os.path.exists(config_file):
        config_file = '%s/.baskit.conf' % os.environ['HOME']
    if not os.path.exists(config_file):
        config_file = '/etc/baskit.conf'
    if not os.path.exists(config_file):
        conf_file = open('baskit.conf', 'w')
        conf_file.write(sample_config)
        conf_file.close()
        config_file = 'baskit.conf'
    return config_file

sample_config = '''
[Server]
name            = default
java_args       = 
environment     = .
binary          = server.jar
server_type     = vanilla
server_branch   = stable
server_build    = 1.0
min_mem         = 1024
max_mem         = 1024
worlds          = world, world_nether, world_the_end

[World: world]
ramdisk         = no
automount       = no

[World: world_nether]
ramdisk         = no
automount       = no

[World: world_the_end]
ramdisk         = no
automount       = no
'''