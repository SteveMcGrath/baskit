## baskit

------

**NOTE**:  The mainline version of baskit is slated to be depricated for the
ng/v2 codebase currently under active development.  Support for this codebase
will be offered until the new version is considered stable enough for general
consumption

------

baskit is a Python wrapper for a bukkit server

It currently uses screen to manage the console.

Supports an interactive CLI mode as well as a command-line interface.
The command-line interface is suitable for calling from cron.

For more information see the [baskit page](http://bukget.org/baskit) at bukget.org

When baskit is first run, it will generate a baskit.ini file in the current directory,
as well as the 'normal' environment directories.

If you are running a dedicated server the /opt/minecraft directory is suggested.

Once you have created the configuration file, you can run baskit from any directory 
as long as the configuration file can be located. 
baskit will currently look in `/etc/baskit.ini`, `~/.baskit.ini` and `./baskit.ini`

Note that some of baskit's commands will attempt to update this file while running 
so it would be convenient if it had rights to do so.

Commands are currently implemented to support:
<table>
<tr><td>Command</td><td>Description</td></tr>
<tr><td>`help [command]`</td><td>Lists and explains commands and options</td></tr>
<tr><td>`start`</td><td>Starts the server (if it is not already running)</td></tr>
<tr><td>`stop`</td><td>Stops the sever (if it is running)</td></tr>
<tr><td>`status`</td><td>Display the current server build and whether the server is ALIVE or DOWN</td></tr>
<tr><td>`update`</td><td>Updates the server file (see help for more information)</td></tr>
<tr><td>`snapshot`</td><td>save or restore server configuration (see help for more information)</td></tr>
<tr><td>`backup [world]`</td><td>backup or restore one world (see help for more information)</td></tr>
<tr><td>`c (command)`</td><td>Send command to the console (if the server is running)</td></tr>
<tr><td>`console`</td><td>Attach to the server console screen. <br/>
You will see a reminder of the keys to use to exit the console. <br/>
(ctrl-a ctrl-d)</td></tr>
<tr><td>`players`</td><td>List the currently connected players</td></tr>
<tr><td>`exit`</td><td>exit the interactive CLI</td></tr>
</table>

Recently implemented support for Ram Disks added or modified the following commands:
<table>
<tr><td>Command</td><td>Description</td></tr>
<tr><td>`start`</td><td>Optionally mount ramdisk(s). Populate ramdisk(s) with world data. Start the server.</td></tr>
<tr><td>`stop`</td><td>Stop the server. Sync world data. Optionally unmount ramdisk(s).</td></tr>
<tr><td>`merge`</td><td>Will sync data from ramdisk(s) to persistent world folder(s).
Suitable for use in cron tasks.</td></tr>
<tr><td>`crashfix`</td><td>Used following a server stop not initiated by baskit.
Will sync data to persistent world folder(s) and optionally unmount ramdisk(s).</td></tr>
<tr><td>`backup [world]`</td><td>Will perform a merge and backup from the persistent world folder.</td></tr>
</table>

sudoers line to allow passwordless mount and unmount of ramdisks in the /opt/minecraft/env
folder for members of the minecraft group. Modify as necessary for your target users and for
your environment folder. Put the line towards the bottom of sudoers. Use visudo to edit the
sudoers file.

`%minecraft   ALL= NOPASSWD: /bin/mount -t tmpfs none /opt/minecraft/env/*, /bin/umount -t tmpfs /opt/minecraft/env/*`
