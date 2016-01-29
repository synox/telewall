import logging

listeners = {}

LOG = logging.getLogger(__name__)


def on(event_name, listener):
    if event_name in listeners.keys():
        listeners[event_name].append(listener)
    else:
        listeners[event_name] = [listener]
    LOG.debug('added listener for %s', event_name)


def notify(event_name, arg):
    LOG.debug('notify event %s (%s)', event_name, arg)
    if event_name in listeners.keys():
        for listener in listeners[event_name]:
            try:
                listener(arg)
            except Exception as e:
                LOG.exception('error while calling listener %s' % listener)
