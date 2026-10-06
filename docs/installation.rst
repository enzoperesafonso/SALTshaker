Installation
============

Requirements
------------

``saltshaker`` requires **Python 3.12** or newer. It depends on several core astronomical and scientific packages:

* ``astropy`` (>=6.1.1)
* ``astroplan`` (>=0.10.1)
* ``numpy`` (>=1.26.4)
* 
Standard Installation
---------------------

You can install the package via ``pip``:

.. code-block:: bash

    pip install saltishaker

Optional extras: ``saltishaker[plot]`` (matplotlib, for ``saltshaker.plotting``) and ``saltishaker[examples]`` (matplotlib and pandas, used by the documentation examples).

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

       git clone https://github.com/enzoperesafonso/saltshaker.git
       cd saltshaker

2. Install dependencies (including development tools like ``pytest`` and ``ruff``, plus plotting and docs extras):

   .. code-block:: bash

       poetry install --with dev --extras "plot docs"

3. Activate the virtual environment:

   .. code-block:: bash

       poetry shell

4. Run the tests to ensure everything is working:

   .. code-block:: bash

       pytest

5. (Optional) Build the documentation:

   .. code-block:: bash

       sphinx-build -b html docs docs/_build/html
