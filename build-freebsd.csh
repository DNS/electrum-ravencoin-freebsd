#!/bin/csh

# RUN AS ROOT

set curdir = `pwd`

setenv CC /usr/local/bin/gcc
setenv CXX /usr/local/bin/g++
setenv AR /usr/local/bin/ar
setenv LD /usr/local/bin/ld
setenv LINKER /usr/local/bin/ld
setenv NM /usr/local/bin/nm
setenv OBJDUMP /usr/local/bin/objdump
setenv RANLIB /usr/local/bin/ranlib

pkg install -y 7-zip wget py39-pip
pkg install -y py39-aiohttp-socks py39-aiohttp py39-aiorpcX py39-attrs py39-bitstring py39-certifi py39-dnspython py39-httplib2 py39-jsonrpclib-pelix py39-pbkdf2 py39-protobuf py39-QDarkStyle py39-qrcode py39-requests py39-secp256k1 py39-sqlite3 py39-bitbox02 py39-btchip-python py39-ckcc-protocol py39-hidapi py39-keepkey py39-trezor py39-cryptography py39-setuptools py39-qt5-pyqt py39-sip py39-cython py39-aiofiles
pip-3.9 install -y multiformats aioipfs ipfs-car-decoder 

#pip-3.9 install -y kawpow
pip-3.9 uninstall -y kawpow

cd ..
wget -cnd https://codeload.github.com/DNS/kawpow/zip/refs/heads/master -O kawpow-master.zip
7z x kawpow-master.zip
cd kawpow-master

python3.9 setup.py clean
rm -rf build/*, dist/*
python3.9 setup.py install --verbose

cd ..
cd $curdir
./run_electrum






