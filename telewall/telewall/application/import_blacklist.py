"""
Imports the blacklist from Ktipp.ch using the converted source http://trick77.com/tools/latest_cc_blacklist.txt

TODO:
It does not detect if a number is not blocked any more. Also it does not detect if a number was unblocked by the user.
This could be addressed in a future release.
"""
import csv
import logging
from six.moves.urllib.request import urlopen

from telewall.core.config import Config
from telewall.core.model import TelephoneNumber
from telewall.core.model import Persistence, BlockedCaller
import codecs

LOG = logging.getLogger(__name__)


class ImportBlacklist(object):
    """ import a list of blocked callers from the internet     """

    def __init__(self, db_path):
        """
        :param db_path: database to use
        """
        self.db_path = db_path

    def load_from_ktipp(self):
        """ load the blacklist from ktipp.        """
        url = 'http://trick77.com/tools/latest_cc_blacklist.txt'
        response = urlopen(url)
        self._import_csv(codecs.iterdecode(response, 'utf-8'),
                         source_name='ktipp')

    def load_csv(self, filename, source_name):
        """ load the given csv file
        :param filename: filename to the csv file
        :param source_name: source name to use for the blocked caller
        """
        with open(filename, 'r') as csvfile:
            self._import_csv(csvfile, source_name)

    def _import_csv(self, csvfile, source_name):
        """ internal method used to import a csv file.
        :param csvfile: filehandler to the csv file
        :param source_name: source name to use for the blocked caller
        :return:
        """
        reader = csv.reader(csvfile, delimiter=';', quotechar="'")

        # first collect all the blocked callers
        entries = []
        for row in reader:
            # the phone number is in the first row
            number = row[0]
            # there are some rows that should be ignored
            if not _is_comment(number) and not _is_invalid(number):
                phone_number = TelephoneNumber(number)
                if not phone_number.is_valid:
                    print('skipping the invalid number %s' % number)
                    continue

                try:
                    comment = row[1]
                    comment = comment.replace('Firma', '').strip()
                except Exception:
                    LOG.exception('can not parse comment')
                    comment = ''

                entity = BlockedCaller(telephone_number=phone_number.full,
                                       comment=comment,
                                       source=source_name)
                entries.append(entity)
        # then persist the whole list
        with Persistence(self.db_path) as p:
            p.block_list(entries)
            print('processed %d phone numbers.' % len(entries))


def _is_comment(row):
    """ check if the row is a comment.
    :param row: the string to check
    :return: True if the list is a comment and should be ignored
    """
    return row.startswith('#')


def _is_invalid(number):
    """ tests for invalid phone numbers.
    :param number: the number string to check
    :return: True if the number must be invalid. Else False.
    """
    return number.startswith('000')


if __name__ == '__main__':
    print('import from Ktipp started.')
    ImportBlacklist(Config.TELEWALL_DATABASE_PATH).load_from_ktipp()
