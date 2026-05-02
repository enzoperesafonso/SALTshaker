Installation
============

Requirements
------------

``saltshaker`` requires **Python 3.12** or newer. It depends on several core astronomical and scientific packages:

* ``astropy`` (>=6.1.1)
* ``astroplan`` (>=0.10.1)
* ``numpy`` (>=1.26.4)
* ``scipy`` (>=1.14.0)
* ``pandas`` (>=2.3.3)
* ``matplotlib`` (>=3.10.8)

Standard Installation
---------------------

You can install the package via ``pip``:

.. code-block:: bash

    pip install saltishaker

.. note::
    While the package is listed on PyPI as ``saltishaker``, it is imported in Python as ``saltshaker``. All examples in this documentation use the ``saltshaker`` import.

Alternatively, you can install directly from the GitHub repository:

.. code-block:: bash

    pip install git+https://github.com/enzoperesafonso/saltshaker.git

Development Installation
------------------------

If you want to contribute to ``saltshaker`` or modify the source code, we recommend using `Poetry <https://python-poetry.org/>`_ to manage your environment.

1. Clone the repository:

   .. code-block:: bash

       git clone https://github.com/enzo-peres-afonso/saltshaker.git
       cd saltshaker

2. Install dependencies (including development tools like ``pytest``, ``ruff``, and ``sphinx``):

   .. code-block:: bash

       poetry install

3. Activate the virtual environment:

   .. code-block:: bash

       poetry shell

4. Run the tests to ensure everything is working:

   .. code-block:: bash

       pytest
