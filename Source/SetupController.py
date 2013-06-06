#!/usr/bin/env python
from TorrentCommander import TorrentCommander
from pytpb import ThePirateBay
from time import sleep
import re
import os
import json
import pdb, traceback, sys
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
            self.torrent_commander.add_torrents(new_torrents)
            self.logger.info("Finished Adding Torrents")
            sleep(0.5*DAY)
    
    def clean_up_directory(self):
        pass
    
    def find_torrents(self,max_torrents=10):
        torrents_to_download = list()
        search_results = self.pirate_bay.search(self.config['search_term'])
        while len(torrents_to_download)<max_torrents: #search loop for this week and on
            # The line termination might be a problem in the future...
            week_search = self.config['search_term'] + " " + str(self.next_week)# + "$"
            logging.debug(week_search)
            found = False
            for result in search_results:
                if re.match(week_search,result['name'],re.IGNORECASE) is not None:
                    torrents_to_download.append(result['magnet_url'])
                    found = True
                    self.next_week+=1
            if not found: break
        #saving the next week search term
        f = open(self.week_file,"w")
        f.write(str(self.next_week))
        f.close()
        return torrents_to_download

if __name__ == '__main__':
    #setup logging
    logging.basicConfig(format="[%(asctime)s] ComicDownloader(%(levelname)s): %(message)s")
    logging.root.setLevel(logging.INFO)
    #fm = logging.Formatter("%(module)s@%(funcName)s:%(lineno)d - %(message)s")
    #_syslog.setFormatter(fm)
    logging.info("Starting setup controller")
    controller = SetupController()
    try:
        controller.main()
    except Exception, e:
        type, value, tb = sys.exc_info()
        #traceback.print_exc()
        logging.exception("Exception encountered in the main control loop")
        pdb.post_mortem(tb)
