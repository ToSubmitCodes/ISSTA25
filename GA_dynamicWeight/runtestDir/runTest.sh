#!/usr/bin/bash

rootDir=./testWorkSpace

for tail in complete noFail noShape noControl baseline # onlyShape onlyControl onlyFail 
do
nohup bash run_${tail}.sh &
done