from operator import itemgetter, setitem

class SettlementPeriodData(tuple):
    'SettlementPeriodData(id, time_start, length, length_in, autostart)' 

    __slots__ = () 

    _fields = ('id', 'time_start', 'length', 'length_in', 'autostart') 

    def __new__(cls, id, time_start, length, length_in, autostart):
        return tuple.__new__(cls, (id, time_start, length, length_in, autostart)) 

    @classmethod
    def _make(cls, iterable, new=tuple.__new__, len=len):
        'Make a new SettlementPeriodData object from a sequence or iterable'
        result = new(cls, iterable)
        if len(result) != 5:
            raise TypeError('Expected 5 arguments, got %d' % len(result))
        return result 

    def __repr__(self):
        return 'SettlementPeriodData(id=%r, time_start=%r, length=%r, length_in=%r, autostart=%r)' % self 

    def _asdict(t):
        'Return a new dict which maps field names to their values'
        return {'id': t[0], 'time_start': t[1], 'length': t[2], 'length_in': t[3], 'autostart': t[4]} 

    def _replace(self, **kwds):
        'Return a new SettlementPeriodData object replacing specified fields with new values'
        result = self._make(map(kwds.pop, ('id', 'time_start', 'length', 'length_in', 'autostart'), self))
        if kwds:
            raise ValueError('Got unexpected field names: %r' % kwds.keys())
        return result 

    def __getnewargs__(self):
        return tuple(self) 

    id = property(itemgetter(0))
    time_start = property(itemgetter(1))
    length = property(itemgetter(2))
    length_in = property(itemgetter(3))
    autostart = property(itemgetter(4))