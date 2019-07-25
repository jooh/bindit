bindit - painless bind mounts for containers
============================================

Bindit is a docker wrapper that makes it easy to containerize applications with file
read/write requirements. 

Here is a typical bind mount pattern for a data science project:

.. code-block:: bash

   $ docker run -v "$HOME"/code:/code -v /drive/data:/data \
      -v /drive/results:/results myimage python /code/script.py \
      /data/input /results/

Notice that you need to define each bind manually, and you need to make sure your script
arguments point to the correct re-mapped paths inside the container. This can be a slow
and error-prone process, since there is no tab-completion of the re-mapped paths or
access to convenient environment variables.

With bindit, you simply enter the file paths as though the container script had access
to your native file system:

.. code-block:: bash

   $ bindit docker run myimage python "$HOME"/code/script.py /drive/data/input /drive/results/

Under the hood, bindit re-maps the paths and passes this command to docker. The above
command would look like this in native docker:

.. code-block:: bash

   $ docker run -v /Users/jc01/code:/bindit/Users/jc01/code \
      -v /drive:/bindit/drive myimage python /bindit/Users/jc01/code/script.py \
      /bindit/drive/data/input /bindit/drive/results/

This saves typing in interactive use. It also makes it easy to create command-line
interface wrappers that handle disk IO for container applications. For this purpose, we
supply a utility script generator: :doc:`bindit_partial <usage_partial>`.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation
   Usage: bindit <usage>
   Usage: bindit_partial <usage_partial>
   Module Reference <modules>
   contributing
   authors
   history

Indices and tables
==================
* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
