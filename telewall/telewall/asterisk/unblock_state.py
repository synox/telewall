import logging
import re

from event import Event
from telewall.asterisk.asterisk_state import AsteriskState
from telewall.core.config import Config
from telewall.core.model import TelephoneNumber, Persistence

LOG = logging.getLogger(__name__)


class UnblockState(AsteriskState):
    """ unblocks a telephone number.
    """

    def __init__(self, call, dialed_extension):
        """
        Create the state instance
        :param call: the managing class, used for callbacks
        """
        super(UnblockState, self).__init__(call)
        self.recording = None
        self.dialed_extension = dialed_extension

    def enter(self):
        """ start recording. Asterisk stopps and saves the recording automatically on hangup.         """
        self._watch_channel_hangup()

        LOG.info('trying to unblock number, extension=%s', self.dialed_extension)

        matches = re.match(r'^[*]\d+[*](\d+)[#]$', self.dialed_extension)
        if matches:
            number = matches.group(1)
            phone_number = TelephoneNumber(number)
            LOG.info('unblocking  phone number %s', phone_number)
            with Persistence(Config.TELEWALL_DATABASE_PATH) as p:
                p.unblock(phone_number)

            self.cleanup()
            self.call.state_machine.change_state(Event.ACTION_COMPLETE)

        else:
            self.cleanup()
            self.call.state_machine.change_state(Event.INVALID_INPUT)

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
