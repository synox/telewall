""" This module contains events and states which implement the asterisk applications. An event is a transition from
one state to another state. Before reading the code read the state diagrams in the documentation.

Some obvious parameters like 'channel' are not documented as docstring, instead see the asterisk ARI documentation:
https://wiki.asterisk.org/wiki/display/AST/Asterisk+12+REST+Data+Models
https://wiki.asterisk.org/wiki/display/AST/Asterisk+12+ARI

Docstring for overwritten methods can be found in the parent class.


The state machine design pattern is inspired by:
https://wiki.asterisk.org/wiki/display/AST/ARI+and+Media%3A+Part+1+-+Recording
"""


class Constants:
    CUSTOM_ANNOUNCEMENT_RECORDING = 'telewall-custom-message'  # stored in '/var/spool/asterisk/recording/'
    DEFAULT_ANNOUNCEMENT = 'sound:/telewall/sounds/de/announcement'
