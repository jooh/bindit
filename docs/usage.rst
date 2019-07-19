=====
Usage
=====

Bindit is a command-line application. The basic usage is to prepend `bindit` to the
container runner command you would ordinarily use. For example, if you wanted to use a
docker container to list the contents of your current home directory you might do
something like this on a unix-based system (Linux, OS X):

.. code-block:: console

    docker run -v "$HOME":/data alpine:latest ls /data

With bindit, the bind mount is created automatically by detecting the file path
reference in the container image arguments. You can basically pretend that the container
has access to your host file system, so this works:

.. code-block:: console

    bindit docker run alpine:latest ls "$HOME"

Bindit mounts are mapped to a new /bindit root inside the container to avoid clobbering
directories that might be necessary for the container to run (in particular, messing
with the container home directory often breaks things). If we set the dryrun flag we
can see the mapping:

.. code-block:: console

   bindit --dryrun docker run alpine:latest ls "$HOME"

Yields something like this:

.. code-block:: console

   docker run -v /Users/jc01:/bindit/Users/jc01 alpine:latest ls /bindit/Users/jc01

Turning the above examples into a re-usable application that can be added to your path
is easy. Here is a minimal example of an ImageMagick interface:

.. code-block:: bash
   
   #!/bin/bash
   bindit docker run pokidov/imagemagick "$@"

Any specified input and output files will be. Oh wait. Do we require that the path
exists? We sure do. Bollocks. Ok, so for sure we cannot support mkdir -p style creation
of arbitrary directories. I guess what we *can* do is support cases where the directory
exists even if the file currently does not.

Default and optional behavior
-----------------------------

Bindit's default behavior can be controlled with the following flags:

-a, --absonly
~~~~~~~~~~~~~

Only auto-bind absolute paths. Useful if you call bindit from a folder that has
sub-folders which shadow binaries inside the container (`python` is a frequent offender
for me).

-d, --dryrun
~~~~~~~~~~~~

Return a formatted shell command without invoking container runner. Useful for
debugging, and when you want to defer running the container to a different context (for
instance, HPC job submission).

Combining user-defined and automatic binds
------------------------------------------

We have seen that bindit defaults to creating new bind mounts in the /bindit directory
inside the container. But bindit also detects user-specified binds, and will use them
whenever possible (for instance, when the user-specified bind is a parent of the input
path):

.. code-block:: console

    mkdir -p foo/bar
    bindit --dryrun docker run -v $(PWD):/container alpine:latest ls foo

Produces something like

.. code-block:: console

   docker run -v /Users/jc01/temp:/container alpine:latest ls /container/foo

Limitations
-----------

There are limitations to what paths bindit can detect automatically. The workaround for
these is typically to use absolute paths or to specify manual binds.

Specifying output paths
~~~~~~~~~~~~~~~~~~~~~~~
Bindit can only detect *relative* paths when they exist. *Absolute* paths work either way. This can trip you up when calling a container application with an argument that defines the output file path. These must always be absolute (unless it's a folder, or you are otherwise modifying or overwriting an existing path).

This can lead to seemingly baffling behavior. For example, suppose we want to use
ImageMagick to downsize an image and save it to a new name. We use --dryrun to preview
what the final docker run command will look like:

.. code-block:: console

   touch in.jpg
   rm -f out.jpg
   bindit --dryrun docker run dpokidov/imagemagick in.jpg -resize 100x100 out.jpg

The input image has been re-mapped correctly, but the output image hasn't because it
doesn't exist yet:

.. code-block:: console

   docker run -v /Users/jc01/temp:/bindit/Users/jc01/temp dpokidov/imagemagick \
      /bindit/Users/jc01/temp/in.jpg -resize 100x100 out.jpg

If we instead specify an absolute output path, everything works better:

.. code-block:: console

   bindit --dryrun docker run dpokidov/imagemagick in.jpg -resize 100x100 "$PWD"/out.jpg

Now both in.jpg and out.jpg get re-mapped to the correct locations:

.. code-block:: console

   docker run -v /Users/jc01/temp:/bindit/Users/jc01/temp dpokidov/imagemagick \
      /bindit/Users/jc01/temp/in.jpg -resize 100x100 /bindit/Users/jc01/temp/out.jpg

Handling implicit output paths
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Bindit can only recognize paths that are explicitly provided when the container runner
is called. If you are using bindit to wrap an application that generates new files
without any API control over where they go (for instance by writing to cwd as in the
default `gzip -d` behavior), this won't work because bindit won't be able to anticipate
this output.
