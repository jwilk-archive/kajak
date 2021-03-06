# Copyright © 2012-2017 Jakub Wilk <jwilk@jwilk.net>
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

import argparse
import contextlib
import io
import os
import re
import subprocess as ipc
import sys
import tempfile

try:
    import jinja2
except ImportError:
    jinja2 = None

from . import chrono
from . import storage as storage_module
from . import utils

class ArgumentParser(argparse.ArgumentParser):

    def __init__(self):
        argparse.ArgumentParser.__init__(self)
        self.__subparsers = self.add_subparsers(
            parser_class=CommandParser
        )
        action = self.add_action('show')
        action.add_argument('range', nargs='?')
        action = self.add_action('push', aliases=['add'])
        action.add_argument('text')
        action.add_argument('date', nargs='?')
        action = self.add_action('pop', aliases=['del', 'delete'])
        action.add_argument('-m', '--multi', action='store_true', help='allow popping more than one task at once')
        action.add_argument('text')
        action.add_argument('range', nargs='?')
        action = self.add_action('reschedule', aliases=['move'])
        action.add_argument('text')
        action.add_argument('range', nargs='?')
        action.add_argument('new_date', type=date_type)
        action = self.add_action('grep')
        action.add_argument('regexp')
        action = self.add_action('import')
        action.add_argument('--replace', action='store_true')
        action = self.add_action('export')
        action.add_argument('range', nargs='?', default=chrono.everytime)
        action = self.add_action('edit')
        action.add_argument('range', nargs='?')

    def add_action(self, name, **kwargs):
        parser = self.__subparsers.add_parser(name, **kwargs)
        parser.set_defaults(action=globals()['do_' + name])
        return parser

def date_type(s):
    return chrono.parse_date(s)
date_type.__name__ = 'date'
date_type.default = chrono.today

def range_type(s):
    return chrono.parse_range(s)
range_type.__name__ = 'date range'
range_type.default = (chrono.distant_past, chrono.today)

class CommandParser(argparse.ArgumentParser):

    def add_argument(self, *args, **kwargs):
        type = None
        try:
            type = kwargs['type']
        except LookupError:
            if args[0].isalnum():
                type_name = '{name}_type'.format(name=args[0])
                try:
                    type = globals()[type_name]
                except LookupError:
                    pass
                else:
                    kwargs['type'] = type
        if ('metavar' not in kwargs) and (args[0][:1] != '-'):
            metavar = args[0].replace('_', '-')
            kwargs['metavar'] = '<{name}>'.format(name=metavar)
        try:
            default = type.default
        except AttributeError:
            pass
        else:
            kwargs.setdefault('default', default)
        argparse.ArgumentParser.add_argument(self, *args, **kwargs)

@contextlib.contextmanager
def storage(options, *, save=None):
    assert save is not None
    path = os.path.join(
        utils.xdg.save_data_path('kajak'),
        'storage.txt'
    )
    result = storage_module.TextStorage(path=path)
    yield result
    if save:
        result.save()

def render_plain(tasks, *, print=print):
    for event in tasks:
        print(event.date, event.text)

def render(tasks):
    if not jinja2:
        return render_plain(tasks)
    # TODO: documentation
    template_paths = [
        os.path.join(path, 'templates')
        for path in utils.xdg.load_config_paths('kajak')
    ]
    template_loader = jinja2.FileSystemLoader(template_paths)
    environment = jinja2.Environment(loader=template_loader)
    try:
        template = environment.get_template('default')
    except jinja2.exceptions.TemplateNotFound:
        return render_plain(tasks)
    tasks = list(tasks)
    print(template.render(today=chrono.today, tasks=tasks), end='')

def do_show(options):
    with storage(options, save=False) as this:
        render(this.iter(options.range))

def do_push(options):
    with storage(options, save=True) as this:
        try:
            this.push(options.date, options.text)
        except storage_module.Duplicate as exc:
            message = 'kajak: error: duplicate {exc}'.format(exc=exc)
            print(message, file=sys.stderr)

@contextlib.contextmanager
def handle_match_errors(text):
    try:
        yield
    except storage_module.NoMatches:
        message = 'kajak: error: no matches for {text!r}'.format(text=text)
        print(message, file=sys.stderr)
        sys.exit(1)
    except storage_module.MultipleMatches as exc:
        message = 'kajak: error: multiple matches for {text!r}:'.format(text=text)
        print(message, file=sys.stderr)
        def custom_print(*args):
            print('-', file=sys.stderr, end=' ')
            print(*args, file=sys.stderr)
        render_plain(exc.args[0], print=custom_print)
        sys.exit(1)

def do_pop(options):
    with storage(options, save=True) as this:
        with handle_match_errors(options.text):
            this.pop(options.range, options.text, multi=options.multi)

def do_reschedule(options):
    with storage(options, save=True) as this:
        with handle_match_errors(options.text):
            this.reschedule(options.range, options.text, options.new_date)

def do_grep(options):
    regexp = re.compile(options.regexp)
    with storage(options, save=False) as this:
        render(this.grep(regexp))

def do_import(options):
    stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='UTF-8')
    with storage(options, save=True) as this:
        if options.replace:
            this.clear(chrono.everytime)
        this.import_(stdin)

def do_export(options):
    stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='UTF-8')
    with storage(options, save=False) as this:
        this.export(options.range, stdout)

def do_edit(options):
    with storage(options, save=True) as this:
        with tempfile.NamedTemporaryFile(prefix='kajak.export.', suffix='.txt', mode='w+t', encoding='UTF-8') as file:
            this.export(options.range, file)
            file.flush()
            ipc.check_call([
                'sensible-editor',
                file.name
            ])
            file.seek(0)
            this.clear(options.range)
            this.import_(file)

def main():
    parser = ArgumentParser()
    if len(sys.argv) == 1:
        # default command
        sys.argv += ['show']
    options = parser.parse_args()
    options.action(options)

# vim:ts=4 sts=4 sw=4 et
