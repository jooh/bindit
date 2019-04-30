"""shell interface routines."""
import sys
import subprocess
import logging

LOGGER = logging.getLogger("bindit")


def run(*arg, interactive=False):
    """subprocess.run wrapper to handle exceptions, writing to stdout/stderr or not."""
    stdout = subprocess.PIPE
    stderr = subprocess.PIPE
    if interactive:
        stdout = None
        stderr = None
    try:
        ret = subprocess.run(
            arg, stdout=stdout, stderr=stderr, check=True, shell=False, encoding="utf-8"
        )
    except subprocess.CalledProcessError as ret:
        print(f"command line exception with args: {arg}")
        if not interactive:
            sys.stdout.write(ret.stdout)
            sys.stderr.write(ret.stderr)
        sys.exit(ret.returncode)
    except BaseException:
        raise
    return ret
