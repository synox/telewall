"""
GPIO: The GPIO modules are imported only with running the start method. GPIO is only available on the Raspberry Pi
and must not be loaded on other machines (e.g. the developers osx system).
"""

import logging
import threading
import time
from Queue import Queue

from telewall.core.util import sleep_until
from telewall.ui.interruptible import Interruptible

LOG = logging.getLogger(__name__)


class ColorLed(object):
    """ represents a physical color (RGB) LED.     """

    def __init__(self, pin_red, pin_green, pin_blue):
        """
        :param pin_red: GPIO pin for the red led
        :param pin_green: GPIO pin for the green led
        :param pin_blue: GPIO pin for the blue led
        """
        self.pin_red = pin_red
        self.pin_green = pin_green
        self.pin_blue = pin_blue

        self._queue = Queue()
        """ Queue of animations to process
        :type = Queue
        """

        self.red = None
        self.green = None
        self.blue = None

    def start(self):
        """ start the worker thread to handle animation         """
        self.setup()
        worker_thread = threading.Thread(target=self._run)
        worker_thread.daemon = True
        worker_thread.start()

    def _run(self):
        """ internal function the runs the endless loop to handle animations.        """
        while True:
            anim = self._queue.get(block=True)
            interruptible = Interruptible(lambda: not self._queue.empty())
            LOG.debug('running animation %s', anim.__class__.__name__)
            anim.once()  # 'once' animation is not interrupted.
            # repeat the 'repeat' animation until there is another animation or the animation is done.
            repeat_done = False
            while self._queue.empty() and not repeat_done:
                repeat_done = anim.repeat(interruptible)

            self.set_wait(0, 0, 0, 0.1)  # short pause between animations

    def setup(self):
        """ setup GPIO pins and start GPIO PWM.        """
        from RPi import GPIO
        GPIO.setup(self.pin_red, GPIO.OUT)
        GPIO.setup(self.pin_green, GPIO.OUT)
        GPIO.setup(self.pin_blue, GPIO.OUT)

        freq = 100  # Hz
        self.red = GPIO.PWM(self.pin_red, freq)
        self.green = GPIO.PWM(self.pin_green, freq)
        self.blue = GPIO.PWM(self.pin_blue, freq)

        # Initial duty cycle is 100, that means 'off'
        self.green.start(100)
        self.red.start(100)
        self.blue.start(100)

    def queue(self, animation):
        """ add an animation to the queue. The animation is run after the current animation has finished.
        :param animation: an instance of Animation
        :type animation: Animation
        """
        self._queue.put(animation)

    def set(self, red, green, blue):
        """
        set led color (used only by Animation implementations)
        :param red: value for red (0 is off, 100 is full)
        :param green:value for green (0 is off, 100 is full)
        :param blue:value for blue (0 is off, 100 is full)
        :return: None
        """
        # inverting the values, so that in the API 0 is off, 100 is full.
        self.red.ChangeDutyCycle(100 - red)
        self.green.ChangeDutyCycle(100 - green)
        self.blue.ChangeDutyCycle(100 - blue)

    def set_wait(self, red=0, green=0, blue=0, sec=1, interruptible=None):
        """
        enable led for X seconds, then disable. (used only by Animation implementations)
        :param red: value for red (0 is off, 100 is full)
        :param green:value for green (0 is off, 100 is full)
        :param blue:value for blue (0 is off, 100 is full)
        :param sec: how many seconds to wait
        :type sec: float
        :param interruptible: a function the returns True if the animation should be stopped
        """

        self.set(red, green, blue)
        if interruptible:
            sleep_until(lambda: interruptible.is_interrupted(), sec)
        else:
            time.sleep(sec)
        self.set(0, 0, 0)
