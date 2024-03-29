#!/bin/bash
python3 ../comp/fjlc.py simtest.oats >simtest.s
python3 ../assem/fj_as.py simtest.s

