# -*- coding: utf-8 -*-

import sys
import json

from filters import ThresholdFilter
from formatters import Formatter
from emitters import StreamEmitter


class AggSink(object):
    "A 'dummy' sink that just aggregates the messages."
    def __init__(self):
        self.records = []

    def on_begin(self, record):
        pass

    def on_complete(self, record):
        self.records.append(record)


_MSG_ATTRS = ('name', 'level', 'status', 'message',
              'begin_time', 'end_time', 'duration')


class StructuredFileSink(object):
    def __init__(self, fileobj=None):
        self.fileobj = fileobj or sys.stdout

    def on_complete(self, record):
        msg_data = dict(record.extras)
        for attr in _MSG_ATTRS:
            msg_data[attr] = getattr(record, attr, None)
        json_str = json.dumps(msg_data, sort_keys=True)
        self.fileobj.write(json_str)
        self.fileobj.write('\n')


class SensibleSink(object):
    def __init__(self, filters=None, formatter=None, emitter=None):
        self.filters = list(filters or [])
        self.formatter = formatter
        self.emitter = emitter

    def on_complete(self, record):
        if self.filters and not all([f(record) for f in self.filters]):
            return
        entry = self.formatter(record)
        return self.emitter(entry)


from quantile import QuantileAccumulator


class QuantileSink(object):
    def __init__(self):
        self.qa = QuantileAccumulator()

    def on_complete(self, record):
        self.qa.add(record.duration)

    def __getattr__(self, name):
        return getattr(self.qa, name)


if __name__ == '__main__':
    fmtr = Formatter('{begin_timestamp} - {record_status}')
    emtr = StreamEmitter()
    ss = SensibleSink(formatter=fmtr, emitter=emtr)
    from logger import BaseLogger
    log = BaseLogger('test_ss', [ss])
    with log.debug('hi_task') as t:
        t.warn('everything ok?')
        t.success('doin great')
