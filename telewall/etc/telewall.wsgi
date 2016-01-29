# load Virtualenv
activate_this = '/telewall/py2-env/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))

# set python path
import sys
sys.path.insert(0, '/telewall/')

# load web applikation
from telewall.web.web import app as application

# configure database (optional)
#application.config['TELEWALL_DATABASE_PATH'] = '/telewall/data/database.sqlite3'
#application.config['ASTERISK_DATABASE_PATH'] = '/var/log/asterisk/master.db'
