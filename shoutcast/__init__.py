
import httplib
import logging
logger = logging.getLogger(__name__)
import os
import re
import socket
import urllib
from urllib2 import urlparse
import sys


try:
    import StringIO
except ImportError:
    import cStringIO as StringIO

STATION = None

def enable(exaile):
    if exaile.loading:
        event.add_callback(_enable, "exaile_loaded")
    else:
        _enable(None, exaile, None)

def _enable(devicename, exaile, nothing):
    global STATION

    STATION = ShoutcastRadioStation()
    exaile.radio.add_station(STATION)

def disable(exaile):
    global STATION
    exaile.radio.remove_station(STATION)
    STATION = None

def set_status(message, timeout=0):
    #from xlgui.panel import radio
    #radio.set_status(message, timeout)
    #print message
    pass

class ShoutcastRadioStation():
    """
        Shoutcast Radio

        Simple usage:

        >>> manager = RadioManager()
        >>> manager.add_station(ShoutcastRadioStation())
        >>> stations = manager.search('shoutcast', 'ravetrax')
        >>> tracks = stations[0].get_playlist().get_tracks()
        >>> len(tracks) > 0
        True
        >>>
    """
    name = 'shoutcast'
    def __init__(self):
        """
            Initializes the shoutcast radio station
        """
        self.user_agent = 'Firefox'
        self.genre_url = 'http://www.shoutcast.com/sbin/newxml.phtml'
        self.cat_url = 'http://www.shoutcast.com/sbin/newxml.phtml?genre=%(genre)s'
        self.playlist_url = 'http://www.shoutcast.com/sbin/tunein-station.pls?id=%(id)s'
        self.search_url = 'http://www.shoutcast.com/sbin/newxml.phtml?search=%(kw)s'
        self.cache_file = os.path.join('/tmp', 'shoutcast.cache')
        self.data = None
        self._load_cache()
        self.subs = {}
        self.playlists = {}

        logger.debug(self.user_agent)

    def _load_cache(self):
        """
            Loads shoutcast data from cache
        """
        if os.path.isfile(self.cache_file):
            self.data = open(self.cache_file).read()
            items = re.findall(r'<genre name="([^"]*)"></genre>', self.data)

            # if there are no cached items, the cache isn't valid anyway, so
            # don't use it
            if not items:
                self.data = None

    def _save_cache(self):
        """
            Saves cache data
        """
        h = open(self.cache_file, 'w')
        h.write(self.data)
        h.close()

    def get_lists(self, no_cache=False):
        """
            Returns the rlists for shoutcast
        """
        if no_cache or not self.data:
            set_status('Contacting Shoutcast server...')
            hostinfo = urlparse.urlparse(self.genre_url)
            try:
                c = httplib.HTTPConnection(hostinfo.netloc,
                        timeout=40)
            except TypeError: # python 2.5 doesnt have timeout=
                c = httplib.HTTPConnection(hostinfo.netloc)
            try:
                c.request('GET', hostinfo.path, headers={'User-Agent':
                    self.user_agent})
                response = c.getresponse()
            except (socket.timeout, socket.error):
                raise radio.RadioException(
                    'Error connecting to Shoutcast server.')

            if response.status != 200:
                raise radio.RadioException(
                    'Error connecting to Shoutcast server.')

            data = response.read()
            set_status('')

            self.data = data
            self._save_cache()
        else:
            data = self.data
        items = re.findall(r'<genre name="([^"]*)"></genre>', data)
        rlists = []

        repl = {'&amp;' : '&',
                '&lt;' : '<',
                '&gt;' : '>'}

        for item in items:
            for k, v in repl.items():
                item = item.replace(k, v)
            rlists.append(item)

        return rlists

    def _get_subrlists(self, name, no_cache=False, onlyurls = False):
        """
            Gets the subrlists for a rlist
        """
        if name in self.subs and not no_cache:
            return self.subs[name]

        name = urllib.quote(name)

        url = self.cat_url % {'genre': name}

        set_status('Contacting Shoutcast server...')
        hostinfo = urlparse.urlparse(url)
        try:
            c = httplib.HTTPConnection(hostinfo.netloc,
                    timeout=40)
        except TypeError: # python 2.5 doesnt have timeout=
            c = httplib.HTTPConnection(hostinfo.netloc)
        try:
            c.request('GET', "%s?%s" % (hostinfo.path, hostinfo.query),
                headers={'User-Agent': self.user_agent})
            response = c.getresponse()
        except (socket.timeout, socket.error):
            raise radio.RadioException(
                'Error connecting to Shoutcast server.')

        if response.status != 200:
            raise radio.RadioException(
                'Error connecting to Shoutcast server.')

        data = response.read()
        set_status('')

        rlists = []
        items = re.findall(r'<station name="([^"]*)" .*? id="(\d+)" br="(\d+)"', data)
        found_names = []

        for item in items:
            rlists.append(self._get_playlist(item[0], item[1], onlyurls))

        return rlists

    def _get_playlist(self, name, station_id, onlyurls = False):
        """
            Gets the playlist for the given name and id
        """
        set_status('Contacting Shoutcast server...')
        if station_id in self.playlists:
            return self.playlists[station_id]
        url = self.playlist_url % {'id': station_id}

        if onlyurls:
            return url
        else:
            return '%s\n%s' % (name, url)


        hostinfo = urlparse.urlparse(url)
        try:
            c = httplib.HTTPConnection(hostinfo.netloc,
                    timeout=20)
        except TypeError: # python 2.5 doesnt have timeout=
            c = httplib.HTTPConnection(hostinfo.netloc)
        try:
            c.request('GET', "%s?%s" % (hostinfo.path, hostinfo.query),
                headers={'User-Agent': self.user_agent})
            response = c.getresponse()
        except (socket.timeout, socket.error):
            set_status(
                'Error connecting to Shoutcast server.')
            return None

        if response.status != 200:
            set_status(
                'Error connecting to Shoutcast server.')
            return None

        data = response.read()
        set_status('')


        #self.playlists[station_id] = playlist.import_from_pls(name + ".pls",
            #handle)
        return data

    def search(self, keyword, onlyurls = False):
        """
            Searches the station for a specified keyword

            @param keyword: the keyword to search
        """
        #from xlgui.panel import radio
        set_status('Contacting Shoutcast server...')
        keyword = urllib.quote(keyword)
        url = self.search_url % {'kw': keyword}

        hostinfo = urlparse.urlparse(url)
        try:
            c = httplib.HTTPConnection(hostinfo.netloc,
                    timeout=30)
        except TypeError: # python 2.5 doesnt have timeout=
            c = httplib.HTTPConnection(hostinfo.netloc)
        try:
            c.request('GET', "%s?%s" % (hostinfo.path, hostinfo.query),
                headers={'User-Agent': self.user_agent})
            response = c.getresponse()
        except (socket.timeout, socket.error):
            set_status(
                'Error connecting to Shoutcast server.')
            return


        if response.status != 200:
            set_status('Error connecting to Shoutcast server.')
            return

        data = response.read()
        set_status('')
        rlists = []
        items = re.findall(r'<station name="([^"]*)" .*? id="(\d+)"', data)

        for item in items:
            rlists.append(self._get_playlist(item[0], item[1], onlyurls))

        return rlists

    def on_search(self):
        """
            Called when the user wants to search for a specific stream
        """
        dialog = dialogs.TextEntryDialog(_("Enter the search keywords"),
            _("Shoutcast Search"))

        result = dialog.run()
        if result == gtk.RESPONSE_OK:
            keyword = dialog.get_value()

            self.do_search(keyword)

    def do_search(self, keyword):
        """
            Actually performs the search in a separate thread
        """
        lists = self.search(keyword)

        glib.idle_add(self.search_done, keyword, lists)

    def search_done(self, keyword, lists):
        """
            Called when the search is finished
        """
        if not lists: return
        dialog = dialogs.ListDialog(_("Search Results"))
        dialog.set_items(lists)
        dialog.connect('response', self._search_response)
        dialog.show_all()
        self._keyword = keyword

    def _search_response(self, dialog, result, *e):

        dialog.hide()
        if result == gtk.RESPONSE_OK:
            items = dialog.get_items()
            if not items: return

            self.do_get_playlist(self._keyword, items[0])

    def do_get_playlist(self, keyword, item):
        pl = item.get_playlist()
        if not pl: return
        pl.name = keyword

        glib.idle_add(self.done_getting_playlist, pl)

    def done_getting_playlist(self, pl):
        self._parent.emit('playlist-selected', pl)

    def get_menu(self, parent):
        """
            Returns a menu that works for shoutcast radio
        """
        self._parent = parent
        menu = parent.get_menu()
        menu.append(_("Search"), lambda *e: self.on_search(), gtk.STOCK_FIND)
        return menu

if __name__ == "__main__":
    s = ShoutcastRadioStation()
    lists = s.search('New Age', onlyurls = True)
    for l in lists:
        sys.stdout.write('%s\n' % l)

    lists = s.get_lists()
    for l in lists:
        sys.stdout.write('%s\n' % (l))

    rl = s._get_subrlists('Ambient', onlyurls = True)
    for r in rl:
        sys.stdout.write('%s\n' % r)

