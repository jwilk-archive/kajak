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
import errno
import os
import re

from . import chrono
from .event import Event

class MatchError(LookupError):
    pass

class NoMatches(MatchError):
    pass

class MultipleMatches(MatchError):
    pass

class Duplicate(LookupError):
    pass

class Storage(object):

    def iter(self, date_range):
        (ldate, rdate) = date_range
        for event in self:
            if event.date < ldate:
                continue
            if event.date > rdate:
                break
            yield event

    def grep(self, regexp):
        match = regexp.search
        return (
            event
            for event in self
            if match(event.text)
        )

class TextStorageSyntaxError(SyntaxError):
    pass

class TextStorage(Storage):

    parse_line = re.compile(r'(?P<year>[0-9]{4})-(?P<month>[0-9]{2})-(?P<day>[0-9]{2})\s+(?P<text>.*)').match

    def __init__(self, path):
        self.path = path
        try:
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except OSError as exc:
            if exc.errno == errno.EEXIST:
                pass
            else:
                raise
        else:
            os.close(fd)
        self.data = set()
        with open(path, 'r+t', encoding='UTF-8') as file:
            self.import_(file)

    def push(self, date, text):
        event = Event(date, text)
        if event in self.data:
            raise Duplicate(event)
        self.data.add(event)

    def pop(self, date_range, text, multi=False):
        candidates = frozenset(
            event
            for event in self.iter(date_range)
            if event.text == text
        )
        if multi or len(candidates) == 1:
            self.data.difference_update(candidates)
        elif len(candidates) == 0:
            raise NoMatches
        else:
            raise MultipleMatches(candidates)

    def reschedule(self, date_range, text, new_date, multi=False):
        candidates = frozenset(
            event
            for event in self.iter(date_range)
            if event.text == text
        )
        if multi or len(candidates) == 1:
            for event in candidates:
                event.date = new_date
        elif len(candidates) == 0:
            raise NoMatches
        else:
            raise MultipleMatches(candidates)

    def __iter__(self):
        return iter(sorted(self.data))

    def clear(self, date_range):
        candidates = frozenset(self.iter(date_range))
        self.data.difference_update(candidates)

    def import_(self, file):
        for n, line in enumerate(file):
            match = self.parse_line(line)
            if match is None:
                raise TextStorageSyntaxError('cannot parse {name}:{n}: {line!r}'.format(name=file.name, n=n, line=line))
            year, month, day, text = match.groups()
            year, month, day = map(int, (year, month, day))
            stamp = datetime.date(year, month, day)
            event = Event(stamp, text)
            self.data.add(event)

    def export(self, date_range, file):
        for event in self.iter(date_range):
            print(event.date, event.text, file=file)

    def save(self):
        tmppath = self.path + '.kajak-tmp'
        with open(tmppath, 'wt', encoding='UTF-8') as file:
            self.export(chrono.everytime, file)
            os.fsync(file)
        os.rename(tmppath, self.path)

# vim:ts=4 sw=4 et
