=============
Usage: bindit
=============

Bindit is a command-line application. The basic usage is to prepend ``bindit`` to the
container runner command you would ordinarily use. 


Motivating example
------------------
Let's say you wanted to use a docker container to list the contents of your current home
directory you might do something like this on a unix-based system (Linux, OS X):

.. code-block:: bash

    $ docker run -v "$HOME":/data alpine:latest ls /data

With bindit, the bind mount is created automatically by detecting the file path
reference in the container image arguments. You can basically pretend that the container
has access to your host file system. So this works:

.. code-block:: bash

    $ bindit docker run alpine:latest ls "$HOME"/data

Bindit mounts are mapped to a new ``/bindit`` path inside the container to avoid
clobbering directories that might be necessary for the container to run (in particular,
messing with the container home directory as singularity does by default often breaks
containers). If we set the ``--dryrun`` flag the docker command prints to standard out
instead of running, and we can see the mapping bindit created:

.. code-block:: bash

   $ bindit --dryrun docker run alpine:latest ls "$HOME"
   docker run -v /Users/jc01:/bindit/Users/jc01 alpine:latest ls /bindit/Users/jc01

Turning the above examples into a re-usable application that can be added to your path
is easy - see :doc:`usage_partial`.

Default and optional behavior
-----------------------------

Bindit's default behavior can be controlled with the following flags:

-a, --absonly
~~~~~~~~~~~~~

Only auto-bind absolute paths. Useful if you call bindit from a folder that has
sub-folders which shadow binaries inside the container (``python`` is a frequent offender
for me).

-d, --dryrun
~~~~~~~~~~~~

Return a formatted shell command without invoking container runner. Useful for
debugging, and when you want to defer running the container to a different context (for
instance, HPC job submission).

Note that bindit *does* require the container runner on path to parse container runner
arguments correctly, so for instance, it's not good practice to dryrun docker jobs on a
machine that does not have docker available (or indeed a different docker version from
what you use in production).

-i, --ignorepath
~~~~~~~~~~~~~~~~

bindit won't attempt to bind any path that is a sub-directory of the specified path(s).
You can use this flag multiple times. The result is appended to a list of default unix
root folders (see ``bindit.IGNORE_PATH``).

-l, --loglevel
~~~~~~~~~~~~~~

Set the verbosity of log messages printed to the shell standard out. Default level is
INFO, try DEBUG for more detail.

Combining user-defined and automatic binds
------------------------------------------

We have seen that bindit defaults to creating new bind mounts in the ``/bindit``
directory inside the container. But bindit also detects user-specified binds, and will
use them whenever possible (for instance, when the user-specified bind is a parent of
the input path):

.. code-block:: bash

    $ mkdir -p foo/bar
    $ bindit --dryrun docker run -v $(PWD):/container alpine:latest ls foo
    docker run -v /Users/jc01/temp:/container alpine:latest ls /container/foo

Limitations
-----------

There are limitations to what paths bindit can detect automatically. The workaround for
these is typically to use absolute paths or to specify manual binds.

Specifying output paths
~~~~~~~~~~~~~~~~~~~~~~~
Bindit can only detect *relative* paths when they exist. *Absolute* paths work either way. This can trip you up when calling a container application with an argument that defines the output file path. These must always be absolute (unless it's a folder, or you are otherwise modifying or overwriting an existing path).

This can lead to seemingly baffling behavior. For example, suppose we want to use
`ImageMagick`_ to downsize an image and save it to a new name. We use ``--dryrun`` to
preview what the final docker run command will look like. Note that the input image has
been re-mapped correctly, but the output image hasn't because it doesn't exist yet:

.. _ImageMagick: https://imagemagick.org

.. code-block:: bash

   $ touch in.jpg
   $ rm -f out.jpg
   $ bindit --dryrun docker run dpokidov/imagemagick in.jpg -resize 100x100 out.jpg
   docker run -v /Users/jc01/temp:/bindit/Users/jc01/temp dpokidov/imagemagick \
      /bindit/Users/jc01/temp/in.jpg -resize 100x100 out.jpg

If we instead specify an absolute output path, both in.jpg and out.jpg get re-mapped to
the correct locations:

.. code-block:: bash

   $ bindit --dryrun docker run dpokidov/imagemagick in.jpg -resize 100x100 "$PWD"/out.jpg
   docker run -v /Users/jc01/temp:/bindit/Users/jc01/temp dpokidov/imagemagick \
      /bindit/Users/jc01/temp/in.jpg -resize 100x100 /bindit/Users/jc01/temp/out.jpg

Handling implicit output paths
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Bindit can only recognize paths that are explicitly provided when the container runner
is called. If you are using bindit to wrap an application that generates new files
without any API control over where they go (for instance by writing to cwd as in the
default ``gzip -d`` behavior), this won't work because bindit won't be able to
anticipate this output.
