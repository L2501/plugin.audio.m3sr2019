# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 L2501
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
from __future__ import unicode_literals

import os
import sys
from routing import Plugin
from kodi_six import xbmc, xbmcgui, xbmcaddon, xbmcplugin
from resources.lib.musicmp3 import musicMp3, gnr_ids
from future.backports.urllib.parse import quote_from_bytes as orig_quote
from future.backports.urllib.parse import unquote_to_bytes as orig_unquote


def quote(s, safe=""):
    return orig_quote(s.encode("utf-8"), safe.encode("utf-8"))


def unquote(s):
    return orig_unquote(s).decode("utf-8")


addon = xbmcaddon.Addon()
plugin = Plugin()
plugin.name = addon.getAddonInfo("name")

USER_DATA_DIR = xbmc.translatePath(addon.getAddonInfo("profile"))
MEDIA_DIR = os.path.join(xbmc.translatePath(xbmcaddon.Addon().getAddonInfo("path")), "resources", "media")
FANART = os.path.join(MEDIA_DIR, "fanart.jpg")
MUSICMP3_DIR = os.path.join(USER_DATA_DIR, "musicmp3")
if not os.path.exists(MUSICMP3_DIR):
    os.makedirs(MUSICMP3_DIR)

fixed_view_mode = addon.getSetting("fixed_view_mode") == "true"
albums_view_mode = addon.getSetting("albums_view_mode")
songs_view_mode = addon.getSetting("songs_view_mode")


@plugin.route("/")
def index():
    _all_artists = xbmcgui.ListItem("Artists")
    _all_artists.setArt({"fanart": FANART, "icon": os.path.join(MEDIA_DIR, "artists.jpg")})
    xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for(musicmp3_artist_main), _all_artists, True)
    _top_albums = xbmcgui.ListItem("Top Albums")
    _top_albums.setArt({"fanart": FANART, "icon": os.path.join(MEDIA_DIR, "topalbums.jpg")})
    xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for(musicmp3_albums_main, "top"), _top_albums, True)
    _new_albums = xbmcgui.ListItem("New Albums")
    _new_albums.setArt({"fanart": FANART, "icon": os.path.join(MEDIA_DIR, "newalbums.jpg")})
    xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for(musicmp3_albums_main, "new"), _new_albums, True)
    _search_artists = xbmcgui.ListItem("Search Artists")
    _search_artists.setArt({"fanart": FANART, "icon": os.path.join(MEDIA_DIR, "searchartists.jpg")})
    xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for(musicmp3_search, "artists"), _search_artists, True)
    _search_albums = xbmcgui.ListItem("Search Albums")
    _search_albums.setArt({"fanart": FANART, "icon": os.path.join(MEDIA_DIR, "searchalbums.jpg")})
    xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for(musicmp3_search, "albums"), _search_albums, True)
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route("/musicmp3/albums_main/<sort>")
def musicmp3_albums_main(sort):
    _directory_items = []
    for i, gnr in enumerate(gnr_ids):
        li = xbmcgui.ListItem("{0} {1} Albums".format(sort.title(), gnr[0]))
        li.setArt(
            {
                "fanart": FANART,
                "icon": os.path.join(
                    MEDIA_DIR, "genre", "{0}.jpg".format(gnr[0].lower().replace(" ", "").replace("&", "_"))
                ),
            }
        )
        _directory_items.append((plugin.url_for(musicmp3_albums_gnr, sort, i), li, True))

    xbmcplugin.addDirectoryItems(plugin.handle, _directory_items, len(_directory_items))
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route("/musicmp3/albums_gnr/<sort>/<gnr>")
def musicmp3_albums_gnr(sort, gnr):
    _directory_items = []
    for sub_gnr in gnr_ids[int(gnr)][1]:
        if sub_gnr[0] == "Compilations":
            section = "compilations"
        elif sub_gnr[0] == "Soundtracks":
            section = "soundtracks"
        else:
            section = "main"

        li = xbmcgui.ListItem("{0} {1} Albums".format(sort.title(), sub_gnr[0]))
        li.setArt(
            {
                "fanart": FANART,
                "icon": os.path.join(
                    MEDIA_DIR,
                    "genre",
                    gnr_ids[int(gnr)][0].lower(),
                    "{0}.jpg".format(sub_gnr[0].lower().replace(" ", "").replace("&", "_")),
                ),
            }
        )
        _directory_items.append((plugin.url_for(musicmp3_main_albums, section, sub_gnr[1], sort, "0"), li, True))

    xbmcplugin.addDirectoryItems(plugin.handle, _directory_items, len(_directory_items))
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route("/musicmp3/artists_main")
def musicmp3_artist_main():
    _directory_items = []
    for i, gnr in enumerate(gnr_ids):
        li = xbmcgui.ListItem("{0} Artists".format(gnr[0]))
        li.setArt(
            {
                "fanart": FANART,
                "icon": os.path.join(
                    MEDIA_DIR, "genre", "{0}.jpg".format(gnr[0].lower().replace(" ", "").replace("&", "_"))
                ),
            }
        )
        _directory_items.append((plugin.url_for(musicmp3_artists_gnr, i), li, True))

    xbmcplugin.addDirectoryItems(plugin.handle, _directory_items, len(_directory_items))
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route("/musicmp3/artists_gnr/<gnr>")
def musicmp3_artists_gnr(gnr):
    _directory_items = []
    for sub_gnr in gnr_ids[int(gnr)][1]:
        if sub_gnr[0] == "Compilations":
            continue
        elif sub_gnr[0] == "Soundtracks":
            continue

        li = xbmcgui.ListItem("{0} Artists".format(sub_gnr[0]))
        li.setArt(
            {
                "fanart": FANART,
                "icon": os.path.join(
                    MEDIA_DIR,
                    "genre",
                    gnr_ids[int(gnr)][0].lower(),
                    "{0}.jpg".format(sub_gnr[0].lower().replace(" ", "").replace("&", "_")),
                ),
            }
        )
        _directory_items.append((plugin.url_for(musicmp3_main_artists, sub_gnr[1], "0"), li, True))

    xbmcplugin.addDirectoryItems(plugin.handle, _directory_items, len(_directory_items))
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route("/musicmp3/search/<cat>")
def musicmp3_search(cat):
    musicmp3_api = musicMp3(MUSICMP3_DIR)
    keyboard = xbmc.Keyboard("", "Search")
    keyboard.doModal()
    if keyboard.isConfirmed():
        keyboardinput = keyboard.getText()
    if keyboardinput:
        _directory_items = []
        if cat == "artists":
            artists = musicmp3_api.search(keyboardinput, cat)
            for a in artists:
                li = xbmcgui.ListItem(a.get("artist"))
                li.setInfo("music", {"title": a.get("artist"), "artist": a.get("artist")})
                _directory_items.append((plugin.url_for(artists_albums, quote(a.get("link"))), li, True))
        elif cat == "albums":
            albums = musicmp3_api.search(keyboardinput, cat)
            for a in albums:
                li = xbmcgui.ListItem("{0}[CR][COLOR=darkmagenta]{1}[/COLOR]".format(a.get("title"), a.get("artist")))
                li.setArt({"thumb": a.get("image"), "icon": a.get("image")})
                li.setInfo(
                    "music",
                    {
                        "title": a.get("title"),
                        "artist": a.get("artist"),
                        "album": a.get("title"),
                        "year": a.get("date"),
                    },
                )
                li.setProperty("Album_Description", a.get("details"))
                _directory_items.append((plugin.url_for(musicmp3_album, quote(a.get("link"))), li, True))

    xbmcplugin.addDirectoryItems(plugin.handle, _directory_items, len(_directory_items))
    xbmcplugin.setContent(plugin.handle, "albums")
    if fixed_view_mode:
        xbmc.executebuiltin("Container.SetViewMode({0})".format(albums_view_mode))
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route("/musicmp3/main_albums/<section>/<gnr_id>/<sort>/<index>/dir")
def musicmp3_main_albums(section, gnr_id, sort, index):
    musicmp3_api = musicMp3(MUSICMP3_DIR)
    dir_items = 40
    index = int(index)
    if section == "main":
        _section = ""
    else:
        _section = section
    albums = musicmp3_api.main_albums(_section, gnr_id, sort, index, dir_items)

    _directory_items = []
    for a in albums:
        li = xbmcgui.ListItem("{0}[CR][COLOR=darkmagenta]{1}[/COLOR]".format(a.get("title"), a.get("artist")))
        li.setArt({"thumb": a.get("image"), "icon": a.get("image")})
        li.setInfo(
            "music",
            {"title": a.get("title"), "artist": a.get("artist"), "album": a.get("title"), "year": a.get("date")},
        )
        _directory_items.append((plugin.url_for(musicmp3_album, quote(a.get("link"))), li, True))

    """ Next Page """
    if len(albums) >= dir_items:
        next_index = str(index + dir_items)
        li = xbmcgui.ListItem("More {0}+".format(next_index))
        l = plugin.url_for(musicmp3_main_albums, section, gnr_id, sort, next_index)
        _directory_items.append((l, li, True))

    xbmcplugin.addDirectoryItems(plugin.handle, _directory_items, len(_directory_items))
    xbmcplugin.setContent(plugin.handle, "albums")
    if fixed_view_mode:
        xbmc.executebuiltin("Container.SetViewMode({0})".format(albums_view_mode))
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route("/musicmp3/main_artists/<gnr_id>/<index>/dir")
def musicmp3_main_artists(gnr_id, index):
    musicmp3_api = musicMp3(MUSICMP3_DIR)
    dir_items = 40
    index = int(index)
    artists = musicmp3_api.main_artists(gnr_id, index, dir_items)

    _directory_items = []
    for a in artists:
        li = xbmcgui.ListItem(a.get("artist"))
        li.setInfo("music", {"title": a.get("artist"), "artist": a.get("artist")})
        li.setProperty("Album_Artist", a.get("artist"))
        _directory_items.append((plugin.url_for(artists_albums, quote(a.get("link"))), li, True))

    """ Next Page """
    if len(artists) >= dir_items:
        next_index = str(index + dir_items)
        li = xbmcgui.ListItem("More {0}+".format(next_index))
        l = plugin.url_for(musicmp3_main_artists, gnr_id, next_index)
        _directory_items.append((l, li, True))

    xbmcplugin.addDirectoryItems(plugin.handle, _directory_items, len(_directory_items))
    xbmcplugin.setContent(plugin.handle, "albums")
    if fixed_view_mode:
        xbmc.executebuiltin("Container.SetViewMode({0})".format(albums_view_mode))
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route("/musicmp3/artists_albums/<link>")
def artists_albums(link):
    musicmp3_api = musicMp3(MUSICMP3_DIR)
    url = unquote(link)
    albums = musicmp3_api.artist_albums(url)

    _directory_items = []
    for a in albums:
        li = xbmcgui.ListItem("{0}[CR][COLOR=darkmagenta]{1}[/COLOR]".format(a.get("title"), a.get("artist")))
        li.setArt({"thumb": a.get("image"), "icon": a.get("image")})
        li.setInfo(
            "music",
            {"title": a.get("title"), "artist": a.get("artist"), "album": a.get("title"), "year": a.get("date")},
        )
        li.setProperty("Album_Description", a.get("details"))
        _directory_items.append((plugin.url_for(musicmp3_album, quote(a.get("link"))), li, True))

    xbmcplugin.addDirectoryItems(plugin.handle, _directory_items, len(_directory_items))
    xbmcplugin.setContent(plugin.handle, "albums")
    if fixed_view_mode:
        xbmc.executebuiltin("Container.SetViewMode({0})".format(albums_view_mode))
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route("/musicmp3/album/<link>")
def musicmp3_album(link):
    musicmp3_api = musicMp3(MUSICMP3_DIR)
    url = unquote(link)
    tracks = musicmp3_api.album_tracks(url)
    _directory_items = []
    for t in tracks:
        _infolabels = {
            "title": t.get("title"),
            "artist": t.get("artist"),
            "album": t.get("album"),
            "duration": t.get("duration"),
        }
        li = xbmcgui.ListItem(t.get("title"))
        li.setProperty("IsPlayable", "true")
        li.setArt({"thumb": t.get("image"), "icon": t.get("image")})
        li.setInfo("music", _infolabels)
        _directory_items.append(
            (plugin.url_for(musicmp3_play, track_id=t.get("track_id"), rel=t.get("rel")), li, False)
        )

    xbmcplugin.addDirectoryItems(plugin.handle, _directory_items, len(_directory_items))
    xbmcplugin.setContent(plugin.handle, "songs")
    if fixed_view_mode:
        xbmc.executebuiltin("Container.SetViewMode({0})".format(songs_view_mode))
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route("/musicmp3/play/<track_id>/<rel>")
def musicmp3_play(track_id, rel):
    musicmp3_api = musicMp3(MUSICMP3_DIR)
    _track = musicmp3_api.get_track(rel)
    _infolabels = {"title": _track.title, "artist": _track.artist, "album": _track.album, "duration": _track.duration}
    li = xbmcgui.ListItem(_track.title, path=musicmp3_api.play_url(track_id, rel))
    li.setInfo("music", _infolabels)
    li.setArt({"thumb": _track.image, "icon": _track.image})
    li.setMimeType("audio/mpeg")
    li.setContentLookup(False)
    xbmcplugin.setResolvedUrl(plugin.handle, True, li)


if __name__ == "__main__":
    plugin.run(sys.argv)
