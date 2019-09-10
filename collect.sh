#!/bin/bash

# Adds logging to the python script
python3 collect.py "$@" 2>&1 | tee -a collect.log
