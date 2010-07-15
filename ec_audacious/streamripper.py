#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = "Ryan McGuire (ryan@enigmacurry.com)"
__date__   = "Wed Jul 14 20:10:38 2010"

"""Wrapper for streamripper that incorporates an active filesystem monitor to
queue downloaded tracks into audacious

Typical usage is to alias streamstripper to this script:

alias streamstripper="python -m ec_audacious.streamstripper"

If this script is started with the --audacious argument, the destination
directory will be monitored (except for the incomplete directory) and any new
tracks downloaded will be queued into audacious.

All options to this script get passed on to the underlying streamstripper
program except for --audacious.
"""

import sys
import os
import threading
import subprocess
import dynamic_filesystem_playlist

class StreamripperThread(threading.Thread):
    def __init__(self, args):
        self.args = args
        threading.Thread.__init__(self)
    def run(self):
        subprocess.Popen(["streamripper"]+self.args[1:]).communicate()

class FSMonitorThread(threading.Thread):
    def __init__(self, args):
        self.args = args
        threading.Thread.__init__(self)
    def run(self):
        dynamic_filesystem_playlist.main(self.args)
        
def main():
    """Start up streamripper, passing all the arguments to it,

    If the --audacious argument is present, start up a dynamic_filesystem_monitor
    to feed the downloaded tracks to audacious"""
    try:
        try:
            d_idx = sys.argv.index("-d")
            dest_path = sys.argv[d_idx+1]
            recursive = False
        except ValueError, IndexError:
            dest_path = os.curdir
            recursive = True
        try:
            sys.argv.remove("--audacious")
        except ValueError:
            pass
        else:
            #Start the dynamic_filesystem_playlist in it's own thread
            fsm_args = ["",dest_path]
            if recursive:
                fsm_args.append("-r")
            fsmonitor = FSMonitorThread(fsm_args)
            fsmonitor.daemon = True
            fsmonitor.start()
        #Start streamripper in it's own thread:
        try:
            streamripper = StreamripperThread(sys.argv)
            streamripper.start()
        finally:
            streamripper.join()
    except KeyboardInterrupt:
        pass
    
if __name__ == '__main__':
    main()
