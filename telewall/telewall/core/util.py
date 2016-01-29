import time
from subprocess import Popen, PIPE

from math import ceil

from telewall.core.config import Config


def sleep_until(wakeup_cond, timeout=0):
    """
    sleeps until the given function returns true or when the timeout expires.
    :param wakeup_cond: sleep stops when this function returns True
    :param timeout: timeout in seconds
    :return: None
    """
    sleep_sum = 0
    step = 0.1
    while (timeout == 0 or sleep_sum <= timeout) and not wakeup_cond():
        time.sleep(step)
        sleep_sum += step


def get_ip():
    """
    :return: IP address of eth0. the interface eth0:0 with the static ip is filtered out.
    """
    try:
        p = Popen("ip addr show eth0 | grep inet | grep -v eth0:0 | grep -v inet6 | awk '{print $2}' | cut -d/ -f1",
                  shell=True,
                  stdout=PIPE)
        output = p.communicate()[0]
        return output.decode(encoding='utf8')
    except:
        return 'ip unknown'


def get_cisco_spa232D_md5(string):
    """ expand the string and hash with md5. this is how spa232d hashes the password.

    Note: no security is gained by expanding the password. The attacker can just repeat the request with the same hash.

    :param string: the string to hash
    :return: md5 hex hash as string
    """
    import hashlib

    # append the length of the string as two decimals with leading 0
    pwd_with_padding = string + "%02d" % (len(string),);

    # expand to 64 characters by repeating the password with length
    expanded = pwd_with_padding * int(ceil(64.0 / len(pwd_with_padding)))
    expanded = expanded[0:64]

    # hash the expanded string
    return hashlib.md5(expanded).hexdigest()


def get_cisco_spa232D_ip():
    """
    :return: public ip address of spa232d device.
    """
    try:
        import requests
        import re
        userid = Config.ATA_USERNAME
        pwd = Config.ATA_PASSWORD
        r = requests.post('http://192.168.15.1:80/login.cgi',
                          data={'submit_button': 'login', 'keep_name': '1', 'enc': '0', 'user': userid,
                                'pwd': get_cisco_spa232D_md5(pwd),
                                '_keep_name': 'on'})

        m = re.search("session_key='(.*)'", r.text)
        session_id = m.group(1)

        r = requests.post('http://192.168.15.1:80/Status_Iface.asp;session_id=%s' % session_id)

        # s = "wan_array[0]=new STATUS_IFACE_ENTRY('wan', 'br0', 'WAN1', 'Automatic Configuration - DHCP', '192.168.0.16', '255.255.255.0', '7C:AD:74:9B:9B:52', '99');"
        m = re.search("'WAN1', '.*?', '(.*?)',", r.text)
        wan_ip = m.group(1)
        if wan_ip == '--':
            # the ip is '--' if the wan interface is not connected.
            return None
        return wan_ip
    except:
        return None
