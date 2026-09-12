"""Small multimodal BC integration probe; no pretrained VLA or capability claims."""
from __future__ import annotations
import argparse
import json
import platform
from pathlib import Path
import time
import numpy as np
import torch
from torch import nn
from .io import write_json,digest
from .pipeline import verify_release


def tokenize(texts,max_length=192):
    # UTF-8 byte IDs, 0 padding, 1..256 bytes. This is a toy tokenizer, not an LLM.
    result=np.zeros((len(texts),max_length),np.int64)
    for i,text in enumerate(texts):
        values=np.frombuffer(str(text).encode('utf8')[:max_length],dtype=np.uint8).astype(np.int64)+1
        result[i,:len(values)]=values
    return torch.from_numpy(result)


class TinyMultimodalBC(nn.Module):
    def __init__(self,state_dim,action_dim,horizon):
        super().__init__();self.horizon=horizon;self.action_dim=action_dim
        self.vision=nn.Sequential(nn.Conv2d(3,8,5,stride=2),nn.ReLU(),nn.Conv2d(8,16,3,stride=2),nn.ReLU(),nn.AdaptiveAvgPool2d(1),nn.Flatten())
        self.text=nn.Embedding(257,16,padding_idx=0)
        self.head=nn.Sequential(nn.Linear(state_dim+32,96),nn.ReLU(),nn.Linear(96,horizon*action_dim))

    def forward(self,image,state,tokens):
        mask=(tokens!=0).unsqueeze(-1)
        text=(self.text(tokens)*mask).sum(1)/mask.sum(1).clamp_min(1)
        return self.head(torch.cat([self.vision(image),state,text],1)).reshape(-1,self.horizon,self.action_dim)


def masked_mse(pred,target,mask):
    denom=mask.sum()
    if denom==0:raise ValueError('Empty loss mask')
    return ((pred-target).square()*mask).sum()/denom


def load_split(directory):
    files=sorted(directory.glob('*.npz'))
    if not files:return None
    arrays=[]
    for file in files:
        with np.load(file,allow_pickle=False) as a:arrays.append({k:a[k] for k in ('image','state','language','actions','action_mask')})
    batch={k:np.concatenate([a[k] for a in arrays]) for k in arrays[0]}
    return {'image':torch.from_numpy(batch['image'].astype(np.float32)/255).permute(0,3,1,2),'state':torch.from_numpy(batch['state']),'tokens':tokenize(batch['language']),'target':torch.from_numpy(batch['actions']),'mask':torch.from_numpy(batch['action_mask'])}


def loss_for(model,b):return masked_mse(model(b['image'],b['state'],b['tokens']),b['target'],b['mask'])


def train_probe(release: Path,output: Path,steps=120,seed=7):
    manifest=verify_release(release)
    torch.set_num_threads(4);torch.manual_seed(seed);torch.use_deterministic_algorithms(True)
    output.mkdir(parents=True,exist_ok=True)
    results=[]
    for source in manifest['sources']:
        sid=source['id'];train=load_split(release/'views'/sid/'train');val=load_split(release/'views'/sid/'validation')
        if train is None:continue
        dims={'state_dim':train['state'].shape[1],'action_dim':train['target'].shape[2],'horizon':train['target'].shape[1]}
        model=TinyMultimodalBC(**dims);optimizer=torch.optim.Adam(model.parameters(),lr=0.003)
        n=len(train['state']);start=time.perf_counter()
        with torch.no_grad():initial=float(loss_for(model,train))
        curve=[]
        for step in range(steps):
            indices=torch.randint(n,(min(32,n),))
            batch={k:v[indices] for k,v in train.items()}
            optimizer.zero_grad();loss=loss_for(model,batch)
            if not torch.isfinite(loss):raise ValueError('Non-finite loss')
            loss.backward()
            if any(p.grad is not None and not torch.isfinite(p.grad).all() for p in model.parameters()):raise ValueError('Non-finite gradients')
            optimizer.step()
            if step%10==0 or step==steps-1:curve.append({'step':step+1,'batch_masked_mse':float(loss.detach())})
        model.eval()
        with torch.no_grad():
            final=float(loss_for(model,train));validation=float(loss_for(model,val)) if val else None
            expected=model(train['image'][:1],train['state'][:1],train['tokens'][:1])
        checkpoint=output/(sid+'.pt')
        torch.save({'model':model.state_dict(),'optimizer':optimizer.state_dict(),'dims':dims,'seed':seed,'steps':steps,'release_id':manifest['release_id'],'statistics_sha256':digest(release/'statistics.json')},checkpoint)
        restored=TinyMultimodalBC(**dims);payload=torch.load(checkpoint,map_location='cpu',weights_only=True);restored.load_state_dict(payload['model']);restored.eval()
        restored_optimizer=torch.optim.Adam(restored.parameters(),lr=.003);restored_optimizer.load_state_dict(payload['optimizer'])
        with torch.no_grad():actual=restored(train['image'][:1],train['state'][:1],train['tokens'][:1])
        restore_error=float((expected-actual).abs().max())
        if restore_error>1e-7:raise ValueError('Checkpoint reload differs')
        results.append({'source_id':sid,'model':'TinyMultimodalBC_random_init','parameters':sum(p.numel() for p in model.parameters()),'input_shapes':{k:list(v.shape) for k,v in train.items()},'train_samples':n,'validation_samples':len(val['state']) if val else 0,'initial_train_masked_mse':initial,'final_train_masked_mse':final,'validation_masked_mse':validation,'finite_gradients':True,'checkpoint_reload_max_abs_error':restore_error,'optimizer_state_restored':True,'wall_seconds':round(time.perf_counter()-start,3),'curve':curve,'checkpoint_sha256':digest(checkpoint),'checkpoint_file':checkpoint.name})
        print(sid,'train',round(initial,5),'->',round(final,5),'validation',validation,flush=True)
    result={'release_id':manifest['release_id'],'purpose':'Validate RGB, time-filtered language, state, masked action chunks, gradients and checkpoint I/O. NOT pretrained VLA fine-tuning or robot capability evaluation.','seed':seed,'steps_per_source':steps,'device':'cpu','python':platform.python_version(),'torch':torch.__version__,'machine':platform.machine(),'platform':platform.platform(),'results':results}
    write_json(output/'training_probe.json',result)
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=Path('data'));p.add_argument('--output',type=Path,default=Path('data/training'));p.add_argument('--steps',type=int,default=120);args=p.parse_args()
    rid=json.loads((args.root/'latest.json').read_text())['release_id'];train_probe(args.root/'releases'/rid,args.output,args.steps)
