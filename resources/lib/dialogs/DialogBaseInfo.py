# -*- coding: utf8 -*-

# Copyright (C) 2015 - Philipp Temminghoff <phil65@kodi.tv>
# This program is Free Software see LICENSE file for details

import xbmcgui
from ..Utils import *
from ..TheMovieDB import *
from ..WindowManager import wm
from ..OnClickHandler import OnClickHandler
from .. import VideoPlayer
from BaseClasses import DialogXML, WindowXML
PLAYER = VideoPlayer.VideoPlayer()
ch = OnClickHandler()


class DialogBaseInfo(WindowXML if SETTING("window_mode") == "true" else DialogXML):
    ACTION_PREVIOUS_MENU = [92, 9]
    ACTION_EXIT_SCRIPT = [13, 10]

    def __init__(self, *args, **kwargs):
        super(DialogBaseInfo, self).__init__(*args, **kwargs)
        self.logged_in = check_login()
        self.dbid = kwargs.get('dbid')
        self.data = None
        self.info = {}
        check_version()

    def onInit(self, *args, **kwargs):
        super(DialogBaseInfo, self).onInit()
        HOME.setProperty("ImageColor", self.info.get('ImageColor', ""))
        self.window = xbmcgui.Window(self.window_id)
        self.window.setProperty("type", self.type)
        self.window.setProperty("tmdb_logged_in", self.logged_in)
        # present for jurialmunkey
        HOME.setProperty("ExtendedInfo_fanart", self.info.get("fanart", ""))

    def fill_lists(self):
        for container_id, listitems in self.listitems:
            try:
                self.getControl(container_id).reset()
                self.getControl(container_id).addItems(listitems)
            except:
                log("Notice: No container with id %i available" % container_id)

    @ch.context(1250)
    def thumbnail_options(self):
        if not self.info.get("dbid"):
            return None
        selection = xbmcgui.Dialog().select(heading=LANG(22080),
                                            list=[LANG(32006)])
        if selection == 0:
            path = self.getControl(focus_id).getSelectedItem().getProperty("original")
            media_type = self.window.getProperty("type")
            params = '"art": {"poster": "%s"}' % path
            get_kodi_json(method="VideoLibrary.Set%sDetails" % media_type,
                          params='{ %s, "%sid":%s }' % (params, media_type.lower(), self.info['dbid']))

    @ch.context(1350)
    def fanart_options(self):
        if not self.info.get("dbid"):
            return None
        selection = xbmcgui.Dialog().select(heading=LANG(22080),
                                            list=[LANG(32007)])
        if selection == 0:
            path = self.getControl(focus_id).getSelectedItem().getProperty("original")
            media_type = self.window.getProperty("type")
            params = '"art": {"fanart": "%s"}' % path
            get_kodi_json(method="VideoLibrary.Set%sDetails" % media_type,
                          params='{ %s, "%sid":%s }' % (params, media_type.lower(), self.info['dbid']))

    @ch.context(1150)
    @ch.context(350)
    def download_video(self):
        selection = xbmcgui.Dialog().select(heading=LANG(22080),
                                            list=[LANG(33003)])
        if selection == 0:
            youtube_id = self.control.getSelectedItem().getProperty("youtube_id")
            import YDStreamExtractor
            vid = YDStreamExtractor.getVideoInfo(youtube_id,
                                                 quality=1)
            YDStreamExtractor.handleDownload(vid)

    def onAction(self, action):
        focus_id = self.getFocusId()
        if action in self.ACTION_PREVIOUS_MENU:
            self.close()
            wm.pop_stack()
        elif action in self.ACTION_EXIT_SCRIPT:
            self.close()
        if action == xbmcgui.ACTION_CONTEXT_MENU:
            ch.serve_context(focus_id, self)

    def open_credit_dialog(self, credit_id):
        info = get_credit_info(credit_id)
        listitems = []
        if "seasons" in info["media"]:
            listitems += handle_tmdb_seasons(info["media"]["seasons"])
        if "episodes" in info["media"]:
            listitems += handle_tmdb_episodes(info["media"]["episodes"])
        if not listitems:
            listitems += [{"label": LANG(19055)}]
        listitem, index = wm.open_selectdialog(listitems=listitems)
        if listitem["media_type"] == "episode":
            wm.open_episode_info(prev_window=self,
                                 season=listitems[index]["season"],
                                 episode=listitems[index]["episode"],
                                 tvshow_id=info["media"]["id"])
        elif listitem["media_type"] == "season":
            wm.open_season_info(prev_window=self,
                                season=listitems[index]["season"],
                                tvshow_id=info["media"]["id"])
