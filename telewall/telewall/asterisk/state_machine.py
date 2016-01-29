import logging

LOG = logging.getLogger(__name__)


class StateMachine(object):
    """ A simple state machine. Events are used to transition between states.

    Based on https://wiki.asterisk.org/wiki/display/AST/Introduction+to+ARI+and+Media+Manipulation
    """

    def __init__(self):
        self.transitions = {}
        """ transitions is a 2-dimensiona map with source state and events as keys. """
        self.current_state = None

    def add_transition(self, src_state, event, dst_state):
        """ add a transitions between states
        :param src_state: source state
        :param event: the event, field of telewall.asterisk.Event
        :param dst_state: destination state
        """
        src_key = self._get_key(src_state)
        if not self.transitions.get(src_key):
            self.transitions[src_key] = {}

        self.transitions[src_key][event] = dst_state

    def change_state(self, event):
        """ run the transition from current state using the event to the new state.
        :param event: the event, field of telewall.asterisk.Event
        :return:
        """
        try:
            key = self._get_key(self.current_state)
            self.current_state = self.transitions[key][event]
            LOG.info('entering state %s', self._get_key(self.current_state))
            self.current_state.enter()
        except KeyError as e:
            LOG.error('can not find transition from %s with event %s', self._get_key(self.current_state), event)
            raise e

    def start(self, initial_state):
        """ start the initial state now

        :param initial_state: the initial state
        """
        self.current_state = initial_state
        self.current_state.enter()

    def has_transition(self, src_state, event):
        """ Checks if the given transition exists. This allowes to make default implementation based on the
        existence of a transition.

        :param src_state: source state
        :param event: the event, field of telewall.asterisk.Event
        :return: True the transition exists
        """
        key = self._get_key(src_state)
        return event in self.transitions[key].keys()

    def _get_key(self, state_instance):
        """ internal method to define the key for the map. the key must be unique for each instance of a class.
        :param state_instance: the state
        :return: a string that can be used as key
        """
        # the class name makes it human-readable for debugging
        return state_instance.__class__.__name__ + str(id(state_instance))
