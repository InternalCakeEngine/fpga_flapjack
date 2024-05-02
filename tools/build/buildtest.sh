#!/bin/bash
fn=`filename -r $1`
python3 ../comp/fjlc.py $fn.oats >$fn.s
python3 ../assem/fj_as.py $fn.s

