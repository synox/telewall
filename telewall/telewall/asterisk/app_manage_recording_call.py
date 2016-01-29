import logging
import thread
import time

import ari

from ending_state import EndingState
from event import Event
from generic_playback_state import GenericPlaybackState
from hangup_state import HungUpState
from playbackrefused_state import PlaybackRefusedState
from dtmf_menu_state import DtmfMenuState
from recording_state import RecordingState
from recording_reset_state import ResetRecordingState
from state_machine import StateMachine
from telewall.asterisk.app_call_base import BaseAsteriskAppCall

LOG = logging.getLogger(__name__)

client = None
stopped = False

APP_NAME = 'telewall-managerecording'


class ManageRecordingCall(BaseAsteriskAppCall):
    """ manages the announcement using asterisk. A new instance is created for each call.   """

    def __init__(self, ari_client, channel, asterisk_app_name):
        """
        :param ari_client: the ari client instance
        :param channel: the active channel with the handset
        """
        super(ManageRecordingCall, self).__init__(ari_client, channel, asterisk_app_name)
        self.state_machine = None
        self.setup_state_machine()

    def setup_state_machine(self):
        """ setup the states and start the initial state """
        main_menu = DtmfMenuState(self, 'sound:/telewall/sounds/de/mainmenu', allowed_keys=['1', '2', '3'])
        playback = PlaybackRefusedState(self)
        recording_instruction = GenericPlaybackState(self, 'sound:/telewall/sounds/de/record-announcement-instruction')
        recording = RecordingState(self)
        recording_reset = ResetRecordingState(self)
        recording_reset_done = GenericPlaybackState(self, 'sound:/telewall/sounds/de/reset-announcement-done')
        hungup_state = HungUpState(self)
        ending_state = EndingState(self)

        self.state_machine = StateMachine()
        self.state_machine.add_transition(main_menu, Event.DTMF_1, playback)
        self.state_machine.add_transition(main_menu, Event.DTMF_2, recording_instruction)
        self.state_machine.add_transition(main_menu, Event.DTMF_3, recording_reset)

        # 1: playback
        self.state_machine.add_transition(playback, Event.PLAYBACK_COMPLETE, ending_state)

        # 2: recording
        self.state_machine.add_transition(recording_instruction, Event.PLAYBACK_COMPLETE, recording)

        # 3: reset recording
        self.state_machine.add_transition(recording_reset, Event.ACTION_COMPLETE, recording_reset_done)
        self.state_machine.add_transition(recording_reset_done, Event.PLAYBACK_COMPLETE, main_menu)

        # hangup event is in every state
        for state in [main_menu, playback, recording_instruction, recording, recording_reset,
                      recording_reset_done]:
            self.state_machine.add_transition(state, Event.HANGUP, hungup_state)

        self.state_machine.start(main_menu)


def stasis_start_cb(channel_obj, event):
    """ called when a channel connecting to this asterisk application.
    :param channel_obj: the channel
    :param event:  the StasisStart event
    """
    channel = channel_obj['channel']

    channel.answer()
    ManageRecordingCall(client, channel, APP_NAME)


def run():
    """run the asterisk application.    """
    global client
    while not stopped:
        try:
            # if the connection is ever lost, we have to try again and again!
            client = ari.connect('http://localhost:8088', 'telewall', 'telewall')
            client.on_channel_event('StasisStart', stasis_start_cb)
            client.run(apps=APP_NAME)
        except SystemExit:
            break
        except:
            LOG.exception('problem with ari client')
            time.sleep(5)  # wait 5 sec until retry


def start():
    """ run the asterisk application in a new thread.   """
    thread.start_new_thread(run, ())


def stop():
    """ stop asterisk.   """
    global stopped
    stopped = True


if __name__ == '__main__':
    # can be used to run from command line, for debugging
    logging.basicConfig(filename='/var/log/telewall-app.log', level=logging.WARN)
    logging.getLogger('telewall').setLevel(logging.DEBUG)
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    logging.getLogger('').addHandler(console)

    LOG.warn('running from cmd')
    run()
