=========
crossroad
=========

--------------------------------------
Cross-Compilation Environment Toolkit.
--------------------------------------

:Date: 2013-09-12
:Version: 0.1
:Manual section: 1
:Author: jehan@girinstud.io

SYNOPSIS
========

**crossroad** [TARGET] [--help] [--version] [--list-all]

DESCRIPTION
===========

**Crossroad** is a developer tool to prepare your shell environment for Cross-Compilation.

OPTIONS
=======

--version                               Show program's version number and exit
-h, --help                              Show the help message and exit. If a *TARGET* is provided, show information about this platform.
-l, --list-all                          List all known platforms

EXAMPLES
========

If you wish to know which cross-compilation environment is settable, run::

    $ crossroad -l
    crossroad, version 0.3
    Available platforms:
    w64                  Windows 64-bit

    Uninstalled platforms:
    w32                  Windows 32-bit

To get more details about the `w64` platform::

    $ crossroad -h w64
    w64: Setups a cross-compilation environment for Microsoft Windows operating systems (64-bit).

    Installed language list:
    - Ada
    - C
    - C++
    - OCaml
    Uninstalled language list:
    - Objective C         Common package name providing the feature: gobjc++-mingw-w64-x86-64
    - fortran             Common package name providing the feature: gfortran-mingw-w64-x86-64

So we can likely compile ``Ada``, ``C``, ``C++`` and ``OCaml`` programs in this environment. Ability to compile Objective C programs for
instance is missing. A package named ``gobjc++-mingw-w64-x86-64`` would probably provide the feature (this package may be named differently
depending on your distribution).

If you want to know why the `w32` platform won't be setup::

    $ crossroad -h w32
    w32: Setups a cross-compilation environment for Microsoft Windows operating systems (32-bit).

    Not available. Some requirements are missing:
    - 686-w64-mingw32-gcc [package "gcc-mingw-w64-i686"] (missing)
    - i686-w64-mingw32-ld [package "binutils-mingw-w64-i686"]

So you will want to install the package ``gcc-mingw-w64-i686`` to be able to cross-compile for Windows 32-bit.

Now let's enter a Windows 64-bit cross-compilation environment::

    $ crossroad w64

You will be greated by a message telling you the basics information to know, likely that you should use `$PREFIX` and `$HOST` as compilation
options. Also your shell should stay the same (currently on bash is supported though), with all your usual customization.
Various environment variables will be updated to find the right binary alternatives, libraries, etc. in particular your `$PATH`, `$CPATH`,
`pkg-config` environment variables, `$LD_LIBRARY_PATH` and so on.

In order for you not to mistake several opened shells, a crossroad prompt will have a small red ``w64✘`` at the start. For instance if your
prompt is usually `user@host ~/some/path $`, your crossroad prompt will be `w64✘ user@host ~/some/path $`.

Once in a crossroad environment, you will be able to install various packages. Let's say your app requires gtk2 and zlib. You would run::

    $ crossroad -i gtk2-devel zlib-devel

All dependencies of these packages will be installed.
Note 0: this specific option can only be run inside a running crossroad shell because it will install packages for this specific shell.
Note 1: there is no way to query and search packages "*for the moment*" but this is a planned feature. Currently `crossroad` uses pre-compiled
package repositories from the OpenSuse cross-compilation. There is plan to use other pre-compiled repositories alongside, provided they are
safe.
Note 2: if you are looking for a specific dependency which does not exist, or not in the right version, you may have to compile it yourself
in the project.

Now let's assume I want to compile my project. I enter the software and run the configure script this way::

    $ cd my_project
    $ ./configure --prefix=$PREFIX --host=$HOST
    $ make
    $ make install

And you got it! That's it, that's all, you just compiled for Windows 64-bit. Easy right? Basically you always need to specify the given
$PREFIX because you don't want to mess your normal environment, and $HOST is the way you tell the configure script which version of your
compiler, linker and of various other tools to use. `crossroad` did quite a bit much that you can't see by setting all the environment
variables right, so that for instance the `pkg-config` tool finds the right Windows libraries, and that the linker does not try to link
against a Linux library (which would fail obviously badly).

Enjoy!