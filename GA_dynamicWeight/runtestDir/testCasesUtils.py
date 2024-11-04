import dill, importlib
from utils import NLayer,NList,NDict,NTensor,NDtype
from keras.src.backend.common.keras_tensor import KerasTensor
import numpy as np
from keras.src.dtype_policies.dtype_policy import FloatDTypePolicy
import json
import traceback
import re
from torch import Tensor
import torch

NSMapDict = {'KR':'keras.layers','torch':'torch.nn'}

def getValue(v,backend):
    if isinstance(v,NDtype):
        return FloatDTypePolicy('float32')
    if isinstance(v, NLayer):
        return None
    elif isinstance(v,NList):
        rv = []
        for e in v.l:
            rv.append(getValue(e,backend))
        return rv
    elif isinstance(v,NDict):
        rv = {}
        for k in v.d.keys():
            rv[k] = getValue(v.d[k],backend)
        return rv
    elif isinstance(v,NTensor):
        if None in v.s:
            return KerasTensor(shape=list(v.s))
        else:
            if backend == 'torch':
                return Tensor(np.random.rand(*list(v.s)))
            else:
                return np.random.rand(*list(v.s))
    else:
        return v

def extractDcit(rawArgDict,backend):
    resArgDict={'init':{},'call':{}}
    for k,v in rawArgDict:
        funcName,argName = k.split('_',1)
        assert funcName in resArgDict.keys(), f'funcName not exists: {funcName}'
        assert not argName in resArgDict[funcName].keys(), f'duplicated argName:{argName}'
        resArgDict[funcName][argName] = getValue(dill.loads(v),backend)
    return resArgDict

def extractErrmag(msg):
    pattern = re.compile('File \"(.*)\"(.*)\n(.*)\n')
    results = re.findall(pattern,msg)
    return '\n'.join(results[-1])

def execute_KR(clsName,rawArgDict):
    dill.dump((clsName,rawArgDict),open('/mnt/data2/Users/sunshuo/temp.pickle','wb'))
    Module = NSMapDict['KR']
    m = importlib.import_module(Module)
    cls = getattr(m,clsName)
    argDict = extractDcit(rawArgDict,'KR')
    Res = [None,None,None,None]
    try:
        layer = cls(**argDict['init'])
        Res[0] = 'Success'
    except Exception as e:
        msg = traceback.format_exc()
        msg = extractErrmag(msg)
        return [(msg,repr(e),str(e)),None,None,None]
    try:
        y = layer(**argDict['call'])
        if isinstance(y,tuple):
            y = y[0]
        Res[1] = list(y.shape)
    except Exception as e:
        msg = traceback.format_exc()
        msg = extractErrmag(msg)
        Res[1] = (msg,repr(e),str(e))
    try:
        if 'inputs' in argDict['call'].keys():
            x = argDict['call']['inputs']
        else:
            x = argDict['call']['sequences']
        if isinstance(x,list) and hasattr(layer,'compute_output_shape'):
            s = layer.compute_output_shape([i.shape for i in x])
            Res[2] = list(s) 
        elif hasattr(layer,'compute_output_shape'):
            s = layer.compute_output_shape(x.shape)
            Res[2] = list(s)
        else:
            Res[2] = None
    except Exception as e:
        msg = traceback.format_exc()
        msg = extractErrmag(msg)
        Res[2] = (msg,repr(e),str(e))
    return Res

def execute_torch(clsName,rawArgDict):
    Module = NSMapDict['torch']
    m = importlib.import_module(Module)
    cls = getattr(m,clsName)
    argDict = extractDcit(rawArgDict,'torch')
    Res = [None,None,None,None]
    try:
        layer = cls(**argDict['init'])
        Res[0] = 'Success'
    except Exception as e:
        msg = traceback.format_exc()
        msg = extractErrmag(msg)
        return [msg,None,None,(repr(e),str(e))]
    try:
        y = layer(**argDict['call'])
        if isinstance(y,tuple):
            y = y[0]
        print(type(y))
        Res[1] = list(y.shape)
    except Exception as e:
        msg = traceback.format_exc()
        msg = extractErrmag(msg)
        Res[1] = msg
        Res[3] = (repr(e),str(e))
    return Res

executorDir = {'KR':execute_KR,'torch':execute_torch}