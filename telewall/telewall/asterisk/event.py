class Event(object):
    """ Events are used to change between states. Use only those defined here. """

    # DTMF digits
    DTMF_1 = '1'
    DTMF_2 = '2'
    DTMF_3 = '3'
    DTMF_4 = '4'
    DTMF_5 = '5'
    DTMF_6 = '6'
    DTMF_7 = '7'
    DTMF_8 = '8'
    DTMF_9 = '9'
    DTMF_0 = '0'
    # Use 'octothorpe' so there is no confusion about 'pound' or 'hash'
    # terminology.
    DTMF_OCTOTHORPE = '#'
    DTMF_STAR = '*'
    # Call has hung up
    HANGUP = 'hangup'
    # Playback of a file has completed
    PLAYBACK_COMPLETE = 'playback_complete'
    # the main action of the state is complete
    ACTION_COMPLETE = 'action_complete'
    CALLER_ALLOWED = 'caller_allowed'
    CALLER_REFUSED = 'caller_refused'
    # channel is answered
    ANSWER = 'answer'
    # channel is busy
    BUSY = 'busy'
    # input is not valid                                                                                                                                                                                                                        # easter egg (ignore this :-) )
    INVALID_INPUT = 'invalid_input'

    @classmethod
    def get_dtmf_event(cls, digit_str):
        if digit_str == '1':
            return Event.DTMF_1
        if digit_str == '2':
            return Event.DTMF_2
        if digit_str == '3':
            return Event.DTMF_3
        if digit_str == '4':
            return Event.DTMF_4
        if digit_str == '5':
            return Event.DTMF_5
        if digit_str == '6':
            return Event.DTMF_6
        if digit_str == '7':
            return Event.DTMF_7
        if digit_str == '8':
            return Event.DTMF_8
        if digit_str == '9':
            return Event.DTMF_9
        if digit_str == '#':
            return Event.DTMF_OCTOTHORPE
        if digit_str == '*':
            return Event.DTMF_STAR
