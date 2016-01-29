import logging

import requests

from telewall.asterisk import Constants
from telewall.core.model import TelephoneNumber

LOG = logging.getLogger(__name__)


class BaseAsteriskAppCall(object):
    """ abstract base class to implement an asterisk application.     """

    def __init__(self, ari_client, channel, asterisk_app_name):
        """
        :param ari_client: the ari client instance
        :param channel: the active channel with the handset
        """
        self.app_name = asterisk_app_name
        self.client = ari_client
        self.channel_incoming = channel
        self.channel_tohandset = None  # can optionally be used by app
        self.bridge = None  # can optionally be used by app
        self.call_state = None  # can optionally be used by app
        caller_dict = self.channel_incoming.json.get('caller')
        self.phone_number = TelephoneNumber(caller_dict['number'])

    def set_telewall_call_state(self, state_str):
        self.client.channels.setChannelVar(channelId=self.channel_incoming.id, variable='CDR(telewall_state)',
                                           value=state_str)

    def get_announcement_media(self):
        """
        :return: the custom recorded announcement if existing, or the default announcement
        """
        try:
            self.client.recordings.getStored(recordingName=Constants.CUSTOM_ANNOUNCEMENT_RECORDING)
            has_custom_recording = True
        except requests.HTTPError as e:
            if e.response.status_code == requests.codes.not_found:
                has_custom_recording = False
                LOG.info('can not find custom sound recording %s', Constants.CUSTOM_ANNOUNCEMENT_RECORDING)
            else:
                raise e

        if has_custom_recording:
            # when using the recorinds api, the prefix 'recording:' is not required. but everywhere with the
            # sound api it is required.
            return 'recording:' + Constants.CUSTOM_ANNOUNCEMENT_RECORDING
        else:
            return Constants.DEFAULT_ANNOUNCEMENT
