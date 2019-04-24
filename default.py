import os
import routing
import xbmcaddon
import xbmc
from xbmc import executebuiltin
from xbmcgui import ListItem
from xbmcplugin import addDirectoryItem, endOfDirectory, setResolvedUrl, setContent
from resources.lib.musicmp3 import musicMp3
from resources.lib import isodate

try:
    from urllib.parse import quote as orig_quote
    from urllib.parse import unquote as orig_unquote
except ImportError:
    from urllib import quote as orig_quote
    from urllib import unquote as orig_unquote


def quote(s, safe=""):
    return orig_quote(s.encode("utf-8"), safe.encode("utf-8"))


def unquote(s):
    return orig_unquote(s).decode("utf-8")


addon = xbmcaddon.Addon()
plugin = routing.Plugin()
plugin.name = addon.getAddonInfo("name")

USER_DATA_DIR = xbmc.translatePath(addon.getAddonInfo("profile")).decode("utf-8")  # !!
MEDIA_DIR = os.path.join(xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('path')).decode("utf-8"), 'resources', 'media')
FANART = os.path.join(MEDIA_DIR, "fanart.jpg")
MUSICMP3_DIR = os.path.join(USER_DATA_DIR, "musicmp3")
if not os.path.exists(MUSICMP3_DIR):
    os.makedirs(MUSICMP3_DIR)

fixed_view_mode = addon.getSetting("fixed_view_mode") == "true"
albums_view_mode = addon.getSetting("albums_view_mode")
songs_view_mode = addon.getSetting("songs_view_mode")

musicmp3_api = musicMp3(MUSICMP3_DIR)


@plugin.route("/")
def index():
    _all_artists = ListItem("All Artists")
    _all_artists.setArt({"fanart": FANART, "icon": os.path.join(MEDIA_DIR, "allartists.jpg")})
    addDirectoryItem(plugin.handle, plugin.url_for(musicmp3_main_artists, "0"), _all_artists, True)
    _top_albums = ListItem("Top Albums")
    _top_albums.setArt({"fanart": FANART, "icon": os.path.join(MEDIA_DIR, "topalbums.jpg")})
    addDirectoryItem(plugin.handle, plugin.url_for(musicmp3_albums_main, "top"), _top_albums, True)
    _new_albums = ListItem("New Albums")
    _new_albums.setArt({"fanart": FANART, "icon": os.path.join(MEDIA_DIR, "newalbums.jpg")})
    addDirectoryItem(plugin.handle, plugin.url_for(musicmp3_albums_main, "new"), _new_albums, True)
    _search_artists = ListItem("Search Artists")
    _search_artists.setArt({"fanart": FANART, "icon": os.path.join(MEDIA_DIR, "searchartists.jpg")})
    addDirectoryItem(plugin.handle, plugin.url_for(musicmp3_search, "artists"), _search_artists, True)
    _search_albums = ListItem("Search Albums")
    _search_albums.setArt({"fanart": FANART, "icon": os.path.join(MEDIA_DIR, "searchalbums.jpg")})
    addDirectoryItem(plugin.handle, plugin.url_for(musicmp3_search, "albums"), _search_albums, True)
    endOfDirectory(plugin.handle)


@plugin.route("/musicmp3/albums_main/<sort>")
def musicmp3_albums_main(sort):
    for i, gnr in enumerate(musicmp3_api.gnr_ids):
        li = ListItem("{0} {1} Albums".format(sort.title(), gnr[0]))
        li.setArt({"fanart": FANART, "icon": os.path.join(MEDIA_DIR, "genre", '{0}.jpg'.format(gnr[0].lower().replace(' ','').replace('&','_')))})
        addDirectoryItem(plugin.handle, plugin.url_for(musicmp3_albums_gnr, sort, i), li, True)
    endOfDirectory(plugin.handle)


@plugin.route("/musicmp3/albums_gnr/<sort>/<gnr>")
def musicmp3_albums_gnr(sort, gnr):
    for sub_gnr in musicmp3_api.gnr_ids[int(gnr)][1]:
        if sub_gnr[0] == "Compilations":
            section = "compilations"
        elif sub_gnr[0] == "Soundtracks":
            section = "soundtracks"
        else:
            section = "main"

        li = ListItem("{0} {1} Albums".format(sort.title(), sub_gnr[0]))
        li.setArt({"fanart": FANART, "icon": os.path.join(MEDIA_DIR, "genre", musicmp3_api.gnr_ids[int(gnr)][0].lower(),'{0}.jpg'.format(sub_gnr[0].lower().replace(' ','').replace('&','_')))})
        addDirectoryItem(
            plugin.handle,
            plugin.url_for(musicmp3_main_albums, section, sub_gnr[1], sort, "0"),
            li,
            True,
        )
    endOfDirectory(plugin.handle)


@plugin.route("/musicmp3/search/<cat>")
def musicmp3_search(cat):
    keyboard = xbmc.Keyboard("", "Search")
    keyboard.doModal()
    if keyboard.isConfirmed():
        keyboardinput = keyboard.getText()
    if keyboardinput:
        if cat == "artists":
            artists = musicmp3_api.search(keyboardinput, cat)
            for a in artists:
                li = ListItem(a.get("artist"))
                li.setInfo("music", {"title": a.get("artist"), "artist": a.get("artist")})
                addDirectoryItem(plugin.handle, plugin.url_for(artists_albums, quote(a.get("link"))), li, True)
        elif cat == "albums":
            albums = musicmp3_api.search(keyboardinput, cat)
            for a in albums:
                li = ListItem("{0}[CR][COLOR=darkmagenta]{1}[/COLOR]".format(a.get("name"), a.get("artist")))
                li.setArt({"thumb": a.get("image"), "icon": a.get("image")})
                li.setInfo("music", {"title": a.get("name"), "artist": a.get("artist"), "album": a.get("name"), "year": a.get("date")})
                li.setProperty("Album_Description", a.get("details"))
                addDirectoryItem(plugin.handle, plugin.url_for(musicmp3_album, quote(a.get("link"))), li, True)
    setContent(plugin.handle, "albums")
    if fixed_view_mode:
        executebuiltin("Container.SetViewMode({0})".format(albums_view_mode))
    endOfDirectory(plugin.handle)


@plugin.route("/musicmp3/main_albums/<section>/<gnr_id>/<sort>/<index>/")
def musicmp3_main_albums(section, gnr_id, sort, index):
    dir_items = 40
    index = int(index)
    if section == "main":
        _section = ""
    else:
        _section = section
    albums = musicmp3_api.main_albums(_section, gnr_id, sort, index, dir_items)

    context_menu = []
    next_index = str(index + dir_items)
    next_page = "ActivateWindow(Music,{0})".format(plugin.url_for(musicmp3_main_albums, section, gnr_id, sort, next_index))
    context_menu.append(("Next {0}+".format(next_index), next_page))
    previous_index = str(index - dir_items)
    if int(previous_index) >= 0:
        previous_page = "ActivateWindow(Music,{0})".format(plugin.url_for(musicmp3_main_albums, section, gnr_id, sort, previous_index))
        context_menu.append(("Previous {0}+".format(previous_index), previous_page))

    for a in albums:
        li = ListItem("{0}[CR][COLOR=darkmagenta]{1}[/COLOR]".format(a.get("name"), a.get("artist")))
        li.setArt({"thumb": a.get("image"), "icon": a.get("image")})
        li.addContextMenuItems(context_menu)
        li.setInfo("music", {"title": a.get("name"), "artist": a.get("artist"), "album": a.get("name"), "year": a.get("date")})
        addDirectoryItem(plugin.handle, plugin.url_for(musicmp3_album, quote(a.get("link"))), li, True)
    setContent(plugin.handle, "albums")
    if fixed_view_mode:
        executebuiltin("Container.SetViewMode({0})".format(albums_view_mode))
    endOfDirectory(plugin.handle)


@plugin.route("/musicmp3/main_artists/<index>")
def musicmp3_main_artists(index):
    dir_items = 40
    index = int(index)
    artists = musicmp3_api.main_artists(index, dir_items)

    context_menu = []
    next_index = str(index + dir_items)
    next_page = "ActivateWindow(Music,{0})".format(plugin.url_for(musicmp3_main_artists, next_index))
    context_menu.append(("Next {0}+".format(next_index), next_page))
    previous_index = str(index - dir_items)
    if int(previous_index) >= 0:
        previous_page = "ActivateWindow(Music,{0})".format(plugin.url_for(musicmp3_main_artists, previous_index))
        context_menu.append(("Previous {0}+".format(previous_index), previous_page))

    for a in artists:
        li = ListItem(a.get("artist"))
        li.setInfo("music", {"title": a.get("artist"), "artist": a.get("artist")})
        addDirectoryItem(plugin.handle, plugin.url_for(artists_albums, quote(a.get("link"))), li, True)
    setContent(plugin.handle, "albums")
    if fixed_view_mode:
        executebuiltin("Container.SetViewMode({0})".format(albums_view_mode))
    endOfDirectory(plugin.handle)


@plugin.route("/musicmp3/artists_albums/<link>")
def artists_albums(link):
    url = unquote(link)
    albums = musicmp3_api.artist_albums(url)
    for a in albums:
        li = ListItem("{0}[CR][COLOR=darkmagenta]{1}[/COLOR]".format(a.get("name"), a.get("artist")))
        li.setArt({"thumb": a.get("image"), "icon": a.get("image")})
        li.setInfo("music", {"title": a.get("name"), "artist": a.get("artist"), "album": a.get("name"), "year": a.get("date")})
        li.setProperty("Album_Description", a.get("details"))
        addDirectoryItem(plugin.handle, plugin.url_for(musicmp3_album, quote(a.get("link"))), li, True)
    setContent(plugin.handle, "albums")
    if fixed_view_mode:
        executebuiltin("Container.SetViewMode({0})".format(albums_view_mode))
    endOfDirectory(plugin.handle)


@plugin.route("/musicmp3/album/<link>")
def musicmp3_album(link):
    url = unquote(link)
    tracks = musicmp3_api.album_tracks(url)
    for t in tracks:
        li = ListItem(t.get("name"))
        li.setProperty("IsPlayable", "true")
        li.setArt({"thumb": t.get("image"), "icon": t.get("image")})
        li.setInfo(
            "music",
            {"title": t.get("name"), "artist": t.get("artist"), "album": t.get("album"), "duration": isodate.parse_duration(t.get("duration")).total_seconds()},
        )
        addDirectoryItem(plugin.handle, plugin.url_for(musicmp3_play, track_id=t.get("id"), rel=t.get("rel")), li, False)
    setContent(plugin.handle, "songs")
    if fixed_view_mode:
        executebuiltin("Container.SetViewMode({0})".format(songs_view_mode))
    endOfDirectory(plugin.handle)


@plugin.route("/musicmp3/play/<track_id>/<rel>")
def musicmp3_play(track_id, rel):
    li = ListItem(path=musicmp3_api.play_url(track_id, rel))
    li.setMimeType("audio/mpeg")
    li.setContentLookup(False)
    setResolvedUrl(plugin.handle, True, li)


if __name__ == "__main__":
    plugin.run()