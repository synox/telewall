import logging

from event import Event
from telewall.asterisk.asterisk_state import AsteriskState
from telewall.core.config import Config
from telewall.core.model import Persistence

LOG = logging.getLogger(__name__)


class CallConnectedState(AsteriskState):
    """ the call is bridged to the handset and the users call talk.
    """

    def __init__(self, call):
        """
        Create the state instance
        :param call: the managing class, used for callbacks
        """
        super(CallConnectedState, self).__init__(call)
        self.dtmf_event = None
        self.pressed_keys = []

    def enter(self):
        """ start recording. Asterisk stopps and saves the recording automatically on hangup.         """
        self._watch_channel_hangup()

        # react to dtmf events from the handset (and not from the first channel)
        self.dtmf_event = self.call.channel_tohandset.on_event('ChannelDtmfReceived', self.on_dtmf)
        self.call.call_state.add_listener(self.call_state_change)

    def on_dtmf(self, channel, event):
        """ handles DTMF signals (from any of the endpoints, they can not be distinguished.
        :param channel: channel where event was fired
        :param event: the dtmf event
        """
        digit = event.get('digit')
        self.pressed_keys += digit
        LOG.debug('pressed keys: %s', self.pressed_keys)
        press_count = self.pressed_keys.count('#')
        LOG.debug("pressed '#' %d times", press_count)

        if press_count >= Config.DTMF_DIGITS_TO_BLOCK_CALLER:
            with Persistence(Config.TELEWALL_DATABASE_PATH) as p:
                if not p.is_blocked(self.call.phone_number):
                    p.block(self.call.phone_number, '', 'dtmf')

            self.call.call_state.refuse()
            self.cleanup()
            self.call.state_machine.change_state(Event.CALLER_REFUSED)

        # easter egg, hidden feature, not used in production
        if Config.EASTEREGGS_ENABLED and self.pressed_keys == ['3', '6', '9']:
            self.pressed_keys = []
            # playback_finished is not handled, not required for this demo
            self.call.bridge.play(media='sound:tt-monkeys')

    def call_state_change(self, event, call_state):
        """ react to call state changes, specifically to 'refusing' state.
        :param event: asterisk event
        :param call_state: call state instance
        """
        LOG.debug('call state changed to %s', call_state.get_current_state())

        if call_state.is_refusing:
            with Persistence(Config.TELEWALL_DATABASE_PATH) as p:
                if not p.is_blocked(self.call.phone_number):
                    p.block(self.call.phone_number, '', 'dtmf')

            # the call state is not changed, as it was already set to 'refusing'.
            self.cleanup()
            self.call.state_machine.change_state(Event.CALLER_REFUSED)

    def cleanup(self):
        """ Close handles and unsubscribe from events         """
        self._cleanup_watch_channel_hangup()
        self.dtmf_event.close()
        self.pressed_keys = []
        self.call.call_state.remove_listener(self.call_state_change)

    def on_hangup(self, channel, event):
        """ when any user hang up close channels and change state
        :param channel: the channel
        :param event: the hangup event
        """
        self.cleanup()
        self.call.state_machine.change_state(Event.HANGUP)
