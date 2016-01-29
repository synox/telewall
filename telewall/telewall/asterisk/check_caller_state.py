import logging
from event import Event
from telewall.core import phonebook
from telewall.asterisk.asterisk_state import AsteriskState
from telewall.core.model import Persistence
from telewall.core.config import Config

LOG = logging.getLogger(__name__)


class CheckCallerState(AsteriskState):
    """ identifies the caller and decides how to handle the call.
    """

    def __init__(self, call):
        """
        Create the state instance
        :param call: the managing class, used for callbacks
        """
        super(CheckCallerState, self).__init__(call)
        self.call = call

    def enter(self):
        """ start recording. Asterisk stopps and saves the recording automatically on hangup.         """
        self._watch_channel_hangup()

        event = None

        self.call.call_state.set_caller(self.call.phone_number)

        if self._is_blocked(self.call.phone_number):
            event = Event.CALLER_REFUSED
            self.call.client.channels.setChannelVar(channelId=self.call.channel_incoming.id, variable='CDR(blocked)',
                                                    value='1')
            self.call.channel_incoming.answer()
            self.call.set_telewall_call_state('refused')
            self.call.call_state.refuse()
        else:
            phonebook.lookup(phone_number=self.call.phone_number)
            # set caller again after name lookup
            self.call.call_state.set_caller(self.call.phone_number)

            event = Event.CALLER_ALLOWED
            self.call.client.channels.setChannelVar(channelId=self.call.channel_incoming.id, variable='CDR(blocked)',
                                                    value='0')
            self.call.set_telewall_call_state('allowed')
            self.call.call_state.permit()

        self.cleanup()
        self.call.state_machine.change_state(event)

    def _is_blocked(self, phone_number):
        """ check if the phone_number is blocked.
        :param TelephoneNumber phone_number: number to check
        :return: True if the phone_number is blocked
        """
        with Persistence(Config.TELEWALL_DATABASE_PATH) as p:
            return p.is_blocked(phone_number)

    def cleanup(self):
        """ Close handles and unsubscribe from events         """
        self._cleanup_watch_channel_hangup()

    def on_hangup(self, channel, event):
        """ when user hang up close channel and change state
        :param channel: the channel
        :param event: the hangup event
        """
        self.cleanup()
        self.call.state_machine.change_state(Event.HANGUP)
