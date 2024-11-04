allTails = ['baseline', 'complete', 'noFail', 'noShape' ,'noControl', 'onlyShape' ,'onlyControl' ,'onlyFail']

text = """#!/usr/bin/bash

rootDir=./testWorkSpace
logDir=../log
tail=%s
for round in 1 2 3 4 5
do
nohup python 0_startExecutor.py ${rootDir}/${tail}_workspace ${tail}_${round} &
sleep 10
python test_${tail}.py ${round} >> ${logDir}/${tail}_${round}_log.txt 
done"""

for tail in allTails:
    f=open(f'./run_{tail}.sh','w')
    f.write(text % tail)
    f.close()