""" This modules provies reverse lookups to the phonebook of tel.search.ch.

Only reverse lookups are supported and it always returns the first result. If there is no result for a telephone number
it automatically accepts recommendations to search with an other number. This allowes to detect company numbers which
do not have every phone number in the phonebook.

The api is documented at http://tel.search.ch/api/help. You can easily apply for an API key, but it is not required
for the basic functions like reverse-lookup.
"""
import logging
from xml.etree import ElementTree
import requests
import timeout_decorator
from lru import lru_cache_function

LOG = logging.getLogger(__name__)

TIMEOUT_SEC = 3
""" Any request is canceled/timed out after X seconds """


def lookup(phone_number):
    """ runs a reverse lookup of the number in the phonebook.
    :param phone_number: the telephone number is used to run the query.
            if successful the name is populated into the object
    :return: a ReverseLookupResult instance
    :rtype: ReverseLookupResult
    """
    try:
        name, correction = _lookup(phone_number.full)
        if name:
            if phone_number:
                phone_number.name = name
            return ReverseLookupResult(name=name, success=True, is_corrected=False)

        if correction:
            name, correction = _lookup(correction)
            if name:
                if phone_number:
                    phone_number.name = '?' + name
                return ReverseLookupResult(name=name, success=True, is_corrected=True)

        return ReverseLookupResult(success=False)
    except timeout_decorator.TimeoutError:
        return ReverseLookupResult(success=False, timedout=True)


@lru_cache_function(max_size=16)
def _lookup(telephone_number):
    """ Internal function, runs a reverse lookup of the number in the phonebook.
    :param telephone_number:  the telephone number to search for
    :return: a tuple of name and correction, both can be None if nothing was found.
    """
    root = _query(telephone_number)
    if root is None:
        return None, None
    name = _find_name(root)
    correction = _find_correction(root)
    LOG.info('looked up %s -> name:%s', telephone_number, name)
    return name, correction


class ReverseLookupResult(object):
    """ Result object for the reverse lookup. It allowes to distinguish timeout, success and corrected results. """

    def __init__(self, name=None, success=True, is_corrected=False, timedout=False):
        """
        Create a Lookup result
        :param name: Resolved name if any (optional)
        :param success: True if the lookup was successful. Else False. (optional)
        :param is_corrected: True if the result is corrected. Else False. (optional)
        :param timedout: True if the request timed out (defaults to False9
        """
        self.name = name
        self.is_corrected = is_corrected
        self.success = success
        self.timedout = timedout

    def __str__(self):
        return 'name=%s, success=%s, timeout=%s, corrected=%s' % (
            self.name, self.success, self.timedout, self.is_corrected)


@timeout_decorator.timeout(TIMEOUT_SEC, use_signals=False)
def _query(telephone_number):
    """ Internal function to to query a number. Requests time out after X seconds.
    :param string telephone_number: the telephone number to search for
    :return: returns the root of the XML tree
    """
    url = 'http://tel.search.ch/api/?was=%s' % telephone_number
    try:
        response = requests.get(url)
        if 'Request limit exceeded.' in response.content:
            LOG.error('too many requests to phonebook, url=%s, response: %s', url, response.content)
            raise timeout_decorator.TimeoutError()

        assert response.status_code == 200
        xml = response.content
        LOG.debug('xml response: %s', xml)
        root = ElementTree.fromstring(xml)
        return root
    except Exception as e:
        LOG.exception('exception while parsing reverse lookup response for url %s', url)
        raise e


def _find_correction(root):
    """ extracts the corrected search term from XML tree.

    the correction tag looks like this:
        <openSearch:Query role="correction" searchTerms="032 321 61 **" totalResults="2" />



    :param root: the root of an XML tree
    :return: the extracted corrected search term, or None if none is found.
    """
    correction = root.find("./{http://a9.com/-/spec/opensearchrss/1.0/}Query[@role='correction']")
    # The expression "{http://a9.com/-/spec/opensearchrss/1.0/}Query" is the fully qualified name for the Tag "Query".

    if correction is not None:
        new_query = correction.attrib['searchTerms']
        LOG.info('found correction query: %s', new_query)
        return new_query

    else:
        # no query with role="correction" found. There is no correction.
        return None


def _find_name(root):
    """ Internal function to extract the name from the lookup result
    :param root:  the root of an XML tree
    :return: the extraced name, or None if none is found.
    """
    title_obj = root.find('./{http://www.w3.org/2005/Atom}entry/{http://www.w3.org/2005/Atom}title')
    if title_obj is not None:
        return title_obj.text
    else:
        return None
