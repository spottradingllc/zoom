import datetime
import json
import logging


class Task(object):
    def __init__(self, name,
                 func=None, args=(), kwargs={}, block=True,
                 retval=True, target=None, host=None, result=None,
                 submitted=None):
        """
        :type name: str
        :type func: types.FunctionType or None
        :type args: tuple
        :type kwargs: dict
        :type block: bool
        :type retval: bool
        :type target: str or None
        :type host: str or None
        :type result: str or None
        :type submitted: str or None
        """
        self.name = name
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.block = block
        self.retval = retval
        self.target = target
        self.host = host
        self.result = result
        self.submitted = submitted

    def to_json(self):
        """
        :rtype: str
        """
        return json.dumps(self.__dict__)

    def to_dict(self):
        """
        :rtype: dict
        """
        return self.__dict__

    @staticmethod
    def from_json(json_data):
        """
        :type json_data: str or dict
        :rtype: zoom.agent.task.task.Task
        """
        if isinstance(json_data, str):
            try:
                json_data = json.loads(json_data)
            except ValueError:
                logging.warning('Data could not be parsed: {0}'
                                .format(json_data))
                return None

        return Task(json_data.get('name'),
                    func=json_data.get('func', None),
                    args=json_data.get('args', ()),
                    kwargs=json_data.get('kwargs', {}),
                    block=json_data.get('block', True),
                    retval=json_data.get('retval', False),
                    target=json_data.get('target', None),
                    host=json_data.get('host', None),
                    result=json_data.get('result', None),
                    submitted=json_data.get('submitted', datetime.datetime.now().strftime('%Y%m%d %H:%M:%S')),
                    )

    def __eq__(self, other):
        return all([
            type(self) == type(other),
            self.name == getattr(other, 'name', None),
            self.target == getattr(other, 'target', None),
            self.host == getattr(other, 'host', None)
        ])

    def __ne__(self, other):
        return any([
            type(self) != type(other),
            self.name != getattr(other, 'name', None),
            self.target != getattr(other, 'target', None),
            self.host != getattr(other, 'host', None)
        ])

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return ('{0}(name={1}, args={2}, kwargs={3}, block={4}, '
                'target={5}, host={6}, result={7}, submitted={8})'
                .format(self.__class__.__name__,
                        self.name,
                        self.args,
                        self.kwargs,
                        self.block,
                        self.target,
                        self.host,
                        self.result,
                        self.submitted))
