#!/bin/sh
curl -L https://files.sloppy.io/sloppy-`uname -s`-`uname -m` > /tmp/sloppy
sudo cp /tmp/sloppy /usr/local/bin/sloppy
sudo chmod +x /usr/local/bin/sloppy
sloppy version
