.. highlight:: shell

============
Installation
============

Standalone binaries
-------------------

We provide self-contained binaries for major systems (Linux, Mac, soon Windows?) for
each of our `Github releases`_. This is the preferred route for most users since there
is no risk of interactions with your current Python environment.

Stable python package
---------------------

If you prefer to install bindit as a python package, you can install the current release
with `pip`_:

.. code-block:: console

    pip install bindit

.. _pip: https://pip.pypa.io

Development version
-------------------

The bleeding edge version of bindit can be pip installed from the `Github repo`_ like so:

.. code-block:: console

   pip install git+git://github.com/jooh/bindit.git


Editable version
----------------

For contributors, you can install an editable version of bindit by first cloning the
repository, then pip installing:

.. code-block:: console

    git clone git://github.com/jooh/bindit
    cd bindit
    pip install -e .

.. _Github repo: https://github.com/jooh/bindit
.. _Github releases: https://github.com/jooh/bindit/releases
