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


class Led(object):
    """ represents a physical simple  LED.     """

    def __init__(self, pin):
        """
        :param pin: GPIO pin to use
        """

        self.pin = pin
        self._queue = Queue()
        """ Queue of animations to process
        :type = Queue
        """

        self.led = None

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

            self.set_wait(0, 0.1)  # short pause between animations

    def setup(self):
        """ setup GPIO pins and start GPIO PWM.        """
        from RPi import GPIO
        GPIO.setup(self.pin, GPIO.OUT)

        freq = 100  # Hz
        self.led = GPIO.PWM(self.pin, freq)

        # Initial duty cycle is 0, that means 'off'
        self.led.start(0)

    def queue(self, animation):
        """ add an animation to the queue. The animation is run after the current animation has finished.
        :param animation: an instance of Animation
        :type animation: Animation
        """
        self._queue.put(animation)

    def set(self, value):
        """
        set led value
        :param value: value for led (0 is off, 100 is full)
        """
        self.led.ChangeDutyCycle(value)

    def set_wait(self, value=0, sec=1, interruptible=None):
        """
        enable led for X seconds, then disable.
        :param value: value for led (0 is off, 100 is full)
        :param sec: how many seconds to enable
        :type sec: float
        :param interruptible: a function the returns True if the animation should be stopped
        """
        self.set(value)
        if interruptible:
            sleep_until(lambda: interruptible.is_interrupted(), sec)
        else:
            time.sleep(sec)
        self.set(0)
