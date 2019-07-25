======
bindit
======


.. image:: https://img.shields.io/pypi/v/bindit.svg
        :target: https://pypi.python.org/pypi/bindit

.. image:: https://img.shields.io/travis/jooh/bindit.svg
        :target: https://travis-ci.org/jooh/bindit

.. image:: https://readthedocs.org/projects/bindit/badge/?version=latest
        :target: https://bindit.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status


Takes the drudgery out of binding volumes on Docker and (soon) Singularity

bindit is a wrapper for container runners that makes it easy to handle file input and
output for containerised command-line applications. It works by detecting file paths in
the container image arguments, and rebasing these as necessary onto new bind mounts. See
`docs`_ for full detail, but here is the high-level API:

.. _docs: https://bindit.readthedocs.io

.. code-block:: console
   
   Usage: bindit [OPTIONS] COMMAND [ARGS]...

     bindit is a wrapper for container runners that makes it easy to handle
     file input and output for containerized command-line applications. It
     works by detecting file paths in the container image arguments, and
     rebasing these as necessary onto new bind mounts.

   Options:
     -i, --ignorepath PATH  path(s) on the host to ignore when detecting new bind
                            mounts. Typical         linux binary locations
                            (/usr/bin etc) are included on this list by default.
     -a, --absonly          Only rebase absolute paths.
     -d, --dryrun           Return formatted shell command without invoking
                            container runner
     -l, --loglevel TEXT    Logging level  [default: INFO]
     --help                 Show this message and exit.

   Commands:
     docker

.. code-block:: console

   Usage: bindit_partial [OPTIONS] SCRIPT_ARG...

     bindit_partial constructs a shell script wrapper for bindit (or your
     container runner directly) that can be used as a command line interface
     for the container. It works a bit like functools.partial in the standard
     library - you can offload some default parameters (e.g. for volume binds
     mounts) to the script in order to obtain a cleaner API for the container.

     For main documentation, see bindit.

   Options:
     --output_file TEXT     Output to file instead of standard out
     --shebang TEXT         Shell interpreter directive  [default: #!/bin/bash]
     --vararg_pattern TEXT  vararg pattern (try "$argv" for csh/tcsh)  [default:
                            "$@"]
     --help                 Show this message and exit.   Usage: bindit_partial [OPTIONS] SCRIPT_ARG...

* Free software: MIT license
* Documentation: https://bindit.readthedocs.io
* Pull requests are welcome!
