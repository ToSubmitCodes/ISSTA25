import dill,os
from pathlib import Path

def assignTask(clsName,argDict,backend,workspace):
    #workspace = f'../test_Phase/{backend}_workspace'
    inputFile = workspace+f'/inputs/{backend}'
    dill.dump((clsName,argDict),open(inputFile,'wb'))
    inputFlag = workspace+'/flags/start'
    inputFlag = Path(inputFlag)
    inputFlag.touch()

def collectRes(backend,workspace):
    ResSet={}
    #workspace = f'../test_Phase/{backend}_workspace'
    outputFlag = workspace+'/flags/done'
    while(True):
        if os.path.exists(outputFlag):
            outputFile = workspace+f'/outputs/{backend}'
            ResSet[backend] = dill.load(open(outputFile,'rb'))
            os.remove(outputFile)
            while True:
                try:
                    os.remove(outputFlag)
                    break
                except Exception as e:
                    print(str(e))
                    pass
            break
    res = analyzeResults(ResSet)
    return res,ResSet

def analyzeResults(resSet):
    #Check1. Invalid
    for k in resSet.keys():
        if not isinstance(resSet[k][1],list):
            return 'Crash'
    return 'Pass'
    


def executeTupleWithBackends(clsName,argTuple,argList,backend,workspace):
    #execute TestCases
    argDict = [(argList[i]['name'],arg) for i,arg in enumerate(argTuple)]
    assignTask(clsName,argDict,backend,workspace)
    #collect Result
    res,ResSet = collectRes(backend,workspace)
    return res,ResSet