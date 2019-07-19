bindit - painless bind mounts for containers
============================================

Bindit is a docker wrapper that makes it easy to containerize applications with file
read/write requirements. 

Here is a typical bind mount pattern for a data analysis project:

.. code-block:: console

   docker run -v "$HOME"/code:/code -v /drive/data:/data \
      -v /drive/results:/results myimage python /code/script.py \
      /data/input /results/

Notice that you need to define each bind manually, and you need to make sure your script
arguments point to the correct re-mapped paths inside the container. This can be a slow
and error-prone process, since there is no tab-completion of the re-mapped paths or
access to convenient environment variables.

With bindit, you simply enter the file paths as though the script had access to your
native file system:

.. code-block:: console

   bindit docker run myimage python "$HOME"/code/script.py /drive/data/input /drive/results/

Under the hood, bindit re-maps the paths and passes this command to docker:

.. code-block:: console

   docker run -v /Users/jc01/code:/bindit/Users/jc01/code \
      -v /drive:/bindit/drive myimage python /bindit/Users/jc01/code/script.py \
      /bindit/drive/data/input /bindit/drive/results/

This is convenient for interactive use, and makes it trivial to generate shell script
wrappers that handle disk IO for container applications.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation
   usage
   Module Reference <modules>
   contributing
   authors
   history

Indices and tables
==================
* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
