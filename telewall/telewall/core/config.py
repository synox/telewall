""" This module contains global configuration settings. """


class Config(object):
    """ enable debug and testing mode for web applications     """
    DEBUG = True
    TESTING = False

    # path to telewall and asterisk database
    TELEWALL_DATABASE_PATH = '/telewall/data/database.sqlite3'
    ASTERISK_DATABASE_PATH = '/var/log/asterisk/master.db'

    # how often to press # until the caller is blocked
    DTMF_DIGITS_TO_BLOCK_CALLER = 2

    # enable 'extra' features
    EASTEREGGS_ENABLED = True

    # username and password for ATA
    ATA_USERNAME = 'admin'
    ATA_PASSWORD = 'telewall'

    # how many days to keep call history records:
    CALL_HISTORY_KEEP_DAYS = 90
