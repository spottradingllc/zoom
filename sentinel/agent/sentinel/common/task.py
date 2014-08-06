

class Task(object):
    def __init__(self, name,
                 func=None, args=(), kwargs={}, block=True, pipe=False):
        """
        :type name: str
        :type func: function or None
        :type args: tuple
        :type kwargs: dict
        :type block: bool
        :type pipe: bool
        """
        self.name = name
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.block = block
        self.pipe = pipe

    def __eq__(self, other):
        return self.name == other

    def __ne__(self, other):
        return self.name != other

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return ('{0}(name={1}, args={2}, kwargs={3}, block={4})'
                .format(self.__class__.__name__,
                        self.name,
                        self.args,
                        self.kwargs,
                        self.block))