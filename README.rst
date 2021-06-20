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

    $ python -m pip install frontend-editables

Basic usage
-----------

.. code-block:: python

    import sysconfig

    import frontend_editables

    path_mapping = ...  # Will have been returned by the backend.
    installed_files = frontend_editables.install(
        "name",
        sysconfig.get_path("purelib"),
        path_mapping,
        frontend_editables.EditableStrategy.lax,
    )
    # Then append the ``installed_files`` to the distribution's ``RECORD``,
    # optionally by passing ``append_to_record=<path to RECORD>`` to ``install``.

CLI
~~~

*frontend_editables* includes an extremely hacky CLI which serves a stopgap
until editable installation is standardised.  You can use this in place
of ``python -m pip install -e ...``.  The CLI supports all of the same
layouts and installation methods supported by the library.  Some examples:

* To install a project with a single module ``foo.py``, symlinking it:
  ``python -m frontend_editables.transitional_cli --strategy strict foo.py foo.py``.
* To install a project with a package ``foo``, located in ``<project-root>/src/foo``,
  with the aid of a ``pth`` file:
  ``python -m frontend_editables.transitional_cli --method pth_file src/foo foo``.
* To install a project with multiple packages at different locations:
  ``python -m frontend_editables.transitional_cli {src/,}foo {lib/,}bar``

Editable distributions can be uninstalled with pip as normal.

.. code-block::

    usage: python -m frontend_editables.transitional_cli [-h]
                                                         [--method {symlink,redirect,pth_file}]
                                                         [--strategy {lax,strict}]
                                                         [--spec SPEC]
                                                         path_pairs
                                                         [path_pairs ...]

    Wacky transitional editable project installer.

    positional arguments:
      path_pairs            pairs of path on disk and corresponding path in
                            the virtual wheel (posix)

    optional arguments:
      -h, --help            show this help message and exit
      --method {symlink,redirect,pth_file}
                            editable installation method to use (default:
                            None)
      --strategy {lax,strict}
                            editable strategy to follow (default: lax)
      --spec SPEC           requirement specifier (default: .)

Contributing
------------

You can use *frontend-editables* to install *frontend-editables* for development::

    $ PYTHONPATH=src python -m frontend_editables.transitional_cli \
        --spec .[test] {src/,}frontend_editables

Before opening a merge request, install `nox <https://github.com/theacodes/nox>`__
and run ``nox``.  The type checking step has an external dependency on ``npm``.

Happy hacking!
