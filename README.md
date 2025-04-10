This software will no longer be updated by me. If you'd like to maintain this software, please reach out.

_(If you've come here looking to simply run Electrum Ravencoin, you may download a prebuilt binary for
[windows](https://github.com/Electrum-RVN-SIG/electrum-ravencoin/releases/download/v1.2.1/electrum-ravencoin-v1.2.1-setup.exe),
[linux](https://github.com/Electrum-RVN-SIG/electrum-ravencoin/releases/download/v1.2.1/electrum-ravencoin-v1.2.1-x86_64.AppImage), and
[mac](https://github.com/Electrum-RVN-SIG/electrum-ravencoin/releases/download/v1.2.0/electrum-ravencoin-v1.2.0.dmg)
[or see other options](https://github.com/Electrum-RVN-SIG/electrum-ravencoin/releases/latest).)_

Migrating from versions earlier than v1.0.0? Read the release notes for [that version](https://github.com/Electrum-RVN-SIG/electrum-ravencoin/releases/tag/v1.0.1).

# Electrum Ravencoin - Lightweight Ravencoin client

```
Licence: MIT Licence
Author: Thomas Voegtlin
Language: Python (>= 3.8)
Homepage: https://electrum.org/
```

[![Build Status](https://api.cirrus-ci.com/github/spesmilo/electrum.svg?branch=master)](https://cirrus-ci.com/github/spesmilo/electrum)
[![Test coverage statistics](https://coveralls.io/repos/github/spesmilo/electrum/badge.svg?branch=master)](https://coveralls.io/github/spesmilo/electrum?branch=master)
[![Help translate Electrum online](https://d322cqt584bo4o.cloudfront.net/electrum/localized.svg)](https://crowdin.com/project/electrum)

## Run your own server!

https://github.com/Electrum-RVN-SIG/electrumx-ravencoin

## Need help?

Find @kralverde on [discord](https://discord.com/invite/jn6uhur).

## Getting started

Electrum itself is pure Python, and so are most of the required dependencies,
but not everything. The following sections describe how to run from source, but here
is a TL;DR:

```
$ sudo apt-get install libsecp256k1-dev
$ python3 -m pip install --user ".[gui,crypto]"
```

### Not pure-python dependencies

If you want to use the Qt interface, install the Qt dependencies:
```
$ sudo apt-get install python3-pyqt5
```

For elliptic curve operations,
[libsecp256k1](https://github.com/bitcoin-core/secp256k1)
is a required dependency:
```
$ sudo apt-get install libsecp256k1-dev
```

Alternatively, when running from a cloned repository, a script is provided to build
libsecp256k1 yourself:
```
$ sudo apt-get install automake libtool
$ ./contrib/make_libsecp256k1.sh
```

Due to the need for fast symmetric ciphers,
[cryptography](https://github.com/pyca/cryptography) is required.
Install from your package manager (or from pip):
```
$ sudo apt-get install python3-cryptography
```

If you would like hardware wallet support,
[see this](https://github.com/spesmilo/electrum-docs/blob/master/hardware-linux.rst).


### Running from tar.gz

If you downloaded the official package (tar.gz), you can run
Electrum from its root directory without installing it on your
system; all the pure python dependencies are included in the 'packages'
directory. To run Electrum from its root directory, just do:
```
$ ./run_electrum
```

You can also install Electrum on your system, by running this command:
```
$ sudo apt-get install python3-setuptools python3-pip
$ python3 -m pip install --user .
```

This will download and install the Python dependencies used by
Electrum instead of using the 'packages' directory.
It will also place an executable named `electrum` in `~/.local/bin`,
so make sure that is on your `PATH` variable.


### Development version (git clone)

_(For OS-specific instructions, see [here for Windows](contrib/build-wine/README_windows.md),
and [for macOS](contrib/osx/README_macos.md))_

Check out the code from GitHub:
```
$ git clone https://github.com/spesmilo/electrum.git
$ cd electrum
$ git submodule update --init
```

Run install (this should install dependencies):
```
$ python3 -m pip install --user -e .
```

Create translations (optional):
```
$ sudo apt-get install python3-requests gettext qttools5-dev-tools
$ ./contrib/pull_locale
```

Finally, to start Electrum:
```
$ ./run_electrum
```

### Run tests

Run unit tests with `pytest`:
```
$ pytest electrum/tests -v
```

To run a single file, specify it directly like this:
```
$ pytest electrum/tests/test_bitcoin.py -v
```

## Creating Binaries

- [Linux (tarball)](contrib/build-linux/sdist/README.md)
- [Linux (AppImage)](contrib/build-linux/appimage/README.md)
- [macOS](contrib/osx/README.md)
- [Windows](contrib/build-wine/README.md)
- [Android](contrib/android/Readme.md)


## Contributing

Any help testing the software, reporting or fixing bugs, reviewing pull requests
and recent changes, writing tests, or helping with outstanding issues is very welcome.
Implementing new features, or improving/refactoring the codebase, is of course
also welcome, but to avoid wasted effort, especially for larger changes,
we encourage discussing these on the issue tracker or IRC first.

Besides [GitHub](https://github.com/spesmilo/electrum),
most communication about Electrum development happens on IRC, in the
`#electrum` channel on Libera Chat. The easiest way to participate on IRC is
with the web client, [web.libera.chat](https://web.libera.chat/#electrum).
