'''
Torrent Commander class
@author: omriz
'''

import transmissionrpc
import json
import re
from time import sleep
from exceptions import Exception
import os
import shutil
import logging

class TorrentCommander(object):
    """
    TorrentCommander class is used to do the following:
    1) Loads a configuration file in JSON format. File should specify:
        a) Server address and port
        b) User
        c) Password
        d) Download directory
    """
    def __init__(self,config_file):
        self.conf = json.load(open(config_file))
        self.transmission = transmissionrpc.Client(
                                address=self.conf['server'],
                                port = int(self.conf['port']),
                                user = self.conf['user'],
                                password = self.conf['password'],
                                )
        self.download_dir = self.conf['download_dir']
        self.logger = logging.getLogger("TorrentCommander")
        self.logger.setLevel(logging.INFO)

    def add_torrents(self,torrents, download_dir=None, file_filter=None):
        """
        Torrents should be a list
        If passed a string it will be downloaded
        file_filter will filter the files we want to download - this will be a list of strings that should match the file names
        example:
            ['Aquaman', 'Superman', 'Justice.*league']
        """
        if not isinstance(torrents,(tuple,list)):
            assert isinstance(torrents,basestring)
            torrents = [torrents]
        if download_dir is None: download_dir = self.download_dir
        for torrent in torrents:
            self.logger.debug(str(torrent))
            if torrent.startswith("magnet"): # Handling magnet links
                running_torrent=self.transmission.add_torrent("1",filename=torrent,download_dir = self.download_dir)
            else:
                running_torrent=self.transmission.add_torrent(torrent,download_dir = self.download_dir)
            #Currently disabling the filter file, it seems the magnet links are taking time
            #I'll probably filter in post processing on completed torrents. More space used, but still functional
            #self.filter_torrent(running_torrent,file_filter)

    def filter_torrent(self,torrent,file_filter):
        """
        This function will take a torrent and select only the relevant files on it
        if there's nothing to use in it, it will remove it from the queue
        """
        try:
            files_dict = self.wait_for_files(torrent,timeout=5*60)
            files = []
            for file_key in files_dict.keys():
                for file_name in file_filter:
                    if re.match(file_name,files_dict[file_key]['name'],re.IGNORECASE) is not None:
                        files.append(file_key)
            if not files: raise NoFilesException
            self.transmission.change(torrent.fields['id'], files_wanted = files)
            self.transmission.start(torrent['id'])
        except NoFilesException:
            self.transmission.remove(torrent['id'], delete_data=True)

    def wait_for_files(self,torrent,timeout=5*60):
        """
        Activates a torrent if needed.
        Waits till it reports back its list of files.
        """
        iterations = timeout/5
        if self.transmission.get_torrent(torrent.fields['id']).status == "stopped":
            self.transmission.start(torrent.fields['id'])
        while iterations:
            files_dict = self.transmission.get_files(torrent.fields['id'])[torrent.fields['id']]
            if files_dict: return files_dict
            sleep(5)
            iterations-=1
        raise NoFilesException

    def cleanup_completed_torrents(self):
        """
        At this point we'll querry the Transmission database and get all apropriate files and filter them
        We'll also stop the torrent
        """
        torrent_ids = self.transmission.list().keys()
        torrent_ids = filter(lambda my_id: self.check_torrent_name(self.transmission.get_torrent(my_id)._fields['name'].value),torrent_ids)
        # Now we have only our interesting torrents
        for my_id in torrent_ids:
            self.logger.debug("ID : {0}".format(my_id))
            if self.transmission.get_torrent(my_id).status in ("seeding","stopped"):
                torrent_name = self.transmission.get_torrent(my_id)._fields['name'].value
                self.transmission.remove(my_id, delete_data=False)
                torrent_directory = self.conf['download_dir']
                #finding the torrent directory
                self.logger.debug("Checking {0}".format(torrent_name))
                for folder in os.listdir(torrent_directory):
                    if re.match(torrent_name,folder,re.IGNORECASE) is not None:
                        torrent_directory = torrent_directory + "/" + folder
                        self.logger.info("Found {0}".format(torrent_name))
                        break
                #going over the files in the torrent and taking only what we want
                self.organize_files(torrent_directory)

    def check_torrent_name(self,name):
        if re.match("\s*".join(self.conf['search_term'].split(" ")),name,re.IGNORECASE) is not None:
            return True
        else:
            return False

    def organize_files(self,directory):
        files = os.listdir(directory)
        self.logger.debug("Going over {0}".format(directory))
        for f in files:
            for comic in self.conf['comics']:
                if re.match(comic,f,re.IGNORECASE): # found an interesting comic
                    self.logger.info("Found {0}".format(f))
                    comic_title = "_".join(comic.split(".*"))
                    target_dir = os.path.join(self.conf['completed_dir'],comic_title)
                    if not os.path.exists(target_dir):
                        os.makedirs(target_dir)
                    if not os.path.exists(os.path.join(target_dir,f)):
                        shutil.copyfile(os.path.join(directory,f),os.path.join(target_dir,f))
                    os.remove(os.path.join(directory,f))
        #deleting what's left
        shutil.rmtree(directory)

class NoFilesException(Exception):
    def __str__(self):
        return "No files found"

if __name__ == '__main__':
    print "Beginning TorrentCommander unit test"
    my_json = "/".join(__file__.split("/")[:-2]+["example.json"])
    commander = TorrentCommander(my_json)
    print "Unit test completed"
