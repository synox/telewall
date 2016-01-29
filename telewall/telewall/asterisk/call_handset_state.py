import logging

from event import Event
from telewall.asterisk.asterisk_state import AsteriskState

LOG = logging.getLogger(__name__)


class CallHandsetState(AsteriskState):
    """ identifies the caller and decides how to handle the call.
    """

    def __init__(self, call):
        """
        Create the state instance
        :param call: the managing class, used for callbacks
        """
        super(CallHandsetState, self).__init__(call)
        self.call = call
        self.hangup_channel1_event = None
        self.second_channel_ready_event = None
        self.second_channel_destroyed_event = None

    def enter(self):
        """ start recording. Asterisk stopps and saves the recording automatically on hangup.         """
        self._watch_channel_hangup()

        self._call_handset(self.call.channel_incoming, endpoint=self.call.handset_endpoint)

    def _call_handset(self, first_channel, endpoint):
        """ opens a new channel to the handset.

        A bridge is created to connect both channels.

        :param first_channel: the first_channel (incomding call)
        :param endpoint: protocol and name of the endpoint (e.g. spa232d-line1)
        """

        LOG.debug('Dialing %s', endpoint)
        self.call.set_telewall_call_state('no_answer')

        sip_callerid_with_name = self._get_sipcallerid(self.call.phone_number)

        self.call.channel_tohandset = self.call.client.channels.originate(endpoint=endpoint,
                                                                          app=self.call.app_name,
                                                                          appArgs='dialed',
                                                                          callerId=sip_callerid_with_name)

        self.call.channel_incoming.ring()

        self.second_channel_ready_event = self.call.channel_tohandset.on_event('StasisStart', self.second_channel_ready)

        # If the endpoint rejects the call, it is destroyed without entering Stasis()
        self.second_channel_destroyed_event = self.call.channel_tohandset.on_event('ChannelDestroyed',
                                                                                   self.second_channel_destroyed)

    def _get_sipcallerid(self, phone_number):
        """
        generate string to use for sip, populated with name

        :return: SIP callerid pupulated with name (if available)
        :rtype: string
        """
        if phone_number.name:
            name = phone_number.name
        else:
            name = phone_number.local
        return "%s <%s>" % (name, phone_number.local)

    def second_channel_ready(self, second_channel, ev):
        """ when second channel is ready add it to the bridge.
        :param second_channel: the channel
        :param ev: the event
        """

        LOG.info('%s answered; bridging with %s', self.call.channel_tohandset.json.get('name'),
                 self.call.channel_incoming.json.get('name'))
        self.call.set_telewall_call_state('answered')
        self.call.channel_incoming.answer()

        self.call.call_state.answer()

        self.call.bridge = self.call.client.bridges.create(type='mixing,dtmf_events')
        self.call.bridge.addChannel(channel=[self.call.channel_incoming.id, self.call.channel_tohandset.id])

        self.cleanup()
        self.call.state_machine.change_state(Event.ANSWER)

    def second_channel_destroyed(self, second_channel, ev):
        self.call.set_telewall_call_state('busy')
        self.cleanup()
        self.call.channel_incoming.hangup(reason='busy')

        self.call.state_machine.change_state(Event.BUSY)

    def cleanup(self):
        """ Close handles and unsubscribe from events         """
        self._cleanup_watch_channel_hangup()

        if self.second_channel_ready_event:
            self.second_channel_ready_event.close()
        if self.second_channel_destroyed_event:
            self.second_channel_destroyed_event.close()

    def on_hangup(self, channel, event):
        """ when user hang up close channel and change state
        :param channel: the channel
        :param event: the hangup event
        """
        self.cleanup()
        self.call.state_machine.change_state(Event.HANGUP)
