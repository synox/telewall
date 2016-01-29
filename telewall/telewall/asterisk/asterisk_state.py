import logging
import requests

LOG = logging.getLogger(__name__)


class AsteriskState(object):
    """ abstract state implementation, should be used as class parent"""

    def __init__(self, call):
        """
        Create the state instance
        :param call: the managing class, used for callbacks
        """
        self.call = call
        self.hangup_channel1_event = None
        self.hangup_channel2_event = None

    def enter(self):
        """ run the state specific actions         """
        pass

    def _watch_channel_hangup(self):
        self.hangup_channel1_event = self.call.channel_incoming.on_event('ChannelHangupRequest', self.on_hangup)
        if self.call.channel_tohandset:
            self.hangup_channel2_event = self.call.channel_tohandset.on_event('ChannelHangupRequest', self.on_hangup)

    def _cleanup_watch_channel_hangup(self):
        self.hangup_channel1_event.close()
        if self.hangup_channel2_event:
            self.hangup_channel2_event.close()

    def _safe_close_channel(self, channel):
        """ close the channel, ignore the not_found error.
        :param channel: the channel to close
        """
        try:
            if channel:
                channel.hangup()
        except requests.HTTPError as e:
            if e.response.status_code != requests.codes.not_found:
                raise e

    def _safe_destroy_bridge(self, bridge):
        """ destroy the bridge, ignore the not_found error.
        :param bridge: the bridge to destroy
        """
        try:
            if bridge:
                LOG.debug('destroying bridge %s', bridge)
                bridge.destroy()
        except requests.HTTPError as e:
            if e.response.status_code != requests.codes.not_found:
                raise e

    def on_hangup(self, channel, event):
        """ callback on hangup, must be overwritten
        """
        pass