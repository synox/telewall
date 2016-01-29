# python 3
import logging
import threading
from threading import Timer
import time

import ari
import requests

from telewall.core.model import Persistence

DB_PATH = '/telewall/data/database.sqlite3'

LOG = logging.getLogger(__name__)


class TestCall(object):
    def __init__(self, console_channel, client):
        self.console_channel = console_channel
        self.telewall_channel = None
        self.running = True
        self.call_states = set()
        self.listeners = {}
        self.client = client
        Timer(15, self.stop)

    def stop(self):
        self.running = False
        self.hangup()

    def send_dtmf(self, digit):
        self._find_channels()

        self.console_channel.sendDTMF(channelId=self.console_channel.id, dtmf=digit)

    def _find_channels(self):
        if self.telewall_channel:
            return

        time.sleep(1)

        channels = self.client.channels.list()
        for channel in channels:
            if channel.id == self.console_channel.id:
                pass
            else:
                self.telewall_channel = channel
        LOG.info('console channel: %s %s', self.console_channel, self.console_channel.json.get('name'))
        if self.telewall_channel:
            LOG.info('telewall channel: %s %s', self.telewall_channel, self.telewall_channel.json.get('name'))

    def _monitor_call(self):
        LOG.debug('started call monitor')
        self.call_states = set()

        self._find_channels()

        if self.telewall_channel:
            channel_to_monitor = self.telewall_channel
        else:
            channel_to_monitor = self.console_channel

        for s in range(1, 30):  # stop after 30 seconds
            if not self.running:
                break
            try:

                channels = self.client.channels.list()
                LOG.debug('current open channels:')
                for channel in channels:
                    name = channel.json.get('name')
                    state = channel.json.get('state')

                    if channel.id == channel_to_monitor.id:
                        if state not in self.call_states:
                            self.call_states.add(state)
                            self._notify(state)
                    LOG.debug('name=%s, state=%s', name, state)

            except requests.exceptions.HTTPError as e:
                # this implies the conneciton was closed (hangup)
                self.call_states.add('Down')
                self._notify('Down')
                LOG.info('connection was closed with error: ', exc_info=True)

            time.sleep(1)

    def get_call_states(self):
        LOG.debug('call states: %s', self.call_states)
        return self.call_states

    def hangup(self):
        self._find_channels()
        for channel in self.client.channels.list():
            try:
                self.client.channels.hangup(channelId=channel.id)
            except:
                pass

    def on_call_status(self, state, cb):
        """
        #
        see states on: http://doxygen.asterisk.org/asterisk1.8/channelstate_8h.html#03585bc87e5bbd0f4d11bc789734c660
        :param state: on of 'Down', 'Rsrved', 'OffHook', 'Dialing', 'Ring', 'Ringing', 'Up', 'Busy', 'Dialing Offhook', 'Pre-ring', 'Unknown'
        :param cb: callback
        :return: None
        """
        self.listeners[state] = cb

    def _notify(self, state):
        if state in self.listeners:
            LOG.debug('sending new state  %s', state)
            self.listeners[state]()


class TestUtil(object):
    def __init__(self):
        self.client = None

    def _start_client(self):
        LOG.debug('starting ari')
        self.client = ari.connect('http://localhost:8088', 'telewall-tester', 'telewall-tester')

    def make_call_to_incoming(self, callerid):
        return self.call_extension('incoming', '100', callerid)

    def call_extension(self, context, extension, callerid):
        if not self.client:
            self._start_client()
        LOG.debug('faking call using CONSOLE to incoming/%s', extension)
        console_channel = self.client.channels.originate(endpoint='CONSOLE/dsp',
                                                         extension=extension,
                                                         context=context,
                                                         callerId=callerid)

        call = TestCall(console_channel, self.client)

        thread = threading.Thread(target=call._monitor_call)
        thread.daemon = True
        thread.start()

        return call

    def unblock_callerid(self, phone_number):
        with Persistence(DB_PATH) as p:
            p.unblock(phone_number)

    def is_blocked_callerid(self, phone_number):
        with Persistence(DB_PATH) as p:
            return p.is_blocked(phone_number)

    def block_callerid(self, phone_number):
        with Persistence(DB_PATH) as p:
            if not p.is_blocked(phone_number):
                p.block(phone_number, '', 'Unit-Test')
