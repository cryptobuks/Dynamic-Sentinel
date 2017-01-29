#!/bin/bash
set -evx

mkdir ~/.darksilkcore

# safety check
if [ ! -f ~/.darksilkcore/.darksilk.conf ]; then
  cp share/darksilk.conf.example ~/.darksilkcore/darksilk.conf
fi