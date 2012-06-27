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

class AmbiguousPop(LookupError):
    pass

class AmbiguousReschedule(LookupError):
    pass

class Storage(object):

    def iter(self, date_range):
        (ldate, rdate) = date_range
        for date, text in self:
            if date < ldate:
                continue
            if date > rdate:
                break
            yield (date, text)

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
        self.data = []
        with open(path, 'r+t', encoding='UTF-8') as file:
            for line in file:
                match = self.parse_line(line)
                year, month, day, text = match.groups()
                year, month, day = map(int, (year, month, day))
                stamp = datetime.date(year, month, day)
                self.data.append((stamp, text))
        self.data.sort()

    def push(self, date, text):
        if not isinstance(date, datetime.date):
            raise TypeError
        if not isinstance(text, str):
            raise TypeError
        if text != text.strip():
            raise ValueError('leading/trailing space not allowed')
        # TODO: check for duplicates
        self.data += [(date, text)]
        self.data.sort()

    def pop(self, date_range, text, multi=False):
        candidates = frozenset(
            (d, t)
            for d, t in self.iter(date_range)
            if t == text
        )
        if multi or len(candidates) == 1:
            self.data = [
                item
                for item in self.data
                if item not in candidates
            ]
        else:
            raise AmbiguousPop(candidates)

    def reschedule(self, date_range, text, new_date, multi=False):
        candidates = frozenset(
            (d, t)
            for d, t in self.iter(date_range)
            if t == text
        )
        if multi or len(candidates) == 1:
            self.data = [
                item
                for item in self.data
                if item not in candidates
            ] + [
                (new_date, text)
                for date, text in candidates
            ]
            self.data.sort()
        else:
            raise AmbiguousReschedule(candidates)

    def __iter__(self):
        return iter(self.data)

    def save(self):
        tmppath = self.path + '.kajak-tmp'
        with open(tmppath, 'wt', encoding='UTF-8') as file:
            for date, text in self.data:
                print(date, text, file=file)
            os.fsync(file)
        os.rename(tmppath, self.path)

# vim:ts=4 sw=4 et
