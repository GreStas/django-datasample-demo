#!/usr/bin/env bash
for f in `find -regex  ".*/migrations/0.*.py"`; do rm $f ; done
