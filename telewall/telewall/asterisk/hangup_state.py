import logging

from telewall.asterisk.asterisk_state import AsteriskState

LOG = logging.getLogger(__name__)


class HungUpState(AsteriskState):
    """ User hang up, cleanup the states   """

    def __init__(self, call):
        """
        Create the state instance
        :param call: the managing class, used for callbacks
        """
        super(HungUpState, self).__init__(call)

    def enter(self):
        """ cleanup handles when user hang up         """
        channel_name = self.call.channel_incoming.json.get('name')
        LOG.info('Channel %s hung up', channel_name)

        # close both channels
        self._safe_close_channel(self.call.channel_incoming)
        self._safe_close_channel(self.call.channel_tohandset)

        if self.call.bridge:
            self._safe_destroy_bridge(self.call.bridge)

        if self.call.call_state:
            self.call.call_state.hangup()
