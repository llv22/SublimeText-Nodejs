#!/bin/sh
# see http://www.huzs.net/?p=920
rsync -avr . --progress /Users/llv22/Library/Application\ Support/Sublime\ Text\ 2/Packages/Nodejs/* --exclude Readme.md
rm /Users/llv22/Library/Application\ Support/Sublime\ Text\ 2/Packages/Nodejs/*.pyc
rm /Users/llv22/Library/Application\ Support/Sublime\ Text\ 2/Packages/Nodejs/lib/*.pyc
