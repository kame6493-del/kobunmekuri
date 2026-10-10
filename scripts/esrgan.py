"""Real-ESRGAN (x4plus_anime_6B, BSD-3) で見本の絵を4倍に拡大する。重みは ESRGAN_WEIGHTS か work_redesign に置く(リポジトリには入れない)"""
import torch, torch.nn as nn, torch.nn.functional as F, numpy as np
from PIL import Image
class RDB(nn.Module):
    def __init__(s, nf=64, gc=32):
        super().__init__()
        s.conv1=nn.Conv2d(nf,gc,3,1,1); s.conv2=nn.Conv2d(nf+gc,gc,3,1,1); s.conv3=nn.Conv2d(nf+2*gc,gc,3,1,1)
        s.conv4=nn.Conv2d(nf+3*gc,gc,3,1,1); s.conv5=nn.Conv2d(nf+4*gc,nf,3,1,1); s.l=nn.LeakyReLU(0.2,True)
    def forward(s,x):
        x1=s.l(s.conv1(x)); x2=s.l(s.conv2(torch.cat((x,x1),1))); x3=s.l(s.conv3(torch.cat((x,x1,x2),1)))
        x4=s.l(s.conv4(torch.cat((x,x1,x2,x3),1))); x5=s.conv5(torch.cat((x,x1,x2,x3,x4),1)); return x5*0.2+x
class RRDB(nn.Module):
    def __init__(s,nf,gc=32):
        super().__init__(); s.rdb1=RDB(nf,gc); s.rdb2=RDB(nf,gc); s.rdb3=RDB(nf,gc)
    def forward(s,x): return s.rdb3(s.rdb2(s.rdb1(x)))*0.2+x
class RRDBNet(nn.Module):
    def __init__(s,nb=6,nf=64):
        super().__init__()
        s.conv_first=nn.Conv2d(3,nf,3,1,1); s.body=nn.Sequential(*[RRDB(nf) for _ in range(nb)]); s.conv_body=nn.Conv2d(nf,nf,3,1,1)
        s.conv_up1=nn.Conv2d(nf,nf,3,1,1); s.conv_up2=nn.Conv2d(nf,nf,3,1,1); s.conv_hr=nn.Conv2d(nf,nf,3,1,1); s.conv_last=nn.Conv2d(nf,3,3,1,1); s.l=nn.LeakyReLU(0.2,True)
    def forward(s,x):
        f=s.conv_first(x); f=f+s.conv_body(s.body(f))
        f=s.l(s.conv_up1(F.interpolate(f,scale_factor=2,mode='nearest'))); f=s.l(s.conv_up2(F.interpolate(f,scale_factor=2,mode='nearest')))
        return s.conv_last(s.l(s.conv_hr(f)))
_m=None
def model():
    global _m
    if _m is None:
        import os
        default = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'work_redesign', 'RealESRGAN_x4plus_anime_6B.pth')
        m=RRDBNet(); sd=torch.load(os.environ.get('ESRGAN_WEIGHTS', default),map_location='cpu',weights_only=True)
        m.load_state_dict(sd.get('params_ema',sd.get('params',sd))); _m=m.eval().cuda()
    return _m
def up4(im: Image.Image) -> Image.Image:
    a=np.asarray(im.convert('RGB')).astype(np.float32)/255
    t=torch.from_numpy(a).permute(2,0,1)[None].cuda()
    with torch.no_grad(): o=model()(t).clamp(0,1)[0].permute(1,2,0).cpu().numpy()
    return Image.fromarray((o*255+.5).astype(np.uint8))
