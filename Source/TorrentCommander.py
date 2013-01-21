'''
Torrent Commander class
@author: omriz
'''

import transmissionrpc
import json
import re
from time import sleep
from exceptions import Exception

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
        conf = json.load(open(config_file))
        self.transmission = transmissionrpc.Client(
                                address=conf['server'],
                                port = int(conf['port']),
                                user = conf['user'],
                                password = conf['password'],
                                )
        self.download_dir = conf['download_dir']
        self.running_torrent_ids = list()

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
            if torrent.startswith("magnet"): # Handling magnet links
                running_torrent=self.transmission.add_torrent(None,filename=torrent,download_dir = self.download_dir)
            else:
                running_torrent=self.transmission.add_torrent(torrent,download_dir = self.download_dir)
            self.filter_torrent(running_torrent,file_filter)

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
            self.running_torrent_ids.append(torrent['id'])
        except NoFilesException:
            self.transmission.remove(torrent['id'], delete_data=True)

    def wait_for_files(self,torrent,timeout=5*60):
        """
        Activates a torrent if needed.
        Waits till it reports back its list of files.
        """
        iterations = timeout/5
        if torrent.status == "stopped":
            self.transmission.start(torrent.fields['id'])
        while iterations:
            files_dict = self.transmission.get_files(torrent.fields['id'])[torrent.fields['id']]
            if files_dict: return files_dict
            sleep(5)
            iterations-=1
        raise NoFilesException
    
    def cleanup_completed_torrents(self):
        for id in self.running_torrent_ids:
            if self.transmission.get_torrent(id).status in ("seeding","stopped"):
                self.transmission.remove(id, delete_data=False)

class NoFilesException(Exception):
    def __str__(self):
        return "No files found"

if __name__ == '__main__':
    print "Beginning TorrentCommander unit test"
    my_json = "/".join(__file__.split("/")[:-2]+["example.json"])
    commander = TorrentCommander(my_json)
    print "Unit test completed"
