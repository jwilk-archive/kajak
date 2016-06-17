# Copyright © 2010-2012 Jakub Wilk <jwilk@jwilk.net>
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
import os
import re
import subprocess as ipc

def _set_c_locale():
    os.environ['LC_ALL'] = 'C'

def parse_date(s):
    if s == 'today':
        # shortcut:
        return datetime.date.today()
    args = ['date', '--rfc-3339=date', '--date={}'.format(s)]
    child = ipc.Popen(args, stdout=ipc.PIPE, stderr=ipc.PIPE, preexec_fn=_set_c_locale)
    stdout, stderr = child.communicate()
    if stderr:
        stderr = stderr.decode('ASCII')
        raise ValueError('cannot parse date: {0}'.format(stderr))
    stdout = stdout.decode('ASCII')
    y, m, d = map(int, stdout.strip().split('-'))
    return datetime.date(y, m, d)

distant_past = datetime.date(1, 1, 1)
distant_future = datetime.date(9999, 1, 1)
everytime = (distant_past, distant_future)
today = datetime.date.today()

split_range = re.compile(r'''
( \s*<\s*(?P<r1>.*)
| \s*>\s*(?P<l1>.*)
| \s*(<?P<l0>.*\S)\s+to\s+(?P<r0>.*)
) $
''', re.VERBOSE).match

def parse_range(s):
    ldate = distant_past
    rdate = distant_future
    match = split_range(s)
    if match is None:
        ldate = rdate = parse_date(s)
    else:
        for k, v in match.groupdict().items():
            if v is None:
                continue
            if k[0] == 'l':
                ldate = parse_date(v)
            else:
                assert k[0] == 'r'
                rdate = parse_date(v)
    return (ldate, rdate)

# vim:ts=4 sts=4 sw=4 et
