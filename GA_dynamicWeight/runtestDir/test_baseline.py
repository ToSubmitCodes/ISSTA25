workspace = './testWorkSpace/baseline_workspace'
popSize = 50

import re,traceback,importlib
  
def initSeedpool(backend, clsName, argInfoList, allseeds):
    newAllRes = []
    allRes = {}
    for tc in allseeds:
        resSumy,resInfo = executeTupleWithBackends(clsName,tc,argInfoList,backend,workspace)
        allRes[tc] = (resInfo,resSumy)
        if resSumy != 'Crash':
            newAllRes.append(tc)
    return  newAllRes,allRes

def initMaxIter(argInfoList, baseLen):
    SpaceVolumn = 1
    for param in argInfoList:
        SpaceVolumn *= len(param['valueSpace'])
    maxIter = min(SpaceVolumn,1000+baseLen)
    return maxIter

def score(seedpool,allRes,argInfoList,keyParams):
    paramValueCount = {paramIndex:{v:0 for v in argInfoList[paramIndex]['valueSpace']} for paramIndex in range(len(argInfoList))}
    for testcase in allRes.keys():
        for i,v in enumerate(testcase):
            paramValueCount[i][v] += 1
    
    valueScore = {paramIndex:{v:0 for v in argInfoList[paramIndex]['valueSpace']} for paramIndex in range(len(argInfoList))}
    for paramIndex in range(len(argInfoList)):
        allV = argInfoList[paramIndex]['valueSpace']
        if len(allV) == 1:
            valueScore[paramIndex][allV[0]] = 1.0
        else:    
            for value in allV:
                valueScore[paramIndex][value] = (len(allRes)-paramValueCount[paramIndex][value])/(len(allRes)*(len(argInfoList[paramIndex]['valueSpace'])-1))
    
    scoreDict = {}
    for testcase in seedpool:
        s = 1
        for i,v in enumerate(testcase):
            base = 1.0 if i not in keyParams else 2.0
            s += valueScore[i][v]*base
        scoreDict[testcase] = s
    return scoreDict

def select(scoreDict):
    parents = []
    for testcase in scoreDict.keys():
        if random.random() < scoreDict[testcase]:
            parents.append(testcase)
    return parents

def mutate(testCase,argInfoList,keyParams):
    newTestCase = []
    for i,val in enumerate(testCase):
        mutationPossibility = 0.05 if i not in keyParams else 0.10
        if random.random() < mutationPossibility and len(argInfoList[i]['valueSpace']) > 1:
            paramValue = argInfoList[i]['valueSpace'].copy()
            paramValue.remove(val)
            newTestCase.append(random.choice(paramValue))
        else:
            newTestCase.append(val)
    return tuple(newTestCase)

def crossover(p1,p2,geneSet):
    newP1 = list(p1)
    newP2 = list(p2)
    for gene in geneSet:
        newP1[gene] = p2[gene]
        newP2[gene] = p1[gene]
    return tuple(newP1),tuple(newP2)

def extractControl(paramInfo,clsName):
    controlParams = set()
    for paramIndex,v in enumerate(paramInfo['ParamList'][clsName]):
        if v['name'] in paramInfo['controlAPDict'][clsName]:
            controlParams.add(paramIndex)
    return controlParams

def getShape(allRes,tc):
    return allRes[tc][0]['KR'][1]

def extractShape(tc1,tc2,allRes):
    shape1 = getShape(allRes,tc1)
    shape2 = getShape(allRes,tc2)
    if shape1 == shape2:
        return None
    diffParam = None
    for i,v in enumerate(tc1):
        if v != tc2[i]:
            if diffParam is not None:
                return None
            else:
                diffParam = i
    return diffParam            

def initShape(seedpool,allRes):
    allShapeParams=set()
    for tc1 in seedpool:
        for tc2 in seedpool:
            if tc1 == tc2:
                continue
            shapeParam = extractShape(tc1,tc2,allRes)
            if shapeParam is not None:
                allShapeParams.add(shapeParam)
    return allShapeParams

def contain(tc, part):
    for ind,v in part:
        if tc[ind] != v:
            return False
    return True

def valid(tc,allfailCores):
    for core in allfailCores:
        if contain(tc,core):
            return False
    return True

def extendFailCores(tc,allFailCores,allRes):
    initRes,ds,ss,Err = allRes[tc][0]['KR']
    if initRes != 'Success':
        msg = initRes
    elif not isinstance(ds,list):
        msg = ds 
    else:
        return allFailCores
    failCore = set([(i,v) for i,v in enumerate(tc)])
    if msg not in allFailCores.keys():
        allFailCores[msg] = failCore
    else:
        newCore = allFailCores[msg] & failCore
        if len(newCore) > 1:
            allFailCores[msg] = newCore
    return allFailCores

def extractFail(tc1,tc2):
    diffParam = None
    for i,v in enumerate(tc1):
        if v != tc2[i]:
            if diffParam is not None:
                return None
            else:
                diffParam = i
    return diffParam 

def extendShapeCores(tc,allFailCores,allRes):
    initRes,ds,ss,Err = allRes[tc][0]['KR']
    if not isinstance(ss,list):
        return allFailCores    
    ss = tuple(ss)
    failCore = set([(i,v) for i,v in enumerate(tc)])
    if ss not in allFailCores.keys():
        allFailCores[ss] = failCore
    else:
        newCore = allFailCores[ss] & failCore
        if len(newCore) > 1:
            allFailCores[ss] = newCore
    return allFailCores

def clsTest_ActGen(backend,clsName, paramInfo, seedpool):
    #initialize          
    argInfoList = paramInfo['ParamList'][clsName]
    SeedPool,allRes = initSeedpool(backend,clsName,argInfoList,seedpool)
    allFailCores = {}
    allShapeCores = {}
    # for tc in SeedPool:
    #     if allRes[tc][1] == 'Crash':
    #         allFailCores = extendFailCores(tc,allFailCores,allRes)
    #     else:
    #         allShapeCores = extendShapeCores(tc,allShapeCores,allRes)
    maxIter = initMaxIter(argInfoList, len(allRes))
    if maxIter == 0:
        return allRes
    print('maxIter: ',maxIter)
    controlParams = set()#extractControl(paramInfo,clsName)
    shapeParams = set()#initShape(SeedPool,allRes)
    
    ScoreDict = score(SeedPool,allRes,argInfoList,(controlParams | shapeParams))
    #start testing
    roundCnt = 0
    while(len(allRes) < maxIter and roundCnt < 100):
        print('Round: ',roundCnt)
        roundCnt += 1
            
        #crossover & mutation
        nextGeneration = [] 
        newPop = []
        tryCnt = 0
        while(len(nextGeneration) < popSize and tryCnt < 2000):
            tryCnt += 1
            p1,p2 = random.choices(list(ScoreDict.keys()),weights=list(ScoreDict.values()),k=2)
            crossPoint = random.randint(1,len(p1)-1)
            diffPSet = [paramIndex for paramIndex in (controlParams | shapeParams) if p1[paramIndex] != p2[paramIndex] ]
            if len(diffPSet) > 0:
                diffP = random.choice(diffPSet)
                allCross = set([diffP,crossPoint])
            else:
                allCross = [crossPoint]
            newP1,newP2 = crossover(p1,p2,allCross)
            for p in newP1,newP2:
                newP = mutate(p,argInfoList,(controlParams | shapeParams))
                nextGeneration.append(newP)
                newPop.append(newP)

           

        #eval
        
        for tc in nextGeneration:
            
            resSumy,resInfo = executeTupleWithBackends(clsName,tc,argInfoList, backend,workspace)
            allRes[tc] = (resInfo,resSumy)
            if len(allRes) >= maxIter:
                print(len(allRes),'no new tc')
                break
             
            # if resSumy != 'Crash':
            #     allShapeCores = extendShapeCores(tc,allShapeCores,allRes)
            #     for oldTc in allRes.keys():
            #         if allRes[oldTc][1] == 'Crash' or oldTc == tc:
            #             continue
            #         shapeParam = extractShape(tc,oldTc,allRes)
            #         if shapeParam is not None:
            #             shapeParams.add(shapeParam)
            # else:
            #     allFailCores = extendFailCores(tc,allFailCores,allRes)
            #     for oldTc in allRes.keys():
            #         if allRes[oldTc][1] == 'Crash' or oldTc == tc:
            #             continue
            #         shapeParam = extractFail(tc,oldTc)
            #         if shapeParam is not None:
            #             shapeParams.add(shapeParam)
            
        ScoreDict = score(newPop,allRes,argInfoList,(controlParams | shapeParams))

 
    print('#Test Cases: ',len(allRes))
    return allRes,{},{}
            
def BackendTest(backend,round):          
    paramInfo = dill.load(open(f'/mnt/data2/Users/sunshuo/ISSTA25/data/ParamInfo_{backend}.pickle','rb'))
    seedpool = dill.load(open(f'/mnt/data2/Users/sunshuo/ISSTA25/data/seedpool_{backend}.pickle','rb'))
    allRes = {}
    actParams = {}
    failCore = {}
    clsCnt = 0
    for clsName in seedpool.keys():
        print(f'{backend},{clsCnt}/{len(seedpool)},{clsName}')
        clsCnt += 1 
        testRes = clsTest_ActGen(backend, clsName, paramInfo, seedpool[clsName])
        if len(testRes) == 3:
            allRes[clsName],actParams[clsName],failCore[clsName] = testRes
    stopflag = Path(workspace+f'/flags/stopFlag_{backend}')
    stopflag.touch()
    dill.dump(allRes,open(f'../results/RQ2/res_{backend}_baseline_{round}.pickle','wb'))
    dill.dump(failCore,open(f'../results/RQ2/core_{backend}_baseline_{round}.pickle','wb'))
    json.dump(actParams,open(f'../results/RQ2/ap_{backend}_baseline_{round}.json','w'),indent=6)
                 
if __name__ == '__main__':
    import dill,json
    import time
    import random
    from executionUtils import executeTupleWithBackends
    from pathlib import Path
    import coverage
    from testCasesUtils import extractDcit
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('round',type=int)
    args = parser.parse_args()

    random.seed(args.round)
    start_time=time.time()
    for backend in ['KR']: 
        BackendTest(backend,args.round)
    endtime = time.time()
    print(f"Execution Time:{endtime-start_time}")                 
                    
                
                    
                            
                            
                    
                                                        
                                
                    
                
                            
                    
            
            
            
                