frontend-editables
==================

This is a PoC of an editable library which operates on the frontend
`as discussed <https://discuss.python.org/t/discuss-tbd-editable-installs-by-gaborbernat/9071>`__
on the Python packaging Discourse.
It supports installing prospective editable distributions
using two different modes (symlink and ``.pth`` files) and two strategies (lax and strict).
The strict strategy reproduces the distribution structure faithfully
whereas the lax strategy exposes the contents of packages as they appear on disk.
This library does not manipulate data files or scripts because I consider that
to be an unnecessary complication in the context of editable installation.

Installation
------------

.. code-block::

    python -m pip install git+https://github.com/layday/frontend-editables

Basic usage
-----------

.. code-block:: python

    import sysconfig

    import frontend_editables

    path_mapping = ...  # Will have been returned by the backend.
    installed_files = frontend_editables.install(
        sysconfig.get_path("purelib"),
        path_mapping,
        frontend_editables.EditableStrategy.lax,
    )
    # Then append the ``installed_files`` to the distribution's ``RECORD``,
    # optionally by passing ``append_to_record=<path to RECORD>`` to ``install``.
