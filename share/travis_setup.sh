#!/bin/bash
set -evx

mkdir ~/.dynamic

# safety check
if [ ! -f ~/.dynamic/.dynamic.conf ]; then
  cp share/dynamic.conf.example ~/.dynamic/dynamic.conf
fi
