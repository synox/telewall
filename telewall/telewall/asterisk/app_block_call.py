import logging
import thread
import time

import ari

from ending_state import EndingState
from event import Event
from generic_playback_state import GenericPlaybackState
from hangup_state import HungUpState
from state_machine import StateMachine
from telewall.asterisk.app_call_base import BaseAsteriskAppCall
from telewall.asterisk.block_state import BlockState

LOG = logging.getLogger(__name__)

client = None
stopped = False

APP_NAME = 'telewall-block'


class BlockCall(BaseAsteriskAppCall):
    """ blockes a caller using asterisk. A new instance is created for each call.   """

    def __init__(self, ari_client, channel, asterisk_app_name, dialed_extension):
        """
        :param ari_client: the ari client instance
        :param channel: the active channel with the handset
        """
        super(BlockCall, self).__init__(ari_client, channel, asterisk_app_name)
        self.dialed_extension = dialed_extension
        self.state_machine = None
        self.setup_state_machine()

    def setup_state_machine(self):
        """ setup the states and start the initial state """
        block = BlockState(self, self.dialed_extension)
        done = GenericPlaybackState(self, 'sound:/telewall/sounds/de/block-done')
        invalid = GenericPlaybackState(self, 'sound:/telewall/sounds/de/phonenumber-invalid')
        hungup_state = HungUpState(self)
        ending_state = EndingState(self)

        self.state_machine = StateMachine()

        self.state_machine.add_transition(block, Event.ACTION_COMPLETE, done)
        self.state_machine.add_transition(block, Event.INVALID_INPUT, invalid)

        self.state_machine.add_transition(done, Event.PLAYBACK_COMPLETE, ending_state)
        self.state_machine.add_transition(invalid, Event.PLAYBACK_COMPLETE, ending_state)

        # hangup event is in every state
        for state in [block, done, invalid]:
            self.state_machine.add_transition(state, Event.HANGUP, hungup_state)

        self.state_machine.start(block)


def stasis_start_cb(channel_obj, event):
    """ called when a channel connecting to this asterisk application.
    :param channel_obj: the channel
    :param event:  the StasisStart event
    """
    channel = channel_obj['channel']

    args = event.get('args')
    if not args:
        LOG.critical("""Error: No extension prvided to the Statis applicaiton 'telewall'.
            Check the extension.conf """)
        channel.hangup()
        return False

    channel.answer()
    BlockCall(client, channel, APP_NAME, dialed_extension=args[0])


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
