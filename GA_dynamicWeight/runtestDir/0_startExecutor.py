
import os,dill
from pathlib import Path
from multiprocessing import Process 


def executeWithBackend(backend,workspace,tail):
    import coverage
    cov = coverage.Coverage(source = ['./keras/src/layers'],concurrency='multiprocessing')
    cov.start()
    from testCasesUtils import executorDir
    stopflag = workspace+f'/flags/stopFlag_{backend}'
    inputFlag = workspace+'/flags/start'
    outputFlag = Path(workspace+'/flags/done')
    inputFile = workspace+f'/inputs/{backend}'
    outputFile = workspace+f'/outputs/{backend}'
    running  = workspace+'/running'
    for fileName in [stopflag,inputFlag,inputFile,outputFile,outputFlag,running]:
        if os.path.exists(fileName):
            os.remove(fileName)
    while(True):
        if os.path.exists(stopflag):
            break
        if os.path.exists(inputFlag):
            clsName,argDict = dill.load(open(inputFile,'rb'))
            os.remove(inputFile)
            while (True):
                try:
                    os.remove(inputFlag)
                    break
                except Exception as e:
                    print(str(e))
            try:
                res = executorDir[backend](clsName,argDict)
                dill.dump(res,open(outputFile,'wb'))
            except Exception as e:
                print(str(e))
            outputFlag.touch()
    print('Done')
    cov.stop()
    cov.json_report(outfile=f'../data/cov/cov_{backend}{tail}.json')
    return 



if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('workspace', type=str)
    parser.add_argument('suffix', type=str)
    

    args = parser.parse_args()  
    BACKENDS = ['KR']#,'torch']
    processes =[]
    for backend in BACKENDS:
        p = Process(target=executeWithBackend,args=(backend,args.workspace,args.suffix))
        p.start()
  