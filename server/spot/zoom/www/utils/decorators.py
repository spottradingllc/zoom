import time
import logging
from functools import wraps


class TimeThis(object):
    
    def __init__(self, filename=""):
        if filename is not "":
            filename += ' '
        self.filename = filename

    def __call__(self, function):
        @wraps(function)
        def new_function(*args, **kwargs):
            start = time.time()
            out = function(*args, **kwargs)
            stop = time.time()
            logging.info(":timethis: {0} {1}, {2:0.6f}"
                         .format(self.filename,
                                 function.__name__,
                                 stop - start))
            return out
        
        return new_function
