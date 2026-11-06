"""2D finite-difference Z0 solver for microstrip / grounded CPW on one dielectric.
Quasi-static: Z0 = 1/(c*sqrt(C*C0)), eps_eff = C/C0. Zero-loss, conductor of finite thickness t.
"""
import numpy as np, scipy.sparse as sp, scipy.sparse.linalg as spl, sys
C0=299792458.0; E0=8.8541878128e-12

def capacitance(er, h, w, gap, t, dx=0.025, W=26.0, Hair=14.0, cpw=True):
    # grid in mm; ground plane at bottom (y=0), dielectric 0..h, air above, Dirichlet box
    nx=int(round(W/dx)); nyd=int(round(h/dx)); nya=int(round(Hair/dx)); ny=nyd+nya
    # permittivity on cell edges: use eps at cell centres, harmonic average on edges
    eps=np.ones((ny,nx)); eps[:nyd,:]=er
    X=np.arange(nx)*dx; cx=W/2
    cond=np.zeros((ny,nx),bool); V=np.zeros((ny,nx))
    ty=int(round(t/dx)); ty=max(ty,1)
    sig=(np.abs(X-cx)<=w/2)
    cond[nyd:nyd+ty,sig]=True; V[nyd:nyd+ty,sig]=1.0
    if cpw:
        gnd=(np.abs(X-cx)>=w/2+gap)
        cond[nyd:nyd+ty,gnd]=True  # coplanar grounds, V=0
    # boundaries Dirichlet 0 (ground plane bottom, top, sides)
    N=nx*ny; idx=lambda j,i:j*nx+i
    rows=[];cols=[];vals=[];b=np.zeros(N)
    fixed=np.zeros((ny,nx),bool); fixed[0,:]=fixed[-1,:]=True; fixed[:,0]=fixed[:,-1]=True
    fixed|=cond
    jj,ii=np.meshgrid(np.arange(ny),np.arange(nx),indexing='ij')
    free=~fixed
    def hm(a,b): return 2*a*b/(a+b)
    diag=np.zeros((ny,nx))
    rr=[];cc=[];vv=[]
    for dj,di in((1,0),(-1,0),(0,1),(0,-1)):
        j2=jj+dj;i2=ii+di
        ok=free&(j2>=0)&(j2<ny)&(i2>=0)&(i2<nx)
        j2c=np.clip(j2,0,ny-1);i2c=np.clip(i2,0,nx-1)
        wgt=hm(eps,eps[j2c,i2c])
        diag+=np.where(ok,wgt,0)
        nb_free=ok&free[j2c,i2c]
        rr.append(idx(jj,ii)[nb_free]);cc.append(idx(j2c,i2c)[nb_free]);vv.append(-wgt[nb_free])
        nb_fix=ok&fixed[j2c,i2c]
        b[idx(jj,ii)[nb_fix]]+=(wgt*V[j2c,i2c])[nb_fix]
    rr.append(idx(jj,ii)[free]);cc.append(idx(jj,ii)[free]);vv.append(diag[free])
    A=sp.csr_matrix((np.concatenate(vv),(np.concatenate(rr),np.concatenate(cc))),shape=(N,N))
    fidx=np.flatnonzero(free.ravel())
    Af=A[fidx][:,fidx]; bf=b[fidx]
    sol=spl.spsolve(Af.tocsc(),bf)
    Phi=V.copy().ravel(); Phi[fidx]=sol; Phi=Phi.reshape(ny,nx)
    # energy W = 1/2 sum eps*|grad phi|^2 ; C = 2W/V^2  (per unit length, eps0 factored)
    E=0.0
    gy=np.diff(Phi,axis=0); ey=hm(eps[:-1,:],eps[1:,:]); E+=np.sum(ey*gy**2)
    gx=np.diff(Phi,axis=1); ex=hm(eps[:,:-1],eps[:,1:]); E+=np.sum(ex*gx**2)
    return E*E0   # F/m (dx cancels in 2D)

def z0(er,h,w,gap,t,dx=0.025,cpw=True):
    c1=capacitance(er,h,w,gap,t,dx,cpw=cpw); c0=capacitance(1.0,h,w,gap,t,dx,cpw=cpw)
    return 1/(C0*np.sqrt(c1*c0)), c1/c0

if __name__=="__main__":
    # validation: microstrip FR4-like case vs Hammerstad (h=1.6, er=4.4, W=3.0 -> ~50 ohm)
    print("validation microstrip er=4.4 h=1.6 W=3.0:", z0(4.4,1.6,3.0,0,0.035,cpw=False))
