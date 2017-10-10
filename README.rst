======
Sheets
======


.. image:: https://img.shields.io/pypi/v/sheets.svg
        :target: https://pypi.python.org/pypi/sheets

.. image:: https://img.shields.io/travis/ianb/sheets.svg
        :target: https://travis-ci.org/ianb/sheets

.. image:: https://readthedocs.org/projects/sheets/badge/?version=latest
        :target: https://sheets.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status

.. image:: https://pyup.io/repos/github/ianb/sheets/shield.svg
     :target: https://pyup.io/repos/github/ianb/sheets/
     :alt: Updates


Like an interpreter / spreadsheet. More just like an interpreter now. Inspired/reacting to Jupyter Notebooks.

* Free software: MIT license

Features
--------

* Rich HTML representations of objects
* AST parsing/rewriting to show information
* [Command interface](https://martinfowler.com/bliki/CommandOrientedInterface.html) between client and server

Goals
-----

See [TODO](TODO.md) for some short-term goals.

* Understand the dependency graph between cells. So if Cell 3 uses a variable or function defined in Cell 1, then we'd like to understand that changes to Cell 1 might invalidate Cell 3.
* Do "experiments" in cells.  E.g., try something with some parameters (or even code/functions), and save the result for future comparison. (This is particularly inspired by use cases in AI and maybe data analysis, where there's not a "right" answer, but several possible approaches, often expensive to test.)
* Allow inspection of how the runtime object and process. E.g., peek at objects that are otherwise temporary or inside closures. Make it easier to get a feel for code that handles objects you aren't familiar with.

Credits
---------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
