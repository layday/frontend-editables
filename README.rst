frontend-editables
==================

*frontend-editables* is a library for installing Python packages for development,
originally created as a proof of concept for
`PEP 662 <https://www.python.org/dev/peps/pep-0662/>`__.
It supports installing prospective "editable" wheels
using one of four different methods:

* "Lax" symlinking

  Symlinks *top-level* packages and modules only – the
  contents of packages can differ from those in the published distribution.

* "Strict" symlinking

  Symlinks *files* only, faithfully mirroring
  the structure of packages as they would appear in the published distribution.

* Redirector

  Generates a custom module finder which is used to load packages and modules
  from another location on disk and
  is injected in the ``sys.meta_path`` on start-up using a dynamic ``.pth`` file.
  This works similarly to the "lax" symlinking method –
  for more details, see `editables <https://github.com/pfmoore/editables>`__.

* Static ``.pth`` file

  Creates a ``.pth`` file which lists directories containing the distribution's
  packages and modules, to add to the Python path.
  This will expose miscellaneous packages and modules which might be
  in the same folder.

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
        [frontend_editables.PthFileInstaller],
        "name",
        sysconfig.get_path("purelib"),
        path_mapping,
    )
    # Then append the ``installed_files`` to the distribution's ``RECORD``,
    # optionally by passing ``append_to_record=<path to RECORD>`` to ``install``.

The paths must map would-be wheel files to their absolute paths on disk;
folder paths are invalid.

CLI
~~~

*frontend_editables* includes an extremely hacky CLI which serves a stopgap
until editable installation is standardised.  You can use this in place
of ``python -m pip install -e ...``.  The CLI supports all of the same
layouts and installation methods supported by the library.  Some examples:

* To install a project with a single module ``foo.py``, symlinking it:
  ``python -m frontend_editables.transitional_cli -m strict_symlink foo.py foo.py``.
* To install a project with a package ``foo``, located in ``<project-root>/src/foo``,
  with the aid of a ``pth`` file:
  ``python -m frontend_editables.transitional_cli -m pth_file src/foo foo``.
* To install a project with multiple packages at different locations, using the
  redirecting path finder:
  ``python -m frontend_editables.transitional_cli -m redirector {src/,}foo {lib/,}bar``

Editable distributions can be uninstalled with pip as normal.

.. code-block::

    usage: python -m frontend_editables.transitional_cli [-h] --method
                                                         {lax_symlink,pth_file,redirector,strict_symlink}
                                                         [--spec SPEC]
                                                         path_pairs [path_pairs ...]

    Wacky transitional editable project installer.

    positional arguments:
      path_pairs            pairs of path on disk and corresponding path in the
                            virtual wheel (posix)

    optional arguments:
      -h, --help            show this help message and exit
      --method {lax_symlink,pth_file,redirector,strict_symlink}, -m {lax_symlink,pth_file,redirector,strict_symlink}
                            editable installation method to use (default: None)
      --spec SPEC           requirement specifier (default: .)

Contributing
------------

You can use *frontend-editables* to install *frontend-editables* for development::

    $ PYTHONPATH=src python -m frontend_editables.transitional_cli \
        --spec .[test] {src/,}frontend_editables

Before opening a merge request, install `nox <https://github.com/theacodes/nox>`__
and run ``nox``.  The type checking step has an external dependency on ``npm``.

Happy hacking!
