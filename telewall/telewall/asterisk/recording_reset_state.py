import requests

from event import Event
from generic_playback_state import GenericPlaybackState
from telewall.asterisk import Constants


class ResetRecordingState(GenericPlaybackState):
    """ Asks the user to confirm and then deletes the custom announcement.    """

    def __init__(self, call):
        super(ResetRecordingState, self).__init__(call, 'sound:/telewall/sounds/de/reset-announcement-confirm')

    def on_dtmf(self, channel, event):
        digit = event.get('digit')
        if digit == '1':
            self.cleanup()
            try:
                # recording may not exist
                self.call.client.recordings.deleteStored(recordingName=Constants.CUSTOM_ANNOUNCEMENT_RECORDING)
            except requests.HTTPError as e:
                if e.response.status_code != requests.codes.not_found:
                    raise e
            self.call.state_machine.change_state(Event.ACTION_COMPLETE)
