import logging
from event import Event
from telewall.asterisk import Constants
from telewall.asterisk.asterisk_state import AsteriskState

LOG = logging.getLogger(__name__)


class RecordingState(AsteriskState):
    """ creates a custom announcement using asterisks recording feature.
    """

    def __init__(self, call):
        """
        Create the state instance
        :param call: the managing class, used for callbacks
        """
        super(RecordingState, self).__init__(call)
        self.recording = None

    def enter(self):
        """ start recording. Asterisk stopps and saves the recording automatically on hangup.         """
        self._watch_channel_hangup()
        self.recording = self.call.channel_incoming.record(name=Constants.CUSTOM_ANNOUNCEMENT_RECORDING,
                                                           format='wav',
                                                           beep=True,
                                                           ifExists='overwrite')

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
