---
title: "Orbits of globular clusters"
excerpt: "Code to compute orbit of all Milky Way globular clusters. This is in response to a tweet..."
layout: single
author_profile: true
---


This is some very simple code that integrates the oribts of all (known) Milky
Way Globular clusters sampling from their phase-space uncertainties, based on
Gaia eDR3 and the [Baumgardt & Vasiliev (2020)
catalogue](https://people.smp.uq.edu.au/HolgerBaumgardt/globular/).

We start by reading importing some very cool packages and defining the position
and velocity of the Sun.

``` python
import vaex
import matplotlib.pyplot as plt
from astropy import coordinates as coord
from astropy import units as u
from orbit_util import sample_orbits ## Where the actual orbit integration is defined

k = 4.7404705
vlsr = 232.8
x_gc_sun = -8.2 # kpc
sunpos = numpy.array([-8.2, 0.0, 0.014 ])
sunvel = numpy.array([11.1, vlsr+12.24, 7.25]) 
coord.galactocentric_frame_defaults.set('v4.0')
v_sun = coord.CartesianDifferential((11.1, 232.8+12.24, 7.25)*u.km/u.s)
dgc_sun = x_gc_sun*u.kpc
```

Next we read the catalogue with the phase-space information. I had it prepared
as an `hdf5` table, using `astropy` Table class. I also run the orbit
integration in this step.

``` python
cooGC = vaex.open('BaumgardtHilker_MWGC.hdf5')

## This uses a LOT of memory, careful  when rerunning it
odf, samples = sample_orbits(cooGC, dt=3, n_steps=1000, nsamp=100,
                             num_cores=62) 
odf.export_hdf5('../mwgc_orbits.hdf5', progress=True)
samples.export_hdf5('../mwgc_samples.hdf5', progress=True)
```

Notice that I am using `vaex` to read and export all my large tables. Read more
about `vaex` [here](https://vaex.io/docs/index.html), it is a truly awesome
module that allows you to handle larger-than-memory datasets and much more!

For the orbit integration I am using `gala`
[(docs)](http://gala.adrian.pw/en/latest/) and the integration function is defined as:

``` python
import gala.dynamics as gd
import gala.integrate as gi
import gala.potential as gp
from gala.units import galactic
from tqdm import tqdm, trange
from joblib import Parallel, delayed
import multiprocessing

k = 4.7404705
potential = gp.MilkyWayPotential()

def _integrate(w, ids=None, dt=1, n_steps=500):
    orbit = potential.integrate_orbit(w, dt=-dt*u.Myr, n_steps=n_steps,
                                      Integrator=gi.DOPRI853Integrator)
    forbit = potential.integrate_orbit(w, dt=dt*u.Myr, n_steps=n_steps,
                                       Integrator=gi.DOPRI853Integrator)
    for n, orb in enumerate([orbit, forbit]):
        time = orb.t.value
        x = orb.x.value
        y = orb.y.value
        z = orb.z.value
        vx = orb.v_x.to(u.km/u.s).value
        vy = orb.v_y.to(u.km/u.s).value
        vz = orb.v_z.to(u.km/u.s).value
        E = orb.energy().to(u.km**2/u.s**2).value
        L = orb.angular_momentum()
        Lx, Ly, Lz = L[0], L[1], L[2]
        Lx = Lx.to(u.kpc*u.km/u.s).value
        Ly = Ly.to(u.kpc*u.km/u.s).value
        Lz = Lz.to(u.kpc*u.km/u.s).value
        ecc = np.repeat(orb.eccentricity(), len(x))
        ID = np.repeat(ids, len(x))
        _orb = orb.to_coord_frame(coord.ICRS)
        _ra = _orb.ra.value
        _dec = _orb.dec.value
        _pmra = _orb.pm_ra_cosdec.value
        _pmdec = _orb.pm_dec.value
        _Vlos = _orb.radial_velocity.value
        _hdist = _orb.distance.value
        out = np.array([time, x, y, z, vx, vy, vz, _ra, _dec, _pmra, _pmdec,
                        _Vlos, _hdist, ecc, E, Lz, ID]).T
        try:
            OUT = np.r_[out[::-1], OUT]
        except:
            OUT = out
    return OUT

def sample_orbits(df, id_column='Cluster', cols=['RA', 'DEC', 'Rsun', 'ERsun',
                                                 'pmra', 'e_pmra', 'pmdec',
                                                 'e_pmdec', 'RV', 'ERV'], 
                  dt=1, n_steps=500, num_cores=32, nsamp=100):

    ## Sample from a normal distribution nsamp times
    cname =  np.repeat(df[id_column].values, nsamp)
    ra =    np.repeat(df[cols[0]].values, nsamp)
    dec =   np.repeat(df[cols[1]].values, nsamp)
    pmra =  np.random.normal(df[cols[4]].values, df[cols[5]].values, 
                             (nsamp, len(df))).T.flatten()
    pmdec =  np.random.normal(df[cols[6]].values, df[cols[7]].values, 
                              (nsamp, len(df))).T.flatten()
    vlos =  np.random.normal(df[cols[8]].values, df[cols[9]].values, 
                             (nsamp, len(df))).T.flatten()
    dist =  np.random.normal(df[cols[2]].values, df[cols[3]].values, 
                             (nsamp, len(df))).T.flatten()

    cooE = coord.SkyCoord(ra=ra*u.deg,
                          dec=dec*u.deg,
                          distance=dist*u.kpc,
                          radial_velocity=vlos*u.km/u.s,
                          pm_ra_cosdec=pmra*u.mas/u.yr,
                          pm_dec=pmdec*u.mas/u.yr)

    # Save for later
    samples = vaex.from_arrays(ra=ra, dec=dec, pmra=pmra, pmdec=pmdec,
                               vlos=vlos, distance=dist)

    cooG = cooE.transform_to(coord.Galactic)
    cooGc = cooE.transform_to(coord.Galactocentric(galcen_distance=dgc_sun,
                                                   galcen_v_sun=v_sun)  
    w0 = gd.PhaseSpacePosition(cooGc.data)

    results = Parallel(n_jobs=num_cores)(delayed(_integrate)(i, ids=cname[n],
                                                 dt=dt, 
                                                 n_steps=n_steps) for n,i in tqdm(enumerate(w0)))
    all = np.vstack(results)
    odf = vaex.from_arrays(ID = all[:,16].astype(np.str),
                           time=all[:,0].astype(np.float32),
                           x=all[:,1].astype(np.float32),
                           y=all[:,2].astype(np.float32),
                           z=all[:,3].astype(np.float32),
                           vx=all[:,4].astype(np.float32),
                           vy=all[:,5].astype(np.float32),
                           vz=all[:,6].astype(np.float32),
                           ra=all[:,7].astype(np.float32),
                           dec=all[:,8].astype(np.float32),
                           pmra=all[:,9].astype(np.float32),
                           pmdec=all[:,10].astype(np.float32),
                           Vlos=all[:,11].astype(np.float32),
                           dist = all[:,12].astype(np.float32),
                           ecc = all[:,13].astype(np.float32),
                           E = all[:,14].astype(np.float32),
                           Lz = all[:,15].astype(np.float32),
                           )
    return (odf, samples)
```

Here is the original tweet that sparked the creation of this post, you can
click on it to see the output of the code.

<center>
<blockquote class="twitter-tweet"><p lang="en" dir="ltr">Orbits of 159 globular clusters around the Milky Way, sampled from their position and velocity uncertainties. Made with gala, <a href="https://twitter.com/matplotlib?ref_src=twsrc%5Etfw">@matplotlib</a> and <a href="https://twitter.com/vaex_io?ref_src=twsrc%5Etfw">@vaex_io</a> <a href="https://t.co/QTbWdoqSIR">pic.twitter.com/QTbWdoqSIR</a></p>&mdash; Eduardo Balbinot (@balbinotdd) <a href="https://twitter.com/balbinotdd/status/1441051694977191938?ref_src=twsrc%5Etfw">September 23, 2021</a></blockquote> <script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>
</center>

<br/>
