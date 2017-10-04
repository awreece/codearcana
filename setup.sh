#!/bin/bash

set -e

mkdir -p output
virtualenv venv
(source venv/bin/activate && pip install -r requirements.txt)
git submodule update --init --recursive
