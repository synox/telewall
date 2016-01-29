"""
GPIO: The GPIO modules are imported only with running the start method. GPIO is only available on the Raspberry Pi
and must not be loaded on other machines (e.g. the developers osx system).
"""
import logging

LOG = logging.getLogger(__name__)


class Button(object):
    """ Represents a physical pushable button. Event handles can be attached.     """

    def __init__(self, pin):
        """ Construct a button
        :param pin: the GPIO pin to use
        """
        self.pin = pin
        self.listeners = []
        """ fuctions to run on button push """

    def start(self):
        """ start the event handler        """
        self.setup()

    def setup(self):
        """ setup GPIO pins and install GPIO event handler    """
        from RPi import GPIO
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

        GPIO.add_event_detect(self.pin, GPIO.RISING,
                              callback=self._onrising, bouncetime=1000)

    def add_listener(self, func):
        """ add listener
        :param func: a function to call when to button was pushed
        """
        self.listeners.append(func)

    def _onrising(self, pin):
        """ interal function run when a button press was deteced.
        :param pin: the GPIO pin
        """
        from RPi import GPIO
        # check that it is actually pressed
        if GPIO.input(self.pin):
            for listener in self.listeners:
                listener()
