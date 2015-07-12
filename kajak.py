# encoding=UTF-8

'''
helper module that allows using command-line tools without installing them
'''

import sys
import lib

sys.modules['kajak'] = lib

# vim:ts=4 sts=4 sw=4 et
