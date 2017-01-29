#!/bin/bash
set -evx

mkdir ~/.darksilk

# safety check
if [ ! -f ~/.darksilk/.darksilk.conf ]; then
  cp share/darksilk.conf.example ~/.darksilk/darksilk.conf
fi