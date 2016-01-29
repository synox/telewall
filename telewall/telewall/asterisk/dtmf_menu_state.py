from generic_playback_state import GenericPlaybackState
from event import Event


class DtmfMenuState(GenericPlaybackState):
    """ Playback a sound and react to dtmf commands. This is a generic implementation.      """

    def __init__(self, call, sound, allowed_keys):
        super(DtmfMenuState, self).__init__(call, sound)
        self.allowed_keys = allowed_keys

    def on_dtmf(self, channel, event):
        digit = event.get('digit')
        if digit in self.allowed_keys:
            self.cleanup()
            self.call.state_machine.change_state(Event.get_dtmf_event(digit))
