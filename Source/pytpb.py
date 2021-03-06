# encoding: utf-8

#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 2 of the License, or
#       (at your option) any later version.
#       
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#       
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#       MA 02110-1301, USA.

import datetime
from urllib import quote_plus
from urlparse import urljoin
import urllib2
import ssl
import lxml.html
import logging

class SearchResultParser(object):
    def __init__(self, html):
        self.doc = lxml.html.parse(html).getroot()
    
    def parse(self):
        row_data = []
        try:
            table = self.doc.xpath('//*[@id="searchResult"]')[0]
            rows = [row for row in table.iterchildren() if row.tag == 'tr']
            for row in rows:
                columns = row.getchildren()[1:]
                row_data.append(self.parse_row_columns(columns))
        except:
            pass
        return row_data
    
    def parse_row_columns(self, columns):
        """Parse the columns of a table row.
        
        *Returns*
            a dictionary with parsed data.
        """
        data = {}
        data["user_type"] = "standard"
        for ele in columns[0].iterchildren():
            if ele.tag == 'div' and ele.get('class') == 'detName':
                a = ele.find('a')
                data["torrent_info_url"] = urljoin(ele.base, a.get('href'))
                data["name"] = a.text_content()
            elif ele.tag == 'a':
                if ele.get('title') == "Download this torrent":
                    data["torrent_url"] = ele.get("href")
                elif ele.get('title') == "Download this torrent using magnet":
                    data["magnet_url"] = ele.get("href")
                elif ele[0].tag == 'img':
                    if ele[0].get('title') == "VIP":
                        data["user_type"] = "VIP"
                    elif ele[0].get('title') == "Trusted":
                        data["user_type"] = "trusted"
                    
            elif ele.tag == 'font':
                a = ele.find('a')
                if a is None:
                    data['user'] = "Anonymous"
                else:
                    data['user'] = urljoin(ele.base, a.get('href'))
                data["uploaded_at"], data["size_of"] = self.process_datetime_string(ele.text_content())
        data['seeders'] = int(columns[1].text_content().strip())
        data['leechers'] = int(columns[2].text_content().strip())
        return data

    def process_datetime_string(self, string):
        """Process the datetime string from a torrent upload.
    
        *Returns*
            Tuple with (datetime, (size, unit))
        """
        def process_datetime(part):
            if part.startswith("Today"):
                h, m = part.split()[1].split(':')
                return datetime.datetime.now().replace(
                    hour=int(h), minute=int(m))
            elif part.startswith("Y-day"):
                h, m = part.split()[1].split(':')
                d = datetime.datetime.now()
                return d.replace(
                    hour=int(h), minute=int(m),
                    day=d.day-1
                )
            elif part.endswith("ago"):
                amount, unit = part.split()[:2]
                d = datetime.datetime.now()
                if unit == "mins":
                    d = d.replace(minute=d.minute - int(amount))
                return d
            else:
                d = datetime.datetime.now()
                if ':' in part:
                    current_date, current_time = part.split()
                    h, m = current_time.split(':')
                    month, day = current_date.split('-')
                    d = d.replace(hour=int(h), minute=int(m), month=int(month), day=int(day))
                else:
                    current_date, year = part.split()
                    month, day = current_date.split('-')
                    d = d.replace(year=int(year), month=int(month), day=int(day))
                return d
        def process_size(part):
            units = {'MiB':1048576, 'GiB': 1073741824}
            size, unit = part.split()[1:]
            size = float(size) * units[unit]
            return int(size)
        string = string.replace(u"\xa0", " ")
        results = [x.strip() for x in string.split(',')]
        date = process_datetime(' '.join(results[0].split()[1:]))
        size = process_size(results[1])
        return (date, size)
        

class ThePirateBay(object):
    """Api for the Pirate Bay"""

    name = 'The Pirate Bay'
    
    searchUrl = 'https://thepiratebay.org/search/%s/%d/7/'
    
    def search(self, term, page_limit = 50):
        self.search_results = list() # emptying the list
        page = 0
        while page < page_limit:
            url = self.searchUrl % (quote_plus(term), page)
            try:
                req = urllib2.Request(url)
                html = urllib2.urlopen(req,timeout=5*60)
            except (urllib2.URLError,ssl.SSLError),e:
                logging.error("Search failed due to {0}".format(e))
                break
            parser = SearchResultParser(html)
            current_results = parser.parse()
            if not self.check_existance(current_results):
                self.search_results += current_results
                page += 1
            else:
                break
        return self.search_results
    
    def check_existance(self,results):
        "We will check if the first element already exist"
        if results is None or len(results)==0 or self.search_results is None or len(self.search_results)==0:
            return False
        for res in self.search_results:
            if res['name'] == results[0]['name']:
                return True
        return False

if __name__ == '__main__':
    def prettySize(size):
        suffixes = [("B",2**10), ("K",2**20), ("M",2**30), ("G",2**40), ("T",2**50)]
        for suf, lim in suffixes:
            if size > lim:
                continue
            else:
                return round(size/float(lim/2**10),2).__str__()+suf
    t = ThePirateBay()
    for t in t.search('the walking dead'):
        print t['name'] + '   ' +str(t['size_of'])+ '////' + str(prettySize(t['size_of']))
    
