This repo contains source code of paper 'Active Parameter Guided Test Case Generation for Deep Learning Libraries' submitted to ISSTA25

The dir 'data' contains parameter space ('ParamInfo_KR.pickle') and initial population ('seedpool_KR.pickle') of each API 

The dir 'GA_dynamicWeight' contains exprimental results and source codes to reproduce our expriments

You can reproduce the experiments in our paper by executing the following commands.

cd GA_dynamicWeight/runtestDir

bash run_complete.sh

You can also reproduce our ablation experiments by executing the following commands.

cd GA_dynamicWeight/runtestDir

bash runTest.sh