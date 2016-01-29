""" Tests the script that imports the blacklist from ktipp.
"""
import logging
import os
import nose
from nose.tools import assert_equals
from telewall.application import import_blacklist
from telewall.core.testutils import create_temp_telewall_db
from telewall.core.model import Persistence

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger(__name__)
LOG.setLevel(logging.DEBUG)

# Change this switch to True to enable online testing.
run_online_tests = False


# the following test works only when online:
def test_load_from_ktipp_online():
    db_path  = create_temp_telewall_db(overwrite=True)
    importer = import_blacklist.ImportBlacklist(db_path)
    if run_online_tests:
        with Persistence(db_path) as p:
            assert_equals(0, len(p.get_all_blocked()))
            importer.load_from_ktipp()
            assert_equals(3170, len(p.get_all_blocked()))


def test_import_local_csv():
    db_path  = create_temp_telewall_db(overwrite=True)
    importer = import_blacklist.ImportBlacklist(db_path)

    with Persistence(db_path) as p:
        assert_equals(0, len(p.get_all_blocked()))

    absolute_filename = os.path.join(os.path.dirname(__file__), 'data', 'blacklist_import_short.csv')

    importer.load_csv(absolute_filename, 'ktipp')
    with Persistence(db_path) as p:
        assert_equals(13, len(p.get_all_blocked()))


def test_import_local_csv_twice():
    db_path  = create_temp_telewall_db(overwrite=True)
    importer = import_blacklist.ImportBlacklist(db_path)

    with Persistence(db_path) as p:
        assert_equals(0, len(p.get_all_blocked()))

    absolute_filename = os.path.join(os.path.dirname(__file__), 'data', 'blacklist_import_short.csv')

    importer.load_csv(absolute_filename, 'ktipp')
    with Persistence(db_path) as p:
        assert_equals(13, len(p.get_all_blocked()))

    importer.load_csv(absolute_filename, 'ktipp')
    with Persistence(db_path) as p:
        assert_equals(13, len(p.get_all_blocked()))


if __name__ == '__main__':
    nose.runmodule()
