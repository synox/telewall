"""
This module handles the user interface using leds, display and button.

GPIO: The GPIO modules are imported only with running the start method. GPIO is only available on the Raspberry Pi
and must not be loaded on other machines (e.g. the developers osx system).

The GPIO numbering_mode GPIO.BOARD is used.

"""
from __future__ import print_function
import logging
from telewall.core.config import Config
from telewall.core.model import Persistence, CallState, AsteriskPersistence, TelephoneNumber
from telewall.core.util import get_cisco_spa232D_ip
from telewall.ui.button import Button
from telewall.ui.color_led import ColorLed
from telewall.ui.display import Display
from telewall.ui.led import Led

LOG = logging.getLogger(__name__)


class Animation(object):
    """ abstract class to structure animation objects     """

    def __init__(self):
        pass

    def once(self):
        """ called once, the implementation run the animations.        """
        pass

    def repeat(self, interruptible=None):
        """ called many times, the implementation run the animations.
        :param interruptible: the instance of Interruptible (optional)
        :return: True to stop the animation, False to continue the animation
        """
        return True


class AnimationOff(Animation):
    """ disable led    """

    def once(self):
        main_led.set(0, 0, 0)


class BlockButtonPressed(Animation):
    """ animation when block button is pressed     """

    def once(self, interruptible=None):
        button_led.set_wait(100, 0.5)



class CallUp(Animation):
    """ animation when call is connected    """

    def repeat(self, interruptible=None):
        main_led.set(0, 50, 0)


class NowBlocked(Animation):
    """ call when call has been blocked     """

    def once(self):
        main_led.set_wait(red=50, sec=5)


class Startup(Animation):
    """ funny animcation on startup     """

    def repeat(self, interruptible=None):
        main_led.set_wait(100, 0, 0, 1, interruptible)
        main_led.set_wait(0, 100, 0, 1, interruptible)
        main_led.set_wait(0, 0, 100, 1, interruptible)
        return True


class StartupButton(Animation):
    """ basic test for the button led startup     """

    def repeat(self, interruptible=None):
        for value in range(0, 100, 5):
            button_led.set_wait(value, 0.04, interruptible)
        for value in range(100, 0, -5):
            button_led.set_wait(value, 0.04, interruptible)
        return True


class NoAction(Animation):
    """ there is no action that could be performed     """

    def once(self):
        main_led.set_wait(blue=50, sec=1)


class CallRefusing(Animation):
    """ a call is beeing refused (pulsing red led)     """

    def repeat(self, interruptible=None):
        for i in range(5, 25, 5):
            main_led.set_wait(red=i, sec=0.08, interruptible=interruptible)

        for i in range(25, 5, -5):
            main_led.set_wait(red=i, sec=0.08, interruptible=interruptible)


def show_callerid_blocked(number):
    """ show the caller id on the display and signal the led.
    :param number: the TelephoneNumber instance of the blocked caller
    """
    main_led.queue(NowBlocked())
    display.show(15, 'Blockiert:', number.local)


def _block_caller(caller_phone_number):
    """ block a caller when pressing the button.
    :param caller_phone_number: the TelephoneNumber to block
    """
    with Persistence(Config.TELEWALL_DATABASE_PATH) as p:
        if not p.is_blocked(caller_phone_number):
            p.block(caller_phone_number, '', 'button')


def on_button_press():
    """ Callback function the call on button press. try to block a caller.  """

    with AsteriskPersistence(Config.ASTERISK_DATABASE_PATH) as asterisk:
        asterisk_anruf = asterisk.get_last_cdr_callerid()
        LOG.info('last caller in asterisk : %s', asterisk_anruf)

    call_state = CallState.instance()
    if call_state.is_ringing or call_state.is_connected:
        _block_caller(call_state.caller)
        show_callerid_blocked(call_state.caller)
        call_state.refuse_if_connected()

    elif asterisk_anruf:
        caller_phone_number = TelephoneNumber(asterisk_anruf.src)
        _block_caller(caller_phone_number)
        show_callerid_blocked(caller_phone_number)
        call_state.refuse_if_connected()

    else:
        LOG.info('nothing to block')
        main_led.queue(NoAction())
        display.show(8, 'Keine Anrufe', 'innert 15min.', centered=True)


def on_standby():
    """ update display on standby (nothing else to display)    """
    ip = get_cisco_spa232D_ip()
    if ip:
        display.show(90, 'Verwalten unter:', ip, centered=True)
    else:
        display.show(2, 'Netzwerk-Fehler.', 'Error IP01', ip)


def on_call_state_change(event, call_state):
    """ called when the CallState has been updated. updates the display and led.
    :param event: event that caused the update
    :param call_state: the CallState instance
    """
    if call_state.caller:
        caller_number = call_state.caller.local
        caller_name = call_state.caller.name
    else:
        caller_number = ''
        caller_name = ''
    LOG.info('ui call state: %s (%s, %s)', call_state.current_state, caller_number, caller_name)

    if call_state.is_connected:
        main_led.queue(CallUp())

    elif call_state.is_disconnected:
        main_led.queue(AnimationOff())
        display.show(15, 'Anruf beendet:', caller_number)

    elif call_state.is_refusing:
        main_led.queue(CallRefusing())

        # use name from blocked callers table or the phonebook name, if available
        blocked_caller_name = None
        if call_state.caller:
            with Persistence(Config.TELEWALL_DATABASE_PATH) as p:
                blocked_caller = p.find(call_state.caller)
                if blocked_caller:
                    blocked_caller_name = blocked_caller.comment

        if blocked_caller_name:
            name = blocked_caller_name
        elif caller_name:
            name = caller_name
        else:
            name = ''
        LOG.debug('name of refused caller:%s (%s/%s)', name, blocked_caller_name, caller_name)
        display.show(15, 'abgewiesen:' + name, caller_number)

    elif call_state.is_ringing:
        main_led.queue(CallUp())
        if caller_name:
            display.show(15, caller_name, caller_number)
        else:
            display.show(15, 'Anruf von', caller_number)
    else:
        pass


# setup the components with the actual pins:
main_led = ColorLed(pin_red=33, pin_green=35, pin_blue=37)

button_led = Led(pin=29)

display = Display(pin_rs=10, pin_contrast=8, pin_rw=26, pin_e=12, pins_data=[16, 18, 22, 24])
display.set_standby_function(on_standby)

button = Button(pin=31)
button.add_listener(on_button_press)
button.add_listener(lambda: button_led.queue(BlockButtonPressed()))


def start():
    """  start running the ui. GPIO must only be loaded when it is stared, as the library is not available on the
         build computer.
    """
    from RPi import GPIO
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BOARD)  # use pin numbers as written on the board

    main_led.start()
    button_led.start()
    display.start()
    button.start()

    CallState.add_listener(on_call_state_change)

    main_led.queue(Startup())
    button_led.queue(StartupButton())
    display.show(10, 'Telewall')


def stop():
    """ stop the ui processes.     """
    from RPi import GPIO
    GPIO.cleanup()
    # the threads of the components are not stopped here. they are flagged as daemon and therefor are
    # destroyed on quit anyway.
