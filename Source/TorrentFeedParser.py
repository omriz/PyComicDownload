'''
Feed Parser class
@author: omriz
'''

import re
import feedparser

class TorrentFeedParser(object):
    '''
    Feed parser is meant to get a feed url and a regular expression and manipulate them.
    It will search all the entries matching the pattern in the feed.
    '''


    def __init__(self, feed_url = None, torrent_string = None):
        '''
        The constructur can be used to parse a feed with a requested string/regular expression.
        '''
        self.torrent_expression = re.compile(torrent_string)
        self.torrents = []
        feed = feedparser.parse(feed_url)
        for entry in feed['entries']:
            if self.torrent_expression.match(entry['title']) is not None:
                self.torrents.append(entry['magneturi'])
    

if __name__ == '__main__':
    print "Beginning TorrentFeedParser unit test"
    feed = "http://rss.thepiratebay.se/602"
    #torrent_string = "DC NEW 52 WEEK \d+"
    torrent_string = "Bloodshot"
    parser = TorrentFeedParser(feed, torrent_string)
    print "Unit test completed"
