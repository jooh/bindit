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
the container image arguments, and rebasing these as necessary onto new bind mounts.

* Free software: MIT license
* Documentation: https://bindit.readthedocs.io.


Features
--------

* Detects references to relative or absolute path on local file system, bind mounts
  directories as necessary to make the paths available inside the container, and rebases
  the paths to point to the new mounts.
* Avoids interfering with or duplicating user-defined bind mounts
* absonly mode: ignore relative paths (useful if you have a `python` directory in your
  cwd...)
* dryrun mode: return a re-formatted container runner command (useful for distributed
  execution on HPCs, testing)


Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
