""" cleans up old database entries.
"""

from telewall.core.model import AsteriskPersistence
from telewall.core.config import Config

if __name__ == '__main__':
    print('cleanup started.')
    with AsteriskPersistence(Config.ASTERISK_DATABASE_PATH) as p:
        p.delete_old_call_records()
    print('cleanup done.')
