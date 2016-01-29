import logging

from event import Event
from telewall.asterisk import Constants
from telewall.asterisk.generic_playback_state import GenericPlaybackState

LOG = logging.getLogger(__name__)


class PlaybackRefusedState(GenericPlaybackState):
    """ play back the announcement when the call has been refused

      extends the generic playback state by using a dynamic sound (default or custom announcement) """

    def __init__(self, call, hangup_caller_when_hangup_handset=True):
        """
        Create the state instance
        :param call: the managing class, used for callbacks
        :param hangup_caller_when_hangup_handset: usually when one party leaves the bridge, all parties are hangup.
                with this setting as True the caller may still stay in the bridge event if the handset hangup.
                One usage may be to allow to caller to hear all the refuse announcement, while the handset is
                already hung up.
        """
        super(PlaybackRefusedState, self).__init__(call, Constants.DEFAULT_ANNOUNCEMENT)
        self.hangup_caller_when_hangup_handset = hangup_caller_when_hangup_handset

    def get_media(self):
        """
        :return: the custom or default announcement.
        """
        return self.call.get_announcement_media()

    def on_hangup(self, channel, event):
        """ when user hang up close channel and change state

        overrides super method, as hangup of channel to handset (2) does not close channel from caller (1).
        :param channel: the channel
        :param event: the hangup event
        """
        LOG.debug('first channel id = %s', self.call.channel_incoming.id)
        if self.call.channel_tohandset:
            LOG.debug('second channel id = %s', self.call.channel_tohandset.id)
        LOG.debug('hangup channel id = %s', channel.id)
        LOG.debug('hangup_caller_when_hangup_handset = %s', self.hangup_caller_when_hangup_handset)
        if self.call.channel_tohandset and channel.id == self.call.channel_tohandset.id and not self.hangup_caller_when_hangup_handset:
            # continue playback even if second channels is hangup.
            LOG.info('second channel hang up, but first channel may still be hearing the announcement')
            pass
        else:
            self.cleanup()
            self.call.state_machine.change_state(Event.HANGUP)
