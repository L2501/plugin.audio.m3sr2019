import os
import isodate
import requests
from bs4 import BeautifulSoup
from datetime import timedelta, datetime
from urlparse import urljoin
from peewee import *

try:
    from http.cookiejar import LWPCookieJar
except ImportError:
    from cookielib import LWPCookieJar
try:
    from urllib.parse import quote_from_bytes as orig_quote
except ImportError:
    from urllib import quote as orig_quote


def quote(s, safe=""):
    return orig_quote(s.encode("utf-8"), safe.encode("utf-8"))


db = SqliteDatabase(None)


class BaseModel(Model):
    class Meta:
        database = db


class Track(BaseModel):
    rel = CharField(unique=True)
    track_id = TextField()
    image = TextField()
    duration = TextField()
    album = TextField()
    artist = TextField()
    title = TextField()


class musicMp3:
    def __init__(self, cache_dir):
        if not os.path.exists(cache_dir):
            cache_dir = os.getcwd()
        TRACKS_DB = os.path.join(cache_dir, "tracks.db")
        COOKIE_FILE = os.path.join(cache_dir, "lwp_cookies.dat")
        db.init(TRACKS_DB)
        db.connect()
        db.create_tables([Track], safe=True)
        self.base_url = "https://musicmp3.ru/"
        self.user_agent = "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:66.0) Gecko/20100101 Firefox/66.0"
        self.s = requests.Session()
        self.s.cookies = LWPCookieJar(filename=COOKIE_FILE)
        self.s.headers.update({"User-Agent": self.user_agent})
        if os.path.isfile(COOKIE_FILE):
            self.s.cookies.load(ignore_discard=True, ignore_expires=True)

    def __del__(self):
        db.close()
        self.s.cookies.save(ignore_discard=True, ignore_expires=True)
        self.s.close()

    def image_url(self, url):
        return "{0}|User-Agent={1}&Referer={2}".format(url, quote(self.user_agent), quote(self.base_url))

    def boo(self, track_id):
        def int32(x):
            if x > 0xFFFFFFFF:
                raise OverflowError
            if x > 0x7FFFFFFF:
                x = int(0x100000000 - x)
                if x < 2147483648:
                    return -x
                else:
                    return -2147483648
            return x

        _in = track_id[5:] + requests.utils.dict_from_cookiejar(self.s.cookies)["SessionId"][8:]
        a = 1234554321
        c = 7
        b = 305419896
        for f in _in:
            f = ord(f) & 255
            a = int(int32((a ^ ((a & 63) + c) * f + a << 8) & 0xFFFFFFFF))
            b = int(b + (int32(b << 8 & 0xFFFFFFFF) ^ a))
            c = c + f
        a = int(a & 0x7FFFFFFF)
        b = int(b & 0x7FFFFFFF)
        d = hex(a)[2:]
        c = hex(b)[2:]
        return ("0000" + hex(a)[2:])[len(d) - 4 :] + ("0000" + hex(b)[2:])[len(c) - 4 :]

    def play_url(self, track_id, rel):
        return "https://listen.musicmp3.ru/{0}/{1}|seekable=0&User-Agent={2}&Referer={3}".format(
            self.boo(track_id), rel, quote(self.user_agent), quote(self.base_url)
        )

    def artists(self, s):
        for a in s.find_all("a"):
            yield {"artist": a.get_text(strip=True), "link": urljoin(self.base_url, a.get("href"))}

    def albums(self, s):
        for li in s.find_all("li", class_="unstyled"):
            yield {
                "title": li.find(class_="album_report__name").get_text(strip=True),
                "image": li.find(class_="album_report__image").get("src"),
                "link": urljoin(self.base_url, li.find(class_="album_report__link").get("href")),
                "artist_link": urljoin(self.base_url, li.find(class_="album_report__artist").get("href")),
                "artist": li.find(class_="album_report__artist").get_text(strip=True),
                "date": li.find(class_="album_report__date").get_text(strip=True),
            }

    def search(self, text, cat):
        params = {"text": text, "all": cat}
        r = self.s.get("https://musicmp3.ru/search.html", params=params, headers={"Referer": self.base_url}, timeout=5)
        soup = BeautifulSoup(r.text, "html.parser")
        _list = []
        if cat == "artists":
            for artist in soup.find_all(class_="artist_preview"):
                _list.append(
                    {"artist": artist.a.get_text(strip=True), "link": urljoin(self.base_url, artist.a.get("href"))}
                )
        elif cat == "albums":
            for album in soup.find_all(class_="album_report"):
                album_report = {
                    "title": album.find(class_="album_report__name").get_text(strip=True),
                    "image": album.find(class_="album_report__image").get("src"),
                    "link": urljoin(self.base_url, album.find(class_="album_report__link").get("href")),
                    "artist_link": urljoin(self.base_url, album.find(class_="album_report__artist").get("href")),
                    "artist": album.find(class_="album_report__artist").get_text(strip=True),
                    "date": album.find(class_="album_report__date").get_text(strip=True),
                }
                if album.find(class_="album_report__details_content"):
                    album_report["details"] = album.find(class_="album_report__details_content").get_text(strip=True)
                _list.append(album_report)
        return _list

    def main_artists(self, start, count):
        _page = 1 + start // 80
        _list = []
        while len(_list) < count:
            params = {"type": "artist", "page": _page}
            r = self.s.get(
                "https://musicmp3.ru/main_artists.html", params=params, headers={"Referer": self.base_url}, timeout=5
            )
            soup = BeautifulSoup(r.text, "html.parser")
            if not soup.a:
                break
            for index, item in enumerate(self.artists(soup), (_page - 1) * 80):
                if len(_list) >= count:
                    break
                else:
                    if index >= start:
                        _list.append(item)
            _page += 1
        return _list

    def main_albums(self, section, gnr_id, sort, start, count):
        _page = 1 + start // 40
        _list = []
        while len(_list) < count:
            params = {"sort": sort, "type": "album", "page": _page}
            if not gnr_id == "0":
                params["gnr_id"] = gnr_id
            if section:
                params["section"] = section
            r = self.s.get("https://musicmp3.ru/main_albums.html", params=params, timeout=5)
            soup = BeautifulSoup(r.text, "html.parser")
            if not soup.li:
                break
            for index, item in enumerate(self.albums(soup), (_page - 1) * 80):
                if len(_list) >= count:
                    break
                else:
                    if index >= start:
                        _list.append(item)
            _page += 1
        return _list

    def artist_albums(self, url):
        r = self.s.get(url, headers={"Referer": self.base_url}, timeout=5)
        soup = BeautifulSoup(r.text, "html.parser")
        _artist = soup.find(class_="page_title__h1").get_text(strip=True)
        _list = []
        for album in soup.find_all(class_="album_report"):
            album_report = {
                "title": album.find(class_="album_report__name").get_text(strip=True),
                "image": album.find(class_="album_report__image").get("src"),
                "link": urljoin(self.base_url, album.find(class_="album_report__link").get("href")),
                "artist_link": url,
                "artist": _artist,
                "date": album.find(class_="album_report__date").get_text(strip=True),
            }
            if album.find(class_="album_report__details_content"):
                album_report["details"] = album.find(class_="album_report__details_content").get_text(strip=True)

            _list.append(album_report)
        return _list

    def album_tracks(self, url):
        r = self.s.get(url)
        soup = BeautifulSoup(r.text, "html.parser")
        image = soup.find(class_="art_wrap__img").get("src")
        tracks = []
        for song in soup.find_all(class_="song"):
            track = {}
            track["title"] = song.find(itemprop="name").get_text(strip=True)
            track["artist"] = song.find(itemprop="byArtist").get("content")
            track["album"] = song.find(itemprop="inAlbum").get("content")
            track["duration"] = str(
                isodate.parse_duration(song.find(itemprop="duration").get("content")).total_seconds()
            )
            track["image"] = self.image_url(image)
            track["track_id"] = song.get("id")
            track["rel"] = song.a.get("rel")[0]
            tracks.append(track)

        with db.atomic():
            Track.replace_many(tracks).execute()
        return tracks

    def get_track(self, rel):
        try:
            return Track.get(Track.rel == rel)
        except:
            return Track()


gnr_ids = [
    (
        "World",
        [
            ("World", "0"),
            ("Celtic", "3"),
            ("Jewish", "14"),
            ("Polynesian", "20"),
            ("African", "23"),
            ("Arabic", "79"),
            ("Brazilian", "93"),
            ("Caribbean", "135"),
            ("Turkish", "164"),
            ("Chinese", "169"),
            ("Japanese", "179"),
            ("Korean", "194"),
            ("South Asian", "200"),
            ("Spanish Folk", "212"),
            ("South American Folk", "220"),
            ("Slavic Folk", "229"),
            ("Nordic Folk", "241"),
            ("Italian Folk", "249"),
            ("French Folk", "252"),
            ("Balkan Folk", "259"),
            ("Latin", "268"),
            ("Compilations", "2"),
        ],
    ),
    (
        "Classical",
        [
            ("Classical", "313"),
            ("Baroque Period", "314"),
            ("Chamber", "315"),
            ("Choral", "316"),
            ("Classical Period", "317"),
            ("Medieval", "318"),
            ("Modern Classical", "326"),
            ("Opera", "343"),
            ("Orchestral", "348"),
            ("Renaissance", "352"),
            ("Romantic Period", "353"),
            ("Classical Crossover", "354"),
            ("Compilations", "313"),
        ],
    ),
    (
        "Metal",
        [
            ("Metal", "355"),
            ("Alternative Metal", "356"),
            ("Black Metal", "360"),
            ("Death Metal", "365"),
            ("Doom Metal", "373"),
            ("Folk Metal", "378"),
            ("Gothic Metal", "382"),
            ("Grindcore", "383"),
            ("Groove Metal", "386"),
            ("Heavy Metal", "387"),
            ("Industrial Metal", "389"),
            ("Metalcore", "391"),
            ("Neo-Classical Metal", "395"),
            ("Power Metal", "396"),
            ("Progressive Metal", "397"),
            ("Symphonic Metal", "398"),
            ("Thrash & Speed Metal", "399"),
            ("Sludge Metal", "404"),
            ("Glam Metal", "407"),
            ("Compilations", "355"),
        ],
    ),
    (
        "Alternative",
        [
            ("Alternative", "408"),
            ("Britpop", "409"),
            ("Dream Pop", "410"),
            ("Grunge", "412"),
            ("Indie Rock", "414"),
            ("Industrial Rock", "419"),
            ("Rap Rock", "420"),
            ("Garage Rock", "421"),
            ("Latin Alternative", "286"),
            ("Post-Punk", "424"),
            ("Emo", "431"),
            ("Punk Rock", "436"),
            ("Compilations", "408"),
        ],
    ),
    (
        "Rock",
        [
            ("Rock", "473"),
            ("Art Rock", "474"),
            ("Christian Rock", "481"),
            ("Comedy Rock", "482"),
            ("Folk Rock", "483"),
            ("Glam Rock", "489"),
            ("Hard Rock", "491"),
            ("Latin Rock", "292"),
            ("Progressive Rock", "494"),
            ("Psychedelic Rock", "500"),
            ("Rock & Roll", "507"),
            ("Southern Rock", "515"),
            ("Rockabilly", "516"),
            ("Compilations", "473"),
        ],
    ),
    (
        "R&B",
        [
            ("R&B", "517"),
            ("Contemporary R&B", "518"),
            ("Funk", "520"),
            ("Soul", "525"),
            ("Early R&B", "534"),
            ("Pop Soul", "537"),
            ("Neo-Soul", "538"),
            ("Compilations", "517"),
        ],
    ),
    (
        "Dance",
        [
            ("Dance", "539"),
            ("Teen Pop", "540"),
            ("Hi-NRG", "542"),
            ("Dance Pop", "543"),
            ("Electropop", "547"),
            ("Alternative Dance", "549"),
            ("Disco", "551"),
            ("Eurodance", "557"),
            ("Compilations", "539"),
        ],
    ),
    (
        "Pop",
        [
            ("Pop", "558"),
            ("Adult Contemporary", "559"),
            ("CCM", "560"),
            ("Euro Pop", "562"),
            ("French Pop", "564"),
            ("Indie Pop", "567"),
            ("Latin Pop", "291"),
            ("Pop Rock", "571"),
            ("Traditional Pop", "579"),
            ("New Wave", "582"),
            ("Easy Listening", "589"),
            ("Blue Eyed Soul", "595"),
            ("Compilations", "558"),
        ],
    ),
    (
        "Jazz",
        [
            ("Jazz", "596"),
            ("Acid Jazz", "597"),
            ("Free Jazz", "599"),
            ("Bebop", "600"),
            ("Big Band", "603"),
            ("Cool Jazz", "606"),
            ("Jazz Fusion", "607"),
            ("Soul Jazz", "610"),
            ("Swing", "611"),
            ("Vocal Jazz", "613"),
            ("Early Jazz", "614"),
            ("World Jazz", "622"),
            ("Compilations", "596"),
        ],
    ),
    (
        "Hip Hop",
        [
            ("Hip Hop", "623"),
            ("Alternative Hip Hop", "624"),
            ("Comedy Rap", "629"),
            ("East Coast Hip Hop", "630"),
            ("French Hip Hop", "631"),
            ("Hardcore Hip Hop", "632"),
            ("Instrumental Hip Hop", "637"),
            ("Political Hip Hop", "638"),
            ("Pop Rap", "639"),
            ("Religious Hip Hop", "640"),
            ("Southern Hip Hop", "644"),
            ("UK Hip Hop", "652"),
            ("West Coast Hip Hop", "653"),
            ("Compilations", "623"),
        ],
    ),
    (
        "Electronic",
        [
            ("Electronic", "654"),
            ("Breakbeat", "655"),
            ("Downtempo", "661"),
            ("Drum and Bass", "664"),
            ("EBM", "678"),
            ("Electro", "681"),
            ("Hardcore Techno", "686"),
            ("House", "698"),
            ("IDM", "717"),
            ("Indie Electronic", "718"),
            ("Techno", "720"),
            ("Trance", "728"),
            ("UK Garage", "737"),
            ("Ambient", "744"),
            ("Dubstep", "749"),
            ("Compilations", "654"),
        ],
    ),
    (
        "Country",
        [
            ("Country", "750"),
            ("Alternative Country", "751"),
            ("Contemporary Country", "755"),
            ("Country Pop", "756"),
            ("Traditional Country", "759"),
            ("Country Rock", "770"),
            ("Compilations", "750"),
        ],
    ),
    (
        "Blues",
        [
            ("Blues", "774"),
            ("Acoustic Blues", "775"),
            ("Electric Blues", "780"),
            ("Piano Blues", "784"),
            ("Blues Rock", "786"),
            ("Compilations", "774"),
        ],
    ),
    (
        "Soundtracks",
        [
            ("Soundtracks", "0"),
            ("Movie Soundtracks", "789"),
            ("TV Soundtracks", "792"),
            ("Game Soundtracks", "794"),
            ("Show Tunes", "796"),
            ("Spoken Word", "797"),
        ],
    ),
]
