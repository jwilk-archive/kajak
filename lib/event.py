# Copyright © 2012 Jakub Wilk <jwilk@jwilk.net>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the “Software”), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import datetime
import functools
import warnings

class EventWarning(UserWarning):
    pass

_extra_setters = {}

def extra(s):
    def nested(f):
        _extra_setters[s] = f
        return f
    return nested

def _check_string(s):
    if not isinstance(s, str):
        raise TypeError
    if not s:
        raise ValueError('empty strings not allowed')
    if s != s.strip():
        raise ValueError('leading/trailing space not allowed')
    if '\r' in s or '\n' in s:
        raise ValueError('newlines not allowed')

class Event(object):

    def __init__(self, date, text, *, extra=()):
        if not isinstance(date, datetime.date):
            raise TypeError
        _check_string(text)
        self.date = date
        self.text = text
        self.extra = list(extra)
        self._reschedule_hint = None
        for key, value in self.extra:
            _check_string(key)
            _check_string(value)
            try:
                setter = _extra_setters[key]
            except LookupError:
                warnings.warn('unknown attribute {0!r}'.format(key), category=EventWarning, stacklevel=2)
                continue
            setter(self, value)

    @extra('reschedule-hint')
    def set_reschedule_hint(self, value):
        self._reschedule_hint = value

    def get_reschedule_hint(self):
        if self._reschedule_hint is None:
            raise LookupError
        return self._reschedule_hint

    def _as_tuple(self):
        return (self.date, self.text)

    def __eq__(self, other):
        if not isinstance(other, Event):
            return NotImplemented
        return self._as_tuple() == other._as_tuple()

    def __lt__(self, other):
        if not isinstance(other, Event):
            return NotImplemented
        return self._as_tuple() < other._as_tuple()

    def __hash__(self):
        return hash(self._as_tuple())

# vim:ts=4 sw=4 et
