import logging
import os
from telewall.core.model import AsteriskPersistence
from telewall.core.model import Persistence

LOG = logging.getLogger(__name__)

tempdir = os.path.join(os.path.dirname(__file__), '..', '..', 'data')


def create_temp_telewall_db(filename=None, sample_data=False, overwrite=False):
    """ setup a temporary sqlite database for testing, creates the  blocked_callers table.
    :param overwrite: True overwrites an existing database. False does not change an existing database.
    :param filename: (optonal) filename to use, defaults to a temporary filename
    :param sample_data: (optioal) True inserts some sample data
    :return: the filename of the file
    """

    if not filename:
        filename = os.path.join(tempdir, 'tmp-telewall.db')

    if os.path.exists(filename) and not overwrite:
        LOG.debug('using existing telewall database %s', filename)
        return filename

    if os.path.exists(filename):
        os.remove(filename)

    with Persistence(filename) as p:
        schema_filename = os.path.join(os.path.dirname(__file__), '..', '..', 'db-schema.sql')
        p.load_schema(schema_filename)

        if sample_data:
            schema_filename = os.path.join(os.path.dirname(__file__), '..', '..', 'db-sampledata.sql')
            p.load_schema(schema_filename)

    LOG.debug('created temp telewall database %s', filename)

    return filename


def create_temp_asterisk_db(filename=None, sample_data=False, overwrite=False):
    """ setup a temporary sqlite database for testing, creates the  call_history table.
    :param overwrite: True overwrites an existing database. False does not change an existing database.
    :param filename: (optonal) filename to use, defaults to a temporary filename
    :param sample_data: (optioal) True inserts some sample data
    :return: the filename of the file
    """

    if not filename:
        filename = os.path.join(tempdir, 'tmp-asterisk.db')

    if os.path.exists(filename) and not overwrite:
        LOG.debug('using existing asterisk database %s', filename)
        return filename

    if os.path.exists(filename):
        os.remove(filename)

    with AsteriskPersistence(filename) as p:
        schema_filename = os.path.join(os.path.dirname(__file__), '..', '..', 'db-schema-asterisk.sql')
        p.load_schema(schema_filename)

        if sample_data:
            schema_filename = os.path.join(os.path.dirname(__file__), '..', '../', 'db-sampledata-asterisk.sql')
            p.load_schema(schema_filename)

    LOG.debug('created temp asterisk database %s', filename)

    return filename


def setup_testdbs(sample_data=False):
    """ create temporary databases and return the filenames as a tuple.
    :param sample_data: enable or disable sample data
    :return: tuple of database filenames (telewall_filename, asterisk_filename).
    """
    return create_temp_telewall_db(sample_data=sample_data), create_temp_asterisk_db(sample_data=sample_data)
