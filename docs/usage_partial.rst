=====================
Usage: bindit_partial
=====================

The purpose of bindit_partial is to create command-line interfaces (CLI) for containerized
applications. It typically does this by wrapping ``bindit``.

Motivating example
------------------

Let's say you want to work with `Freesurfer`_, a neuroimaging package that works with a
directory where your data and a license file (*I know*) live. There might also be
additional config files that you want to make available inside the container. This can
result in pretty hairy docker run commands:

.. code-block:: bash

   $ docker run -v /your/subjects/dir:/opt/freesurfer/ \
      -v /path/to/other:/other \
      freesurfer/freesurfer:6.0 recon-all -subjid bert -all \
      -expert /other/file

``bindit`` can help make this less annoying, but you will still have to use a manual
bind mount to handle Freesurfer's implicit file IO requirements (the container will look
for the subject ``bert`` and a license file in ``/opt/freesurfer``). These inputs are
going to be the same for any use case, so it makes more sense to bake them into a CLI
wrapper script.  This is where bindit_partial comes in:

.. _Freesurfer: https://surfer.nmr.mgh.harvard.edu

.. code-block:: bash

   $ bindit_partial bindit --dryrun docker run -v /your/subjects/dir:/opt/freesurfer/ \
      freesurfer/freesurfer:6.0 > freesurfer_wrap

If we inspect ``freesurfer_wrap`` we find the following shell script:

.. code-block:: bash

   $ cat freesurfer_wrap
   #!/bin/bash
   bindit --dryrun docker run -v /your/subjects/dir:/opt/freesurfer/ freesurfer/freesurfer:6.0 "$@"

Now we make the CLI executable and call it:

.. code-block:: bash

   $ chmod u+x freesurfer_wrap
   $ ./freesurfer_wrap recon-all -subjid sub -all -expert /path/to/other/file

The output of this short command is very similar ro the docker command  we started with,
(to actually execute this example instead, you'd want to remove the ``--dryrun`` flag
above):

.. code-block:: bash

   docker run -v /your/subjects/dir:/opt/freesurfer/ \
      -v /path/to/other:/bindit/path/to/other \
      freesurfer/freesurfer:6.0 recon-all -subjid bert -all \
      -expert /bindit/path/to/other/file

Notice that the pre-specified manual bind of ``/your/subjects/dir`` persists, while the
new ``path/to/other/file`` we specified when calling the script has been re-mapped to be
available inside the container.

Default and optional behavior
-----------------------------

bindit_partial's default behavior is to generate a bash script, which gets passed to
standard out (so you can e.g. pipe it to a file with ``bindit_partial [args] >
wrapper_script``. You can change this behavior with the following flags:

-output_file
~~~~~~~~~~~~

Output the shell script to the specified file path instead of standard out.

-shebang
~~~~~~~~

The shell interpreter directive (default: ``#!/bin/bash``). Useful for generating shell
wrappers in other script languages.

-vararg_pattern
~~~~~~~~~~~~~~~

The shell pattern for passing all input arguments to the wrapped container (default
``"$@"``). In csh or tcsh you might use ``$argv`` instead.

