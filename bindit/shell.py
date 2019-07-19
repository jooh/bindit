"""shell interface routines."""
import sys
import subprocess
import shlex


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


def join_and_quote(arg_list):
    """return a string of appropriately quoted and escaped arguments from list."""
    # need to cast to str because join chokes on pathlib.Path as of python 3.6
    # and shlex to get quotes on args with spaces (and escape any nested quotes)
    return " ".join([shlex.quote(str(this_arg)) for this_arg in arg_list])
