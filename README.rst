frontend-editables
==================

This is a PoC of an editable library which operates on the frontend
`as discussed <https://discuss.python.org/t/discuss-tbd-editable-installs-by-gaborbernat/9071>`__
on the Python packaging Discourse.
It supports installing prospective editable distributions
using three different methods (symlink, redirector and ``.pth`` files)
and two strategies (lax and strict).
The strict strategy reproduces the distribution structure faithfully
whereas the lax strategy exposes the contents of packages as they appear on disk.
The input must be a mapping of would-be wheel file paths and absolute paths on disk;
folder paths are invalid.
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

CLI
---

*frontend_editables* includes an extremely hacky CLI which serves a stopgap
until editable installation is standardised::

    $ python -m frontend_editables.transitional_cli
    usage: transitional_cli.py [-h] [--method {symlink,redirect,pth_file}] [--strategy {lax,strict}] path_pairs [path_pairs ...]

    Wacky transitional editable project installer.

    positional arguments:
    path_pairs            pairs of path on disk and corresponding path in the virtual wheel (posix)

    optional arguments:
    -h, --help            show this help message and exit
    --method {symlink,redirect,pth_file}
                            editable installation method to use (default: None)
    --strategy {lax,strict}
                            editable strategy to follow (default: lax)
