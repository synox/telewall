class Interruptible(object):
    """ Helper class to allow interrupting functions.    """

    def __init__(self, is_interrupted_func):
        """
        :param is_interrupted_func: the function is called often. It should return True to interrupt the process.
        """
        self.is_interrupted_func = is_interrupted_func

    def is_interrupted(self):
        """
        :return: returns True if the process has been interrupted.
        """
        return self.is_interrupted_func()
