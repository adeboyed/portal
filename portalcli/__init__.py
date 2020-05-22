import sys

from .errors import CommandLineError
from .utils import split_argv
from .Portal import Portal


def _real_main(argv=None):
    retcode = 0
    
    cmd, args = split_argv(argv)

    portal = Portal()
    retcode = portal.run_command(cmd, args)

    sys.exit(retcode)




def main(argv=None):
    try:
        _real_main(sys.argv)
    except CommandLineError as err:
        sys.exit(err.message)
    except KeyboardInterrupt:
        sys.exit('\nERROR: Interrupted by user')


__all__ = ['main', 'Portal']