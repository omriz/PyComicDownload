'''
Torrent Commander class
@author: omriz
'''

import transmissionrpc
import json

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

    def add_torrents(torrents, download_dir=None, file_filter=None):
        """
        Torrents should be a list
        If passed a string it will be downloaded
        file_filter will filter the files we want to download
        """
        if not isinstance(torrents,(tuple,list)):
            assert isinstance(torrents,basestring)
            torrents = [torrents]
        download_dir = self.download_dir if download_dir is None
        for torrent in torrents:
            running_torrent=self.transmission.add_torrent(torrent,download_dir = self.download_dir,paused=True)
            self.activate_torrent(running_torrent,file_filter)

    def activate_torrent(torrent,file_filter):
    #TODO - needs implementation
        pass

if __name__ == '__main__':
    print "Beginning TorrentCommander unit test"
    my_json = "/".join(__file__.split("/")[:-2]+["example.json"])
    commander = TorrentCommander(my_json)
    print "Unit test completed"
