import logging
import uuid
import requests
from asterisk_state import AsteriskState
from event import Event

LOG = logging.getLogger(__name__)


class GenericPlaybackState(AsteriskState):
    """
    Plays a sound and continues to the next state, if a transition for the Event Event.PLAYBACK_COMPLETE is
    configured. DTMF events can be handles by a subclass.
    """

    def __init__(self, call, sound):
        """
        Create the state instance
        :param call: the managing class, used for callbacks
        :param sound: the sound to play (can also be changed at runtime by overriding get_media())
        """
        super(GenericPlaybackState, self).__init__(call)
        self.hangup_channel1_event = None
        self.hangup_channel2_event = None
        self.dtmf_event = None
        self.playback_id = None
        self.playback = None
        self.playback_finished = None
        self.sound = sound

    def enter(self):
        self._watch_channel_hangup()


        self.call.channel_incoming.answer()
        self.dtmf_event = self.call.channel_incoming.on_event('ChannelDtmfReceived', self.on_dtmf)
        self.playback_finished = self.call.client.on_event('PlaybackFinished', self.on_playback_finished)
        self.playback_id = str(uuid.uuid4())
        if self.call.bridge:
            self.playback = self.call.bridge.playWithId(playbackId=self.playback_id, media=self.get_media())
        else:
            self.playback = self.call.channel_incoming.playWithId(playbackId=self.playback_id, media=self.get_media())

        LOG.debug('playback: %s', self.playback)

    def get_media(self):
        """
        Method can be overwritten by subclass to provide dynamic sound file at runtime.
        :return: the sound file to be used. must be prefixed with 'sound:' or 'recording:'
        """
        return self.sound

    def cleanup(self):
        """ Close handles and unsubscribe from events         """
        self.playback_finished.close()
        if self.playback:
            try:
                self.playback.stop()
            except requests.HTTPError:
                pass
        self.dtmf_event.close()
        self._cleanup_watch_channel_hangup()

    def on_playback_finished(self, event):
        """ when playback finished
        :param event: the triggered event
        :type event: PlaybackFinished
        """
        if self.playback_id == event.get('playback').get('id'):
            self.playback = None

            if self.call.state_machine.has_transition(self, Event.PLAYBACK_COMPLETE):
                self.cleanup()
                self.call.state_machine.change_state(Event.PLAYBACK_COMPLETE)

    def on_hangup(self, channel, event):
        """ when user hang up close channel and change state
        :param channel: the channel
        :param event: the hangup event
        """
        self.cleanup()
        self.call.state_machine.change_state(Event.HANGUP)

    def on_dtmf(self, channel, event):
        """ can be overwritten by subclass to implement dtmf handling
        :param channel: then channel on which dtmf was received
        :param event: the ChannelDtmfReceived event
        :type event: ChannelDtmfReceived
        :return:
        """
        pass
