#!/bin/bash

sudo apt-get install -y python3 python3-pip python3-dev gcc
pip3 install -r requirements.txt
python3 -m spacy download en_core_web_sm

