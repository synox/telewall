# coding=utf8
""" Telewall web application to manage blocked callers.

This web application allowes the user to list the blocked callers and block new callers.
There is no authentication and no protection against Cross-Site Request Forgery (CSRF).
The Flask framework does however protect against XSS and Injections.

The configuration is read from the telewall.core.config.Config class and may be altered at runtime in the Flask
app object. example: app.config['TELEWALL_DATABASE_PATH'] = '/telewall/data/database.sqlite3'

"""
import locale
import logging
import re
from flask import Flask, render_template, redirect, url_for, flash, request, abort
from telewall.core.model import TelephoneNumber, Persistence, Pagination, AsteriskPersistence
from telewall.core.testutils import create_temp_telewall_db, create_temp_asterisk_db

# Import locale to format dates to swiss-german standards.
try:
    locale.setlocale(locale.LC_ALL, 'de_CH.utf8')
except:
    pass

# number of entries per page, used for paging.
ENTRIES_PER_PAGE = 25

app = Flask(__name__)
# import config from Config class
app.config.from_object('telewall.core.config.Config')

# enable global warn logging and create logger for telewall
logging.basicConfig(level=logging.WARN)
LOG = logging.getLogger(__name__)
LOG.setLevel(logging.DEBUG)


@app.route('/')
def root():
    """ Redirects to the call_history page.    """
    return redirect(url_for('call_history'))


@app.route('/call_history')
def call_history():
    """  Shows the call history.

    Note: SQL pagination is not used on the call history as it does not influence page loading performance.
    Therefor Javascript paging is used for paging.
    """
    with AsteriskPersistence(app.config['ASTERISK_DATABASE_PATH']) as p:
        call_history_chunk = p.get_call_history()

    # load the blocked callers in order to mark them in the view
    with Persistence(app.config['TELEWALL_DATABASE_PATH']) as p:
        blocked_callers = p.get_blocked_callers()

    # add blocked metadata to call history:
    blocked_map = dict([(blocked_caller.telephone_number, blocked_caller) for blocked_caller in blocked_callers])
    for call_record in call_history_chunk:
        if call_record.full_number() in blocked_map.keys():
            call_record.blocked_caller = True
        else:
            call_record.blocked_caller = False

    return render_template('call_history.html', call_history=call_history_chunk)


@app.route('/blocked_callers', defaults={'page': 1})
@app.route('/blocked_callers-page-<int:page>')
def blocked_callers(page):
    """ Shows a list of the blocked callers.
    :param page: page for paging
    """
    with Persistence(app.config['TELEWALL_DATABASE_PATH']) as p:
        count = p.get_blocked_callers_count()
        chunk = p.get_blocked_callers(page, ENTRIES_PER_PAGE)

        if not chunk and page != 1:
            return redirect(url_for('blocked_callers'))
        pagination = Pagination(page, ENTRIES_PER_PAGE, count)
        return render_template('blocked_callers.html', blocked_callers=chunk, pagination=pagination)


@app.route('/block_caller', methods=['POST', 'GET'])
def block_caller():
    """  Blocks a caller using a form.

    The GET requests shows the form.
    The POST requets tries to save the information. On success, the user is redirected.
    """
    if request.method == 'POST':
        telephone_number_str = request.form['telephone_number']
        comment = request.form.get('comment', '')
        next_page = request.form.get('next_page', 'blocked_callers')
        if _is_plausible_number(telephone_number_str):
            _block_number(telephone_number_str, comment)
            if next_page == 'status':
                return redirect(url_for('search_result', number=telephone_number_str))
            else:
                return redirect(url_for(next_page))
        else:
            flash(u'Die eingegebene Rufnummer ist ungültig. Bitte versuchen Sie es nochmal. ', 'warning')
            return render_template('block_caller.html', telephone_number=telephone_number_str, comment=comment)
    else:
        # GET Request
        return render_template('block_caller.html')


@app.route('/unblock_caller', methods=['POST', 'GET'])
def unblock_caller():
    """  Unblocks a caller using a form.

        The GET requests shows the form.
        The POST requets tries to save the information.
        On success, the user is redirected.
    """
    if request.method == 'POST':
        telephone_number_str = request.form['telephone_number']
        next_page = request.form.get('next_page', 'blocked_callers')
        with Persistence(app.config['TELEWALL_DATABASE_PATH']) as p:
            phone_number = TelephoneNumber(telephone_number_str)
            if p.is_blocked(phone_number):
                p.unblock(phone_number)
                flash('Der Anrufer %s wurde entsperrt.' % phone_number.local, 'success')
            else:
                flash('Der Anrufer %s war bereits entsperrt.' % phone_number.local, 'success')
        if next_page == 'status':
            return redirect(url_for('search_result', number=telephone_number_str))
        else:
            return redirect(url_for(next_page))
    else:
        # GET Request
        return render_template('unblock_caller.html')


@app.route('/status-<number>', methods=['GET'])
def search_result(number):
    """  Show if the caller is blocked or not.
    :param number: phone number string
    """
    phone_number = TelephoneNumber(number)
    with Persistence(app.config['TELEWALL_DATABASE_PATH']) as p:
        blocked_caller = p.find(phone_number)
    with AsteriskPersistence(app.config['ASTERISK_DATABASE_PATH'], print_sql=True) as p:
        call_history = p.get_call_history(phone_number=phone_number)

    return render_template('status.html', phone_number_local=phone_number.local, blocked_caller=blocked_caller,
                           call_history=call_history)


@app.route('/search', methods=['POST', 'GET'])
def search():
    """  Search a caller using a form.
    The GET requests shows the form.
    The POST requets redirects the user.
    """
    if request.method == 'POST':
        telephone_number_str = request.form['telephone_number']
        if _is_plausible_number(telephone_number_str):
            return redirect(url_for('search_result', number=telephone_number_str))
        else:
            flash(u'Die eingegebene Rufnummer ist ungültig. Bitte versuchen Sie es nochmal. ', 'warning')
            return render_template('search_form.html', telephone_number=telephone_number_str)
    else:
        return render_template('search_form.html')


@app.errorhandler(404)
def page_not_found(error):
    """ Shows an error message in case an invalid address is accessed.
    :param error: error object
    """
    return 'Sorry, Seite nicht gefunden. Versuchen Sie es <a href="%s">hier</a>.' % url_for('root')


def _is_plausible_number(telephone_number):
    """ Internal function validates if the number looks roughly like a phone number. Does not validate it.
    :param telephone_number: the phone number string to validate.
    :return: True if the number is roughly valid.
    """
    return re.match('[+0][0-9 ]+', telephone_number) and TelephoneNumber(telephone_number, validate=True).is_valid


def _block_number(telephone_number, comment=''):
    """ Internal function blocks a telephone number.
    :param telephone_number: phone number to block
    :param comment: (optional) comment typed by the user
    """
    source = 'web'
    with Persistence(app.config['TELEWALL_DATABASE_PATH']) as p:
        phone_number = TelephoneNumber(telephone_number)
        if not p.is_blocked(phone_number):
            p.block(phone_number, comment, source)
            flash('Der Anrufer %s wurde gesperrt.' % telephone_number, 'success')
        else:
            flash('Der Anrufer %s ist bereits gesperrt.' % telephone_number, 'success')


# used for session and cookie handling, should be changed in production.
app.secret_key = '\xf7\xe3\xe1\xa7o\x91\x1fZ\'\xf0\xbf\x7fY\xb8\xa0\xd4\xe6\x9bC1\xdf/\xa6\x10'


def url_for_other_page(page):
    """ url helper function for pagination.

    taken from http://flask.pocoo.org/snippets/44/, see documentation there
    :param page: page number
    :return: url for the given page number
    """
    args = request.view_args.copy()
    args['page'] = page
    return url_for(request.endpoint, **args)


app.jinja_env.globals['url_for_other_page'] = url_for_other_page

if __name__ == '__main__':
    # when executing the module directly, a temporary database is created.
    app.config['TELEWALL_DATABASE_PATH'] = create_temp_telewall_db(sample_data=True, overwrite=False)
    app.config['ASTERISK_DATABASE_PATH'] = create_temp_asterisk_db(sample_data=True, overwrite=False)
    app.debug = True
    app.run(host='127.0.0.1', port=9090)
