from data_utilities import *class Session(object):    __slots__ = ('base',)        def __init__(self):        self.base = None            def pop(self, key=-1):        pass        def has_hey(self, key):        pass        def __setitem__(self, key, item):        pass        def __getitem__(self, key):        pass        def set_data(self):        pass        def clean(self):        pass        class DictSession(dict):    __slots__ = ()        def __init__(self):        self.base = {}                