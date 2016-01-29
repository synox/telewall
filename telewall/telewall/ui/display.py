"""
GPIO: The GPIO modules are imported only with running the start method. GPIO is only available on the Raspberry Pi
and must not be loaded on other machines (e.g. the developers osx system).

"""
import logging
import threading
import time
from Queue import Queue
from math import floor

from telewall.core.util import sleep_until

LOG = logging.getLogger(__name__)


class Display(object):
    """ Represents a physical character dispaly     """
    COLUMNS = 16
    """ configure the number of columns of the display """
    ROWS = 2
    """ configure the number of rows of the display """
    SCROLL_STEP_DURATION = 0.3  # sec
    """ while scrolling text, how long to show one frame  """

    def __init__(self, pin_rs, pin_contrast, pin_rw, pin_e, pins_data):
        """ See the display manual for the meaning of the pins.
        :param pin_rs: the GPIO pin for RS
        :param pin_contrast: the GPIO pin for contrast
        :param pin_rw: the GPIO pin for RW
        :param pin_e: the GPIO pin for E
        :param pins_data: the GPIO data pins (array with 4 integers)
        :return:
        """
        self.pins_data = pins_data
        self.pin_e = pin_e
        self.pin_rw = pin_rw
        self.pin_contrast = pin_contrast
        self.pin_rs = pin_rs

        self._queue = Queue()

        self.contrast = None
        self.lcd = None
        self.standby_function = None

    def start(self):
        """ start the worker thread to handle animation         """
        self.setup()

        worker_thread = threading.Thread(target=self._run)
        worker_thread.daemon = True
        worker_thread.start()

        LOG.debug('started display')

    def setup(self):
        """ setup GPIO pins and start GPIO PWM
        """
        from RPLCD import CharLCD
        from RPi import GPIO as GPIO

        GPIO.setup(self.pin_contrast, GPIO.OUT)
        self.lcd = CharLCD(pin_rs=self.pin_rs, pin_rw=self.pin_rw, pin_e=self.pin_e, pins_data=self.pins_data,
                           numbering_mode=GPIO.BOARD, cols=Display.COLUMNS, rows=Display.ROWS, dotsize=8)
        self.lcd.cursor_pos = (0, 0)

        # the contrast needs a curtain  current, found value by try and error
        self.contrast = GPIO.PWM(self.pin_contrast, 1000)
        self.contrast.start(40)

    def _run(self):
        """ internal function that runs endless loop  """
        while True:
            # get message from the queue, wait if there is no message
            msg = self._queue.get(block=True)
            # set the cursor to row 0, column 0
            self.lcd.home()
            start_time = time.time()
            while self._queue.empty() and (time.time() - start_time) < msg.duration:
                # the display is always filled with spaces. This avoids the requirement to call clear() and this
                # avoids flickering.
                self.lcd.write_string(msg.get_line1())
                self.lcd.write_string(msg.get_line2())
                # scroll the text one step
                msg.scroll()
                # sleep to keep the scrolling text for a moment (but stop if there is another message waiting)
                sleep_until(lambda: not self._queue.empty(), Display.SCROLL_STEP_DURATION)
            # if the queue is empty and there is a standby function: run it.
            if self._queue.empty():
                if self.standby_function:
                    self.standby_function()

    def set_standby_function(self, func):
        """ defines a function that should be run when there is nothing else to display.
        :param func: the function that will be called
        """
        self.standby_function = func

    def show(self, sec, line1, line2='', scroll=True, centered=True):
        """ show the given text on the display. The request is queued until the previous request has finished.
        :param sec: how many seconds to display the text for
        :param line1: text for first line
        :param line2: text for second lind
        :param scroll: True  to enable scrolling
        :param centered: True to center the text (looks nice!)
        """
        msg = Display.Message(duration=sec, scroll=scroll,
                              line1=Display.Line(line1, scroll=scroll, centered=centered),
                              line2=Display.Line(line2, scroll=scroll, centered=centered),
                              )
        self._queue.put(msg)

    class Line(object):
        """ Represents one line on the display . It has its own scroll state.        """
        SCROLL_BREAK = ' - '
        """ symbols to show between text when scrolling """

        def __init__(self, text, scroll=False, centered=False):
            """
            :param text: text to scroll
            :param scroll: True to enable scrolling
            :param centered: True to center the text (looks nice!)
            """
            self.text = Display.Line._clean(text)

            if centered:
                spaces = Display.COLUMNS - len(self.text)
                if spaces > 0:
                    leftspaces = int(spaces / 2)
                    rightspaces = int(spaces - leftspaces)
                    self.text = ' ' * leftspaces + self.text + ' ' * rightspaces
            # only scroll if the text is too long
            self.scroll_enabled = scroll and len(self.text) > Display.COLUMNS

            # current scroll position
            self.scroll_offset = 0

        def get(self):
            """ the text that should be displayed in the current scrolling position             """
            if self.scroll_enabled:
                long_line = self.text + Display.Line.SCROLL_BREAK + self.text
                result = long_line[self.scroll_offset:Display.COLUMNS + self.scroll_offset]
            else:
                result = self.text[0:Display.COLUMNS]
            return result.ljust(Display.COLUMNS)

        def scroll(self):
            """ scroll one step (if enabled)           """
            if self.scroll_enabled:
                self.scroll_offset += 1
                if self.scroll_offset == len(self.text) + len(Display.Line.SCROLL_BREAK):
                    self.scroll_offset = 0

        @staticmethod
        def _clean(string):
            """ internal helper method to strip newlines from the string. Newlines are shown as empty character,
            which is not what we want.
            :param string: string to clean
            :return: cleaned string
            """
            return string.replace('\n', '').strip()

        def __str__(self):
            """
            :return: text representation for debugging
            """
            return '%s' % self.text

    class Message:
        """ represents a message to display, may contain 2 lines.        """

        def __init__(self, duration, line1, line2, scroll=True):
            """
            :param duration: how many seconds to display the text for
            :param line1: text for first line
            :param line2: text for second lind
            :param scroll: True  to enable scrolling
            """
            self.line1 = line1
            self.line2 = line2
            self.duration = duration

        def scroll(self):
            """ scroll one step (if enabled)           """
            self.line1.scroll()
            self.line2.scroll()

        def get_line1(self):
            """
            :return: the text that should be displayed in line 1 in the current scrolling position
            """
            return self.line1.get()

        def get_line2(self):
            """
            :return: the text that should be displayed in line 2 in the current scrolling position
            """
            return self.line2.get()

        def __str__(self):
            """
            :return: text representation for debugging
            """
            return '%s/%s(%s sec)' % (self.line1, self.line2, self.duration)
