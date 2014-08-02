#!/usr/bin/env python
from TorrentCommander import TorrentCommander
from pytpb import ThePirateBay
from time import sleep
import re
import os
import json
import pdb, sys
from exceptions import Exception
import logging
from logging import handlers

MINUTE = 60
HOUR = 60*MINUTE
DAY = 24*HOUR

#TODO:
# Logging?
# Interrupt/Debugging signals

class SetupController(object):
    """
    This module will be used to control the whole setup
    """
    def __init__(self):
        config_file = os.environ["HOME"]+"/.comic_setup.json"
        self.week_file = os.environ["HOME"]+"/.next_week"
        self.torrent_commander = TorrentCommander(os.environ["HOME"]+"/.comic_setup.json")
        self.pirate_bay = ThePirateBay()
        f = open(self.week_file,"r")
        self.next_week = int(f.readline().split("\n")[0])
        f.close()
        self.config = json.load(open(config_file))
        self.logger = logging.getLogger("SetupController")
        self.logger.setLevel(logging.INFO)

    def main(self):
        """
        Main control loop:
            1) Check current running torrents and stop them on complete
            2) Search for new torrents
            3) Wait for next iteration
        """
        while True:
            self.torrent_commander.cleanup_completed_torrents()
            self.clean_up_directory()
            self.logger.info("Finished Cleanup")
            new_torrents = self.find_torrents()
            #sys.exit(-1)
            self.torrent_commander.add_torrents(new_torrents)
            self.logger.info("Finished Adding Torrents")
            sleep(60*MINUTE)

    def clean_up_directory(self):
        pass

    def update_week(self):
        #this might be costly but it's safer this way
        self.next_week += 1
        #saving the next week search term
        f = open(self.week_file,"w")
        f.write(str(self.next_week))
        f.close()

    def find_torrents(self,max_torrents=10):
        torrents_to_download = list()
        search_results = self.pirate_bay.search(self.config['search_term'])
        while len(torrents_to_download)<max_torrents: #search loop for this week and on
            # The line termination might be a problem in the future...
            week_search = self.config['search_term']  + str(self.next_week) #+ "\s*$"
            self.logger.info("Searching for "+week_search)
            found = False
            for result in search_results:
                self.logger.debug("Found results %s"%(result['name']))
                if re.match("\s*".join(week_search.split(" ")),result['name'],re.IGNORECASE) is not None:
                    self.logger.info("Adding %s"%(result['name']))
                    torrents_to_download.append(result['magnet_url'])
                    found = True
                    self.update_week()
                    break #found the week we were looking for
            if not found: break
        return torrents_to_download

if __name__ == '__main__':
    #setup logging
    #logging.basicConfig(format="[%(asctime)s] ComicDownloader(%(levelname)s): %(message)s")
    rotator_handler = handlers.RotatingFileHandler("/tmp/comic_donwloader.log",mode="a",maxBytes=1024*1024)
    logging.root.addHandler(rotator_handler)
    rotator_handler.setLevel(logging.DEBUG)
    logging.root.setLevel(logging.DEBUG)
    fm = logging.Formatter("[%(asctime)s] ComicDownloader(%(levelname)s): %(message)s")
    rotator_handler.setFormatter(fm)
    #_syslog.setFormatter(fm)
    while (1):
        try:
            logging.info("Starting setup controller")
            controller = SetupController()
            controller.main()
        except Exception, e:
            type, value, tb = sys.exc_info()
            #traceback.print_exc()
            logging.exception("Exception encountered in the main control loop")
            sleep(HOUR)
