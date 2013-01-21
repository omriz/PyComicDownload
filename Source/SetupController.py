
import TorrentCommander
from pytpb import ThePirateBay
from time import sleep
import re

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
        self.torrent_commander = TorrentCommander("~/.comic_setup.json")
        self.pirate_bay = ThePirateBay()
        f = open("~/.next_week","r")
        self.next_week = int(f.readline().split("\n")[0])
        f.close()
        self.config = json.load(open(config_file))
    
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
            new_torrents = self.find_torrents()
            self.torrent_commander.add_torrents(new_torrents)
            sleep(DAY)
    
    def clean_up_directory(self):
        pass
    
    def find_torrents(self,max_torrents=10):
        torrents_to_download = list()
        search_results = self.pirate_bay.search(search_term)
        while length(torrents_to_download)<max_torrents: #search loop for this week and on
            # The line termination might be a problem in the future...
            week_search = self.config['search_term'] + " " + str(self.next_week) + "$"
            found = False
            for result in search_results:
                if re.match(week_search,result['name']) is not None:
                    torrents_to_downlad.append(result['magnet_url'])
                    found = True
                    self.next_week+=1
            if not found: break
        #saving the next week search term
        f = open("~/.next_week","w")
        f.write(str(self.next_week))
        f.close()