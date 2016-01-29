import logging
import thread
import time

import ari

from ending_state import EndingState
from event import Event
from hangup_state import HungUpState
from playbackrefused_state import PlaybackRefusedState
from state_machine import StateMachine
from telewall.asterisk.app_call_base import BaseAsteriskAppCall
from telewall.asterisk.call_connected_state import CallConnectedState
from telewall.asterisk.call_handset_state import CallHandsetState
from telewall.asterisk.check_caller_state import CheckCallerState
from telewall.core.model import CallState

LOG = logging.getLogger(__name__)

client = None
stopped = False

APP_NAME = 'telewall-incoming'


class IncomingCall(BaseAsteriskAppCall):
    """ manages an incoming call using asterisk. A new instance is created for each call.   """

    def __init__(self, ari_client, channel, handset_endpoint, asterisk_app_name):
        """
        :param ari_client: the ari client instance
        :param channel: the active channel with the handset_endpoint
        """
        super(IncomingCall, self).__init__(ari_client, channel, asterisk_app_name)
        self.handset_endpoint = handset_endpoint
        self.call_state = CallState.instance()

        self.state_machine = None
        self.setup_state_machine()

    def setup_state_machine(self):
        """ setup the states and start the initial state """
        check_caller = CheckCallerState(self)
        call_handset = CallHandsetState(self)
        playback_refused = PlaybackRefusedState(self, hangup_caller_when_hangup_handset=False)
        call_connected = CallConnectedState(self)

        hungup_state = HungUpState(self)
        ending_state = EndingState(self)

        self.state_machine = StateMachine()

        # identification
        self.state_machine.add_transition(check_caller, Event.CALLER_ALLOWED, call_handset)
        self.state_machine.add_transition(check_caller, Event.CALLER_REFUSED, playback_refused)

        # allowed
        self.state_machine.add_transition(call_handset, Event.ANSWER, call_connected)
        self.state_machine.add_transition(call_handset, Event.BUSY, ending_state)
        self.state_machine.add_transition(call_connected, Event.CALLER_REFUSED, playback_refused)

        # refused
        self.state_machine.add_transition(playback_refused, Event.PLAYBACK_COMPLETE, ending_state)

        # hangup event is in every state (except the final states hangup and ending)
        for state in [check_caller, call_handset, playback_refused, playback_refused, call_connected]:
            self.state_machine.add_transition(state, Event.HANGUP, hungup_state)

        self.state_machine.start(check_caller)


def stasis_start_cb(channel_obj, event):
    """ called when a channel connecting to this asterisk application.
    :param channel_obj: the channel
    :param event:  the StasisStart event
    """
    channel = channel_obj['channel']

    # validate args
    args = event.get('args')
    if not args:
        LOG.critical("""Error: No arguments prvided to the Statis applicaiton 'telewall'.
            Check the extension.conf and the call to  'client.channels.originate'. """)
        channel.hangup()
        return False

    if args[0] == 'dialed':
        # call to handset (outgoing leg) is not handled here.
        LOG.debug('call to handset: %s', channel)
        return False

    LOG.info('Handle call of channel %s', channel.json.get('name'))

    IncomingCall(client, channel, handset_endpoint=args[0], asterisk_app_name=APP_NAME)


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
    global thr
    thr = thread.start_new_thread(run, ())


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
