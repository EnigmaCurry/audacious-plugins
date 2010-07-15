#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = "Ryan McGuire (ryan@enigmacurry.com)"
__date__   = "Mon Jul 12 23:51:33 2010"

"""
This tool monitors a given directory for the creation of new media files to
feed into your Audacious playlist on the fly.

I wanted to save a shoutcast stream with streamripper but be able to play the
saved files immediately, but I needed a way to queue the files so that the
playlist was never exhausted. Here's the result.

See LICENSE.txt for information regarding your rights to this tool.
"""

import dbus
import pyinotify
import optparse
import os
import sys
import fnmatch
import urllib
import time
import logging
import shlex
import subprocess

logging.basicConfig()
logger = logging.getLogger("main")

class FileEventHandler(pyinotify.ProcessEvent):
    def __init__(self, options):
        self.audacious = Audacious()
        self.file_types = [x.lower() for x in options.file_types.split(",")]
        self.options = options
    def process_IN_CREATE(self, event):
        self.process(event)
    def process_IN_MOVED_TO(self, event):
        self.process(event)
    def process(self, event):
        for ft in self.file_types:
            if fnmatch.fnmatch(event.pathname.lower(),"*."+ft):
                break
        else:
            return
        uri = "file://"+urllib.quote(event.pathname)
        if self.options.no_dupes and uri in self.audacious.get_tracklist():
            return
        #Don't add things in an "incomplete" dir
        if "incomplete" in event.pathname.split(os.path.sep):
            return
        logger.info("Adding Track: "+event.pathname)
        #Add the track
        self.audacious.add_track(uri)
        
class Audacious(object):
    def __init__(self):
        try:
            self.dbus_setup()
        except dbus.exceptions.DBusException:
            #Maybe audacious wasn't running, let's start it and try again.
            subprocess.Popen(shlex.split("sh -c 'audacious &'"))
            time.sleep(5)
            self.dbus_setup()
    def dbus_setup(self):
        self.bus = dbus.SessionBus()
        root_obj       = self.bus.get_object("org.mpris.audacious", '/')
        player_obj     = self.bus.get_object("org.mpris.audacious", '/Player')
        tracklist_obj  = self.bus.get_object("org.mpris.audacious", '/TrackList')
        org_obj        = self.bus.get_object("org.mpris.audacious", '/org/atheme/audacious')
        self.root      = dbus.Interface(root_obj, dbus_interface='org.freedesktop.MediaPlayer')
        self.player    = dbus.Interface(player_obj, dbus_interface='org.freedesktop.MediaPlayer')
        self.tracklist = dbus.Interface(tracklist_obj, dbus_interface='org.freedesktop.MediaPlayer')
        self.org       = dbus.Interface(org_obj, dbus_interface='org.atheme.audacious')
    def get_tracklist(self):
        tracklist_files = set()
        for x in range(0,self.tracklist.GetLength()):
            fn = str(self.tracklist.GetMetadata(x)['location'])
            tracklist_files.add(fn)
        return tracklist_files
    def add_track(self, path):
        try:
            self.tracklist.AddTrack(path,False)
            #Get the track info, just so the playlist display updates
            self.tracklist.GetMetadata(self.tracklist.GetLength()-1)
        except dbus.exceptions.DBusException:
            logger.error("Could not connect to Audacious.. is it running?")

def monitor(options):
    handler = FileEventHandler(options)
    wm = pyinotify.WatchManager()
    notifier = pyinotify.Notifier(wm, handler)
    path = os.path.abspath(options.path)
    wm.add_watch(path, pyinotify.IN_CREATE|pyinotify.IN_MOVED_TO, rec=options.recursive)
    logger.info("Watching %s for new media files of type %s ..." % (path,options.file_types))
    notifier.loop()

def main(args):
    usage = "%prog [options] PATH_TO_MONITOR"
    description = "Monitors a given PATH for newly created audio files and "\
    "automatically adds them to the audacious tracklist."
    parser = optparse.OptionParser(usage, description=description, version="%prog 0.1")
    parser.add_option("-r","--recursive",dest="recursive",
                      action="store_true",default=False,
                      help="Recursively monitor the path")
    parser.add_option("-q","--quiet",dest="quiet",
                      action="store_true",default=False,
                      help="Be more verbose")
    parser.add_option("-t","--file-types",dest="file_types",
                     default="mp3,ogg,flac",
                     help="file extensions of files to add to tracklist")
    parser.add_option("-d","--no-dupes",dest="no_dupes",
                      action="store_true",default=False,
                      help="Only add files not already in the Audacious tracklist")
    (options, pargs) = parser.parse_args(args)
    if len(pargs) != 2:
        parser.print_help()
        sys.exit(1)
    if not options.quiet:
        logger.setLevel(logging.INFO)
    options.path = pargs[1]
    monitor(options)
    
if __name__ == "__main__":
    main(sys.argv)
