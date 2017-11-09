#!/bin/sh

for png in `find addons/game.controller.* -name "*.png"`;
do
  echo "crushing $png"
  pngcrush -brute -ow "$png"
done
