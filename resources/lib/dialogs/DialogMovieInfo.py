# -*- coding: utf8 -*-

# Copyright (C) 2015 - Philipp Temminghoff <phil65@kodi.tv>
# This program is Free Software see LICENSE file for details

import threading

import xbmc
import xbmcgui

from resources.lib import Utils
from resources.lib import TheMovieDB as tmdb
from resources.lib import omdb
from resources.lib import ImageTools
from resources.lib.WindowManager import wm
from DialogBaseInfo import DialogBaseInfo

from kodi65 import addon
from kodi65 import kodijson
from ActionHandler import ActionHandler

ID_LIST_SIMILAR = 150
ID_LIST_SETS = 250
ID_LIST_YOUTUBE = 350
ID_LIST_LISTS = 450
ID_LIST_STUDIOS = 550
ID_LIST_CERTS = 650
ID_LIST_CREW = 750
ID_LIST_GENRES = 850
ID_LIST_KEYWORDS = 950
ID_LIST_ACTORS = 1000
ID_LIST_REVIEWS = 1050
ID_LIST_VIDEOS = 1150
ID_LIST_IMAGES = 1250
ID_LIST_BACKDROPS = 1350

ID_BUTTON_PLAY_NORESUME = 8
ID_BUTTON_PLAY_RESUME = 9
ID_BUTTON_TRAILER = 10
ID_BUTTON_PLOT = 132
ID_BUTTON_MANAGE = 445
ID_BUTTON_SETRATING = 6001
ID_BUTTON_OPENLIST = 6002
ID_BUTTON_FAV = 6003
ID_BUTTON_ADDTOLIST = 6005
ID_BUTTON_RATED = 6006

ch = ActionHandler()


def get_window(window_type):

    class DialogMovieInfo(DialogBaseInfo, window_type):

        def __init__(self, *args, **kwargs):
            super(DialogMovieInfo, self).__init__(*args, **kwargs)
            self.type = "Movie"
            data = tmdb.extended_movie_info(movie_id=kwargs.get('id'),
                                            dbid=self.dbid)
            if not data:
                return None
            self.info, self.data, self.states = data
            sets_thread = SetItemsThread(self.info.get_property("set_id"))
            self.omdb_thread = Utils.FunctionThread(function=omdb.get_movie_info,
                                                    param=self.info.get_property("imdb_id"))
            self.omdb_thread.start()
            sets_thread.start()
            self.info.update_properties(ImageTools.blur(self.info.get_art("thumb")))
            if "dbid" not in self.info.get_infos():
                self.info.set_art("poster", Utils.get_file(self.info.get_art("poster")))
            sets_thread.join()
            self.setinfo = sets_thread.setinfo
            self.info.update_properties({"set.%s" % k: v for k, v in sets_thread.setinfo.iteritems()})
            set_ids = [item.get_property("id") for item in sets_thread.listitems]
            self.data["similar"] = [i for i in self.data["similar"] if i.get_property("id") not in set_ids]
            self.listitems = [(ID_LIST_ACTORS, self.data["actors"]),
                              (ID_LIST_SIMILAR, self.data["similar"]),
                              (ID_LIST_SETS, sets_thread.listitems),
                              (ID_LIST_LISTS, self.data["lists"]),
                              (ID_LIST_STUDIOS, self.data["studios"]),
                              (ID_LIST_CERTS, self.data["releases"]),
                              (ID_LIST_CREW, self.data["crew"]),
                              (ID_LIST_GENRES, self.data["genres"]),
                              (ID_LIST_KEYWORDS, self.data["keywords"]),
                              (ID_LIST_REVIEWS, self.data["reviews"]),
                              (ID_LIST_VIDEOS, self.data["videos"]),
                              (ID_LIST_IMAGES, self.data["images"]),
                              (ID_LIST_BACKDROPS, self.data["backdrops"])]

        def onInit(self):
            super(DialogMovieInfo, self).onInit()
            super(DialogMovieInfo, self).update_states()
            self.get_youtube_vids("%s %s, movie" % (self.info.label,
                                                    self.info.get_info("year")))
            self.join_omdb_async()

        def onClick(self, control_id):
            super(DialogMovieInfo, self).onClick(control_id)
            ch.serve(control_id, self)

        def onAction(self, action):
            super(DialogMovieInfo, self).onAction(action)
            ch.serve_action(action, self.getFocusId(), self)

        @ch.click(ID_BUTTON_TRAILER)
        def play_trailer(self, control_id):
            listitem = self.getControl(ID_LIST_VIDEOS).getListItem(0)
            youtube_id = listitem.getProperty("youtube_id")
            wm.play_youtube_video(youtube_id=youtube_id,
                                  listitem=listitem,
                                  window=self)

        @ch.click(ID_LIST_STUDIOS)
        def open_company_list(self, control_id):
            filters = [{"id": self.FocusedItem(control_id).getProperty("id"),
                        "type": "with_companies",
                        "typelabel": addon.LANG(20388),
                        "label": self.FocusedItem(control_id).getLabel().decode("utf-8")}]
            wm.open_video_list(prev_window=self,
                               filters=filters)

        @ch.click(ID_LIST_REVIEWS)
        def show_review(self, control_id):
            author = self.FocusedItem(control_id).getProperty("author")
            text = "[B]%s[/B][CR]%s" % (author, Utils.clean_text(self.FocusedItem(control_id).getProperty("content")))
            xbmcgui.Dialog().textviewer(heading=addon.LANG(207),
                                        text=text)

        @ch.click(ID_LIST_KEYWORDS)
        def open_keyword_list(self, control_id):
            filters = [{"id": self.FocusedItem(control_id).getProperty("id"),
                        "type": "with_keywords",
                        "typelabel": addon.LANG(32114),
                        "label": self.FocusedItem(control_id).getLabel().decode("utf-8")}]
            wm.open_video_list(prev_window=self,
                               filters=filters)

        @ch.click(ID_LIST_GENRES)
        def open_genre_list(self, control_id):
            filters = [{"id": self.FocusedItem(control_id).getProperty("id"),
                        "type": "with_genres",
                        "typelabel": addon.LANG(135),
                        "label": self.FocusedItem(control_id).getLabel().decode("utf-8")}]
            wm.open_video_list(prev_window=self,
                               filters=filters)

        @ch.click(ID_LIST_CERTS)
        def open_cert_list(self, control_id):
            info = self.FocusedItem(control_id).getVideoInfoTag()
            filters = [{"id": self.FocusedItem(control_id).getProperty("iso_3166_1"),
                        "type": "certification_country",
                        "typelabel": addon.LANG(32153),
                        "label": self.FocusedItem(control_id).getProperty("iso_3166_1")},
                       {"id": self.FocusedItem(control_id).getProperty("certification"),
                        "type": "certification",
                        "typelabel": addon.LANG(32127),
                        "label": self.FocusedItem(control_id).getProperty("certification")},
                       {"id": str(info.getYear()),
                        "type": "year",
                        "typelabel": addon.LANG(345),
                        "label": str(info.getYear())}]
            wm.open_video_list(prev_window=self,
                               filters=filters)

        @ch.click(ID_LIST_LISTS)
        def open_lists_list(self, control_id):
            wm.open_video_list(prev_window=self,
                               mode="list",
                               list_id=self.FocusedItem(control_id).getProperty("id"),
                               filter_label=self.FocusedItem(control_id).getLabel().decode("utf-8"))

        @ch.click(ID_BUTTON_OPENLIST)
        def show_list_dialog(self, control_id):
            xbmc.executebuiltin("ActivateWindow(busydialog)")
            movie_lists = tmdb.get_account_lists()
            listitems = ["%s (%i)" % (i["name"], i["item_count"]) for i in movie_lists]
            listitems = [addon.LANG(32134), addon.LANG(32135)] + listitems
            xbmc.executebuiltin("Dialog.Close(busydialog)")
            index = xbmcgui.Dialog().select(addon.LANG(32136), listitems)
            if index == -1:
                pass
            elif index < 2:
                wm.open_video_list(prev_window=self,
                                   mode="favorites" if index == 0 else "rating")
            else:
                wm.open_video_list(prev_window=self,
                                   mode="list",
                                   list_id=movie_lists[index - 2]["id"],
                                   filter_label=movie_lists[index - 2]["name"],
                                   force=True)

        @ch.click(ID_BUTTON_PLOT)
        def show_plot(self, control_id):
            xbmcgui.Dialog().textviewer(heading=addon.LANG(207),
                                        text=self.info.get_info("plot"))

        @ch.click(ID_BUTTON_SETRATING)
        def set_rating_dialog(self, control_id):
            rating = Utils.get_rating_from_selectdialog()
            if tmdb.set_rating(media_type="movie",
                               media_id=self.info.get_property("id"),
                               rating=rating,
                               dbid=self.info.get("dbid")):
                self.update_states()

        @ch.click(ID_BUTTON_ADDTOLIST)
        def add_to_list_dialog(self, control_id):
            xbmc.executebuiltin("ActivateWindow(busydialog)")
            account_lists = tmdb.get_account_lists()
            listitems = ["%s (%i)" % (i["name"], i["item_count"]) for i in account_lists]
            listitems.insert(0, addon.LANG(32139))
            listitems.append(addon.LANG(32138))
            xbmc.executebuiltin("Dialog.Close(busydialog)")
            index = xbmcgui.Dialog().select(heading=addon.LANG(32136),
                                            list=listitems)
            if index == 0:
                listname = xbmcgui.Dialog().input(heading=addon.LANG(32137),
                                                  type=xbmcgui.INPUT_ALPHANUM)
                if not listname:
                    return None
                list_id = tmdb.create_list(listname)
                xbmc.sleep(1000)
                tmdb.change_list_status(list_id=list_id,
                                        movie_id=self.info.get_property("id"),
                                        status=True)
            elif index == len(listitems) - 1:
                self.remove_list_dialog(account_lists)
            elif index > 0:
                tmdb.change_list_status(account_lists[index - 1]["id"], self.info.get_property("id"), True)
                self.update_states()

        @ch.click(ID_BUTTON_FAV)
        def change_list_status(self, control_id):
            tmdb.change_fav_status(media_id=self.info.get_property("id"),
                                   media_type="movie",
                                   status=str(not bool(self.states["favorite"])).lower())
            self.update_states()

        @ch.click(ID_BUTTON_RATED)
        def open_rating_list(self, control_id):
            wm.open_video_list(prev_window=self,
                               mode="rating")

        @ch.click(ID_BUTTON_PLAY_RESUME)
        def play_movie_resume(self, control_id):
            self.exit_script()
            xbmc.executebuiltin("Dialog.Close(movieinformation)")
            kodijson.play_media("movie", self.info["dbid"], True)

        @ch.click(ID_BUTTON_PLAY_NORESUME)
        def play_movie_no_resume(self, control_id):
            self.exit_script()
            xbmc.executebuiltin("Dialog.Close(movieinformation)")
            kodijson.play_media("movie", self.info["dbid"], False)

        @ch.click(ID_BUTTON_MANAGE)
        def show_manage_dialog(self, control_id):
            options = []
            movie_id = str(self.info.get("dbid", ""))
            imdb_id = str(self.info.get("imdb_id", ""))
            if movie_id:
                call = "RunScript(script.artwork.downloader,mediatype=movie,dbid={}%s)".format(movie_id)
                options += [[addon.LANG(413), call % "mode=gui"],
                            [addon.LANG(14061), call % ""],
                            [addon.LANG(32101), call % "mode=custom,extrathumbs"],
                            [addon.LANG(32100), call % "mode=custom"]]
            else:
                options += [[addon.LANG(32165), "RunPlugin(plugin://plugin.video.couchpotato_manager/movies/add?imdb_id=" + imdb_id + ")||Notification(script.extendedinfo,%s))" % addon.LANG(32059)],
                            [addon.LANG(32170), "RunPlugin(plugin://plugin.video.trakt_list_manager/watchlist/movies/add?imdb_id=" + imdb_id + ")"]]
            if xbmc.getCondVisibility("system.hasaddon(script.libraryeditor)") and movie_id:
                options.append([addon.LANG(32103), "RunScript(script.libraryeditor,DBID=" + movie_id + ")"])
            options.append([addon.LANG(1049), "Addon.OpenSettings(script.extendedinfo)"])
            selection = xbmcgui.Dialog().select(heading=addon.LANG(32133),
                                                list=[i[0] for i in options])
            if selection == -1:
                return None
            for item in options[selection][1].split("||"):
                xbmc.executebuiltin(item)

        def update_states(self):
            xbmc.sleep(2000)  # delay because MovieDB takes some time to update
            _, __, self.states = tmdb.extended_movie_info(movie_id=self.info.get_property("id"),
                                                          dbid=self.dbid,
                                                          cache_time=0)
            super(DialogMovieInfo, self).update_states()

        def remove_list_dialog(self, account_lists):
            listitems = ["%s (%i)" % (d["name"], d["item_count"]) for d in account_lists]
            index = xbmcgui.Dialog().select(addon.LANG(32138), listitems)
            if index >= 0:
                tmdb.remove_list(account_lists[index]["id"])
                self.update_states()

        @Utils.run_async
        def join_omdb_async(self):
            self.omdb_thread.join()
            Utils.pass_dict_to_skin(data=self.omdb_thread.listitems,
                                    prefix="omdb.",
                                    window_id=self.window_id)

    class SetItemsThread(threading.Thread):

        def __init__(self, set_id=""):
            threading.Thread.__init__(self)
            self.set_id = set_id

        def run(self):
            if self.set_id:
                self.listitems, self.setinfo = tmdb.get_set_movies(self.set_id)
            else:
                self.listitems = []
                self.setinfo = {}

    return DialogMovieInfo
