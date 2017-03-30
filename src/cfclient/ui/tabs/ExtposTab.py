#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#     ||          ____  _ __
#  +------+      / __ )(_) /_______________ _____  ___
#  | 0xBC |     / __  / / __/ ___/ ___/ __ `/_  / / _ \
#  +------+    / /_/ / / /_/ /__/ /  / /_/ / / /_/  __/
#   ||  ||    /_____/_/\__/\___/_/   \__,_/ /___/\___/
#
#  Copyright (C) 2011-2013 Bitcraze AB
#
#  Crazyflie Nano Quadcopter Client
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.

#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
#  02110-1301, USA.

"""
An example template for a tab in the Crazyflie Client. It comes pre-configured
with the necessary QT Signals to wrap Crazyflie API callbacks and also
connects the connected/disconnected callbacks.
"""

import logging

from PyQt5 import uic
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QMessageBox

import threading

import zmq

import cfclient
from cfclient.ui.tab import Tab

__author__ = 'Bitcraze AB'
__all__ = ['ExposTab']

logger = logging.getLogger(__name__)

example_tab_class = uic.loadUiType(cfclient.module_path +
                                   "/ui/tabs/exampleTab.ui")[0]


class ExposTab(Tab, example_tab_class):
    """Tab for plotting logging data"""

    _connected_signal = pyqtSignal(str)
    _disconnected_signal = pyqtSignal(str)
    _log_data_signal = pyqtSignal(int, object, object)
    _log_error_signal = pyqtSignal(object, str)
    _param_updated_signal = pyqtSignal(str, str)
    _position_received_signal = pyqtSignal(float, float, float)

    def __init__(self, tabWidget, helper, *args):
        super(ExposTab, self).__init__(*args)
        self.setupUi(self)

        self.tabName = "External position"
        self.menuName = "External position"
        self.tabWidget = tabWidget

        self._helper = helper

        # Always wrap callbacks from Crazyflie API though QT Signal/Slots
        # to avoid manipulating the UI when rendering it
        self._connected_signal.connect(self._connected)
        self._disconnected_signal.connect(self._disconnected)
        self._log_data_signal.connect(self._log_data_received)
        self._param_updated_signal.connect(self._param_updated)
        self._position_received_signal.connect(self._position_received)

        # Connect the Crazyflie API callbacks to the signals
        self._helper.cf.connected.add_callback(
            self._connected_signal.emit)

        self._helper.cf.disconnected.add_callback(
            self._disconnected_signal.emit)

        self._ctx = zmq.Context()

        logger.info("Connecting socket to Crazyflie detector ...")
        self._socket = self._ctx.socket(zmq.PULL)
        self._socket.connect("tcp://127.0.0.1:7777")

        def receivePosition():
            while self._socket is not None:
                try:
                    msg = self._socket.recv_json()
                    if msg["detect"]:
                        self._position_received_signal.emit(msg["pos"][0],
                                                            msg["pos"][1],
                                                            msg["pos"][2])
                except Exception:
                    continue
        self._receive_thread = threading.Thread(target=receivePosition,
                                                daemon=True)
        self._receive_thread.start()

        self._connected = False

    def _connected(self, link_uri):
        """Callback when the Crazyflie has been connected"""
        self._connected = True

    def _disconnected(self, link_uri):
        """Callback for when the Crazyflie has been disconnected"""
        self._connected = False

    def _position_received(self, x, y, z):
        if self._connected:
            self._helper.cf.extpos.send_extpos(x, y, z+1.5)
        # logger.info("External position: {},{},{}".format(x, y, z))

    def _param_updated(self, name, value):
        """Callback when the registered parameter get's updated"""

        logger.debug("Updated {0} to {1}".format(name, value))

    def _log_data_received(self, timestamp, data, log_conf):
        """Callback when the log layer receives new data"""

        logger.debug("{0}:{1}:{2}".format(timestamp, log_conf.name, data))

    def _logging_error(self, log_conf, msg):
        """Callback from the log layer when an error occurs"""

        QMessageBox.about(self, "Example error",
                          "Error when using log config"
                          " [{0}]: {1}".format(log_conf.name, msg))
