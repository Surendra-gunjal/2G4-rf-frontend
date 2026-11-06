import numpy as np, json, time
from scipy.optimize import brentq
from z0_solver import capacitance, C0
h=0.813; t=0.035
def z0c(er,w,gap,cpw,dx=0.05):
    c1=capacitance(er,h,w,gap,t,dx,W=16.0,Hair=8.0,cpw=cpw)
    c0=capacitance(1.0,h,w,gap,t,dx,W=16.0,Hair=8.0,cpw=cpw)
    return 1/(C0*np.sqrt(c1*c0)), c1/c0
def hj(er,W):
    u=W/h
    a=1+np.log((u**4+(u/52)**2)/(u**4+0.432))/49+np.log(1+(u/18.1)**3)/18.7
    b=0.564*((er-0.9)/(er+3))**0.053
    ee=(er+1)/2+(er-1)/2*(1+10/u)**(-a*b)
    f=6+(2*np.pi-6)*np.exp(-(30.666/u)**0.7528)
    return 60*np.log(f/u+np.sqrt(1+(2/u)**2))/np.sqrt(ee), ee
t0=time.time(); res={}
for er in (3.55,3.38):
    Wcf=brentq(lambda W:hj(er,W)[0]-50,0.5,4)
    zms,ems=z0c(er,Wcf,0,False)                       # FD spot check of closed-form width
    Wcp=brentq(lambda W:z0c(er,W,0.30,True)[0]-50,0.4,2.5,xtol=0.01)
    zc,ec=z0c(er,Wcp,0.30,True)
    res[er]=dict(W_microstrip_closedform=round(Wcf,3),Z0_FD_at_that_W=round(float(zms),1),
                 W_GCPW_gap0p30=round(Wcp,3),GCPW_Z0_check=round(float(zc),1),GCPW_eps_eff=round(float(ec),2))
    print(er,res[er],f"{time.time()-t0:.0f}s",flush=True)
json.dump(res,open('width_results.json','w'),indent=1)
