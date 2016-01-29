import datetime
import logging
import re
from math import ceil

import phonenumbers
import sqlalchemy
from sqlalchemy import Column, String, DateTime, Integer
from sqlalchemy import or_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from statu import acts_as_state_machine, State, Event, after

from telewall.core.config import Config

Base = declarative_base()

LOG = logging.getLogger(__name__)


class Pagination(object):
    """ Helper class for pagination of html pages.     """

    def __init__(self, page, per_page, total_count):
        """
        :param page: current page number
        :param per_page: number of entries per page
        :param total_count: total number of entries
        :return:
        """
        self.page = page
        self.per_page = per_page
        self.total_count = total_count

    @property
    def pages(self):
        """
        :return: total number of pages
        """
        return int(ceil(self.total_count / float(self.per_page)))

    @property
    def has_prev(self):
        """
        :return: True if there are previous pages.
        """
        return self.page > 1

    @property
    def has_next(self):
        """
        :return: True if there are more pages.
        """
        return self.page < self.pages

    def iter_pages(self, left_edge=2, left_current=2,
                   right_current=5, right_edge=2):
        """ iterates the pages.

        The parameters allow to configure the how many page numbers to show. Examples:
         - 1 2 3 ... 8 *9* 10 11 ... 25 26 (left_edge=3, left_current=1, right_current=2 right_edge=2)
         - 1 2 ... 7 8 *9* 10 11 ... 26    (left_edge=2, left_current=2, right_current=2 right_edge=1)

        :param left_edge: number of page numbers to show on the left end
        :param left_current:  numnber of pages to show on the left of the current page
        :param right_current: numnber of pages to show on the right of the current page
        :param right_edge:  number of page numbers to show on the right end
        :return:
        """
        last = 0
        for num in xrange(1, self.pages + 1):
            if num <= left_edge or \
                    (self.page - left_current - 1 < num < self.page + right_current) or \
                            num > self.pages - right_edge:
                if last + 1 != num:
                    yield None
                yield num
                last = num


class TelephoneNumber(object):
    """ Parses telephone numbers and stores them in a standardized format. Each instance contains the telephone
    number as an international (e164) and a national representation.

    The parser is as simple as possible and customized for switzerland. It does however handle international country
    codes.

    The telefphone number can be validated against the phonenumbers library
    (https://github.com/daviddrysdale/python-phonenumbers). It can detect invalid country codes and invalid phone
    number length. However is slow, as it requires 10x  more processing time compared to the simple parsing. Validation
    is only activated when the constructor is called with validate=True

    the instance variables are:
    - self.full:  phone number in the international e164 standard (+4131...)
    - self.local: phone number in the national format for swiss numbers, or same as self.full for forgein numbers.
                  (031... or +49...)
    """
    DEFAULT_COUNTRY_CODE = 41
    """ defines how to handle national phone numbers with leading 0"""

    def __init__(self, number_string, name=None, validate=False):
        """
        :param number_string: a phone number in national or international format (031... or +4131... or +49...)
        :param name: the name of the owner of the phone number (optional)
        :param validate: True enables phone number validation (optional, slow)
        :return:
        """
        self.name = name
        self.is_valid = True

        if validate:
            # validation takes 10 times longer to process
            try:
                parsed = phonenumbers.parse(number_string, 'CH')
                self.is_valid = phonenumbers.is_possible_number(parsed)
                # phonenumbers.is_valid_number() is not used here, as it might be too limiting for this application.
            except phonenumbers.NumberParseException as e:
                LOG.info("the number '%s' is invalid. cause: %s", number_string, e)
                self.is_valid = False

        self._quickparse(number_string)

    def _quickparse(self, number_string):
        """ parses the phone number.
        :param number_string:  a phone number in national or international format (031... or +4131... or +49...)
        """
        # remove whitespace
        nospace = re.sub(r'\s', "", number_string)

        if re.match(r'^0[1-9][\s0-9]+$', nospace):
            # national number starting with 0 and then a non-zero number
            self.full = re.sub(r'^0', '+%d' % TelephoneNumber.DEFAULT_COUNTRY_CODE, nospace)
            self.local = nospace
        elif re.match(r'^([+]|00)%d' % TelephoneNumber.DEFAULT_COUNTRY_CODE, nospace):
            # national number in international format starting with +41 or 0041
            self.full = nospace
            self.local = re.sub(r'^([+]|00)%d' % TelephoneNumber.DEFAULT_COUNTRY_CODE, '0', nospace)
        else:
            # international number, replace leading 00 with +
            self.full = re.sub(r'^00', '+', nospace)
            self.local = self.full

    def __str__(self):
        return self.full


@acts_as_state_machine
class CallState:
    """ This state machine holds the state of calls. It is triggered by by asterisk events and
    notfies subscribed listeners.

    The permit(), refuse(), answer() and hangup() represent the events that can be called. The boolean properties
    is_disconnected, is_refusing, is_ringing and is connected contain True if the given state is activ.
    These method are created by the @acts_as_state_machine annotation at runtime.
    See https://github.com/DisruptiveLabs/statu
    """

    def __init__(self):
        self.caller = None

    listeners = []
    INSTANCE = None

    @classmethod
    def instance(cls):
        if not CallState.INSTANCE:
            CallState.INSTANCE = CallState()
        return CallState.INSTANCE

    @classmethod
    def add_listener(cls, listener):
        cls.listeners.append(listener)
        LOG.debug('CallState listeners: %s', cls.listeners)

    @classmethod
    def remove_listener(cls, listener):
        cls.listeners.remove(listener)
        LOG.debug('CallState listeners after remove: %s', cls.listeners)

    def set_caller(self, phone_number):
        """set the callers telephone number
        :param phone_number: the telefone number of the caller
        """
        self.caller = phone_number

    # states:
    disconnected = State(initial=True)
    refusing = State()
    ringing = State()
    connected = State()

    # transition methods:
    permit = Event(from_states=disconnected, to_state=ringing)
    refuse = Event(from_states=(disconnected, connected), to_state=refusing)
    answer = Event(from_states=ringing, to_state=connected)
    hangup = Event(from_states=(connected, ringing, refusing, disconnected), to_state=disconnected)

    def get_current_state(self):
        """
        :return: the current state name as a string
        :rtype: string
        """
        return self.current_state

    @after('hangup')
    def notify_hangup(self):
        """  process Hangup event  """
        self._notify('hangup', CallState.listeners)
        # reset variables that are valid in disconnected state
        self.set_caller(None)

    @after('answer')
    def notify_answer(self):
        """ process events, call listeners       """
        self._notify('answer', CallState.listeners)

    @after('permit')
    def notify_permit(self):
        """ process events, call listeners       """
        self._notify('permit', CallState.listeners)

    @after('refuse')
    def notify_refuse(self):
        """ process events, call listeners       """
        self._notify('refuse', CallState.listeners)

    def _notify(self, event, listeners):
        LOG.debug('On %s changed to state %s. Notify Listeners %s', event, self.get_current_state(), listeners)
        for listener in listeners:
            listener(event, self)

    def refuse_if_connected(self):
        """ change to 'refuse' state in case the connected state is active.
        """
        if self.is_connected:
            self.refuse()


class BlockedCaller(Base):
    """ Database entity for a blocked caller     """
    __tablename__ = 'blocked_callers'

    telephone_number = Column(String, primary_key=True)
    comment = Column(String)
    source = Column(String)
    created = Column(DateTime, default=datetime.datetime.now)

    def __repr__(self):
        """
        :return: string representation for debugging
        """
        return "<BlockedCaller(telephone_number='%s', comment='%s', source='%s')>" % (
            self.telephone_number, self.comment, self.source)

    def national_telephone_number(self):
        """
        :return: returns the national part of the phone number
        """
        return TelephoneNumber(self.telephone_number).local


class CallRecord(Base):
    """ Database entry for on call record in the call history     """
    __tablename__ = 'call_history'

    AcctId = Column(Integer, primary_key=True)
    src = Column(String)
    start = Column(DateTime)
    end = Column(DateTime)
    dcontext = Column(String)
    clid = Column(String)
    channel = Column(String)
    dstchannel = Column(String)
    lastapp = Column(String)
    lastdata = Column(String)
    duration = Column(Integer)
    billsec = Column(Integer)
    disposition = Column(String)
    telewall_state = Column(String)
    blocked = Column(Integer)

    def __repr__(self):
        """
        :return: string representation for debugging
        """
        return "<CallRecord(src='%s',  end='%s')>" % (
            self.src, self.end)

    def _parse_number(self):
        """ internal method to parse the phone number. It is parsed only once.         """
        if not hasattr(self, 'phone_number'):
            self.phone_number = TelephoneNumber(self.src)

    def local_number(self):
        """
        :return: the local presentation of the phone number
        """
        self._parse_number()
        return self.phone_number.local

    def full_number(self):
        """
        :return: international format of the phone number
        """
        self._parse_number()
        return self.phone_number.full

    def is_blocked(self):
        """
        :return: True if the caller was blocked in that call
        """
        return self.blocked == True

    def is_missed(self):
        """
        :return: True if this is a missed call
        """
        return self.telewall_state in ['no_answer', '']

    def is_answered(self):
        """
        :return: True if the call was answered
        """
        return self.telewall_state == 'answered'

    def is_busy(self):
        """
        :return: True if the phone was busy and therefor refused with 'busy'
        """
        return self.telewall_state == 'busy'

    def format_billsec(self):
        """
        :return: human readable string repersentation of the call duration.
        """
        if self.billsec < 150:
            return '%i sek.' % self.billsec
        elif self.billsec < 3600 * 2:
            return '%i min.' % (self.billsec / 60)
        else:
            return '%i h.' % (self.billsec / 3600)


class Persistence(object):
    """ Persistence class should be used using the 'with' keyword. The resource is automatically closed after
     running the block. exmaple:

    with Persistence(Config.TELEWALL_DATABASE_PATH) as p:
        if not p.is_blocked(caller_phone_number):
            p.block(caller_phone_number, '', 'button')

    """

    def __init__(self, db_filename):
        """ is the constructor for th 'with' block
        :param db_filename: Path to Database
        """
        self.engine = sqlalchemy.create_engine('sqlite:///%s' % db_filename, echo=False)
        self.sessionmaker = sessionmaker(bind=self.engine)

    def __enter__(self):
        """ this is run when the 'with' block is entered. It connects to the database.
        """
        self.session = self.sessionmaker(expire_on_commit=False)
        # Expire on commit is false. This ensures that the entities from the database can still be used after commiting
        # the session and closing the connection.
        return self

    def __exit__(self, type, value, traceback):
        """ this is run at the end of the 'with' block
        :param type: (not used)
        :param value: (not used)
        :param traceback: (not used)
        :return:
        """
        self.session.commit()
        self.session.close()

    def persist(self, object):
        """ persist the given object
        :param object: object to persist
        """
        self.session.add(object)

    def is_blocked(self, phone_number):
        """
        checks if the number is blocked
        :param phone_number: TelephoneNumber object
        :return: True if number is blocked
        """
        assert isinstance(phone_number, TelephoneNumber)
        return self.session.query(BlockedCaller).filter_by(telephone_number=phone_number.full).count() > 0

    def get_blocked_callers_count(self):
        """
        Count the number of blocked callers.

        :return: the number of blocked callers.
        """
        return self.session.query(BlockedCaller).count()

    def get_all_blocked(self):
        """ Return the list of all blocked entries. """
        return self.session.query(BlockedCaller).order_by(BlockedCaller.created.desc()).all()

    def get_blocked_callers(self, page=None, per_page=None):
        """ Return the list of all blocked callers
        :param page: page for paging (optional)
        :param per_page: how many entries per page for paging (optional)
        :return: list of blocked callers
        """
        q = self.session.query(BlockedCaller)
        if per_page:
            q = q.limit(per_page)
        if page:
            # Page 1 means offset 0, therefor substract 1
            q = q.offset((page - 1) * per_page)
        return q.all()

    def load_schema(self, filename):
        """ load the give schema into the databse
        :param filename: sql file to load
        """
        with open(filename, 'r') as f:
            sql = f.read()

        conn = self.session.connection().connection
        conn.executescript(sql)

    def block(self, phone_number, comment='', source_name=''):
        """ Block the number
        :param phone_number: TelephoneNumber object
        :param comment: comment (optional)
        :param source_name: source (optional)
        :return: BlockedCaller entity
        :rtype: BlockedCaller
        """
        assert isinstance(phone_number, TelephoneNumber)
        entity = BlockedCaller(telephone_number=phone_number.full, comment=comment, source=source_name)
        self.persist(entity)
        self.session.flush()
        return entity

    def block_list(self, list_of_entries):
        """  block all the given entries
        :param list_of_entries: list of  BlockedCaller objects
        """
        # doing plain sql to increase performance
        conn = self.session.connection().connection
        c = conn.cursor()
        rows = []
        for entity in list_of_entries:
            row = (entity.telephone_number, entity.comment, entity.source,)
            rows.append(row)
        c.executemany('INSERT OR IGNORE INTO blocked_callers (telephone_number, comment, source) VALUES (?,?,?)', rows)
        conn.commit()
        self.session.flush()

    def unblock(self, phone_number):
        """ Whitelist the number.
        :param phone_number: TelephoneNumber object
        """
        assert isinstance(phone_number, TelephoneNumber)
        self.session.query(BlockedCaller).filter(BlockedCaller.telephone_number == phone_number.full).delete(
                synchronize_session=False)

    def find(self, phone_number):
        """ return the blocked caller.
        :param phone_number: TelephoneNumber object
        :return: BlockedCaller instance
        :rtype: BlockedCaller
        """
        assert isinstance(phone_number, TelephoneNumber)
        return self.session.query(BlockedCaller).filter(
                BlockedCaller.telephone_number == phone_number.full).one_or_none()


class AsteriskPersistence(object):
    """ Persistence class for Asterisk should be used using the 'with' keyword. The resource is automatically closed after
     running the block. exmaple:

    with AsteriskPersistence(Config.ASTERISK_DATABASE_PATH) as asterisk:
        asterisk_anruf = asterisk.get_last_cdr_callerid()

    """

    def __init__(self, asterisk_db_filename, print_sql=False):
        """ is the constructor for th 'with' block
        :param asterisk_db_filename: Path to Database
        :param print_sql: True to print sql to stdout
        """
        engine = sqlalchemy.create_engine('sqlite:///%s' % asterisk_db_filename, echo=print_sql)
        self.sessionmaker = sessionmaker(bind=engine)

    def __enter__(self):
        """ this is run when the 'with' block is entered. It connects to the database.
        """
        self.session = self.sessionmaker(expire_on_commit=False)
        return self

    def __exit__(self, type, value, traceback):
        """ this is run at the end of the 'with' block
        :param type: (not used)
        :param value: (not used)
        :param traceback: (not used)
        :return:
        """
        self.session.commit()
        self.session.close()

    def persist(self, object):
        """ persist the given object
        :param object: object to persist
        """
        self.session.add(object)
        self.session.flush()

    def get_last_cdr_callerid(self, after_time=None):
        """ Return the last caller ID that was recorded by asterisk in the last 15 minutes, or None.
        :param after_time: find calls after the given date (default: now-15min)
        :return: Anruf
        """

        if after_time is None:
            after_time = datetime.datetime.now() - datetime.timedelta(minutes=15)

        result = self.session.query(CallRecord).from_statement(
                sqlalchemy.text("""SELECT *
                    FROM call_history
                    WHERE dcontext ='incoming'
                    AND end > :endDate
                    ORDER BY end DESC
                    LIMIT 1""")).params(endDate=after_time).all()

        if result:
            return result[0]
        else:
            return None

    def get_call_history_count(self):
        """
        :return: number of entries in the call history
        """
        return self.session.query(CallRecord).count()

    def get_call_history(self, phone_number=None, page=None, per_page=None):
        """ return the call history, allows paging
        :param phone_number: phone number to filtet for (optional)
        :param page: current page (optional)
        :param per_page: number of entries per page (optional)
        :return: call history
        """
        filter = (CallRecord.dcontext == 'incoming',)
        if phone_number:
            filter = (CallRecord.dcontext == 'incoming',
                      or_(CallRecord.src == phone_number.local, CallRecord.src == phone_number.full))

        q = self.session.query(CallRecord).filter(*filter).order_by(CallRecord.end.desc())

        if per_page:
            q = q.limit(per_page)
        if page:
            # Page 1 means offset 0, therefor substract 1
            q = q.offset((page - 1) * per_page)
        return q.all()

    def delete_old_call_records(self):
        """ remove old call records from the call history
        """
        delete_before = datetime.datetime.now() - datetime.timedelta(days=Config.CALL_HISTORY_KEEP_DAYS)
        self.session.query(CallRecord).filter(CallRecord.end < delete_before).delete(synchronize_session=False)


    def load_schema(self, filename):
        """ load the give schema into the databse
        :param filename: sql file to load
        """
        with open(filename, 'r') as f:
            sql = f.read()

        conn = self.session.connection().connection
        conn.executescript(sql)
