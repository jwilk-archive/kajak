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

import os

class xdg(object):
    '''
    tiny replacement for PyXDG's xdg.BaseDirectory
    '''

    xdg_config_home = os.environ.get('XDG_CONFIG_HOME') or ''
    if not os.path.isabs(xdg_config_home):
        xdg_config_home = os.path.join(os.path.expanduser('~'), '.config')

    @classmethod
    def load_config_paths(xdg, resource):
        for config_dir in xdg.xdg_config_dirs:
            path = os.path.join(config_dir, resource)
            if os.path.exists(path):
                yield path

    xdg_data_home = os.environ.get('XDG_DATA_HOME') or ''
    if not os.path.isabs(xdg_data_home):
        xdg_data_home = os.path.join(os.path.expanduser('~'), '.local', 'share')

    @classmethod
    def save_data_path(xdg, resource):
        path = os.path.join(xdg.xdg_data_home, resource)
        try:
            os.makedirs(path, 0o700)
        except OSError:
            if not os.path.isdir(path):
                raise
        return path

# vim:ts=4 sw=4 et
