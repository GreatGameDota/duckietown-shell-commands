import sys

import dt_shell
from dt_shell import UserError

if sys.version_info < (3, 6):
    msg = 'duckietown-shell-commands requires Python 3.6 and later.\nDetected %s.' % str(sys.version)
    raise UserError(msg)

from .command import *

min_duckietown_shell = '4.0.13'
duckietown_shell_commands_version = '4.0.7'


def parse_version(x):
    return tuple(int(_) for _ in x.split('.'))


def render_version(t):
    return ".".join(str(_) for _ in t)


def check_compatible():
    sys.stderr.write('Duckietown Shell commands version %s\n' % duckietown_shell_commands_version)
    OtherVersions = getattr(dt_shell, 'OtherVersions', {})
    OtherVersions.name2versions['duckietown-shell-commands'] = duckietown_shell_commands_version

    vnow = parse_version(dt_shell.__version__)
    vneed = parse_version(min_duckietown_shell)

    if vneed > vnow:
        msg = '''

Detected Duckietown Shell %s but these commands (%s) need Duckietown Shell >= %s.
''' % (render_version(vnow), duckietown_shell_commands_version, render_version(vneed))



        raise UserError(msg)


check_compatible()
