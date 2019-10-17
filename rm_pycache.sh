#!/usr/bin/env bash
for f in `find -regex  ".*/__pycache__/.*.pyc"`; do rm $f ; done
