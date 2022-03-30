---
title: "N-Body in Blender"
excerpt: "A short and incomplete tutorial on how to use Blender to render your N-Body simulation in an `artistic' way."
layout: single
author_profile: true
---

A while ago I was trying to showcase some simulations a student made using
GADGET for a stellar stream. I tried matplotlib, but the camera animation
options are a bit limited. So I stumbled upon this nice article by [B. Kent
](https://www.cv.nrao.edu/~bkent/blender/files/nbody.pdf) showing how to do it
in Blender. However, this tutorial works well for older versions of Blender, it
was hard to follow in v3.8+. So I am here sharing my experience producing
N-Body animations in recent Blender versions.

Blender is free and you can install it quite easily as a self-contained binary,
but for full installation instructions see
[here](https://www.blender.org/download/). What makes it very powerful is that
any action can be scripted using it built-in Python interpreter. 

## The Scripting tab

A good place to start is the scripting tab. You will see a large editor screen
on your right, a 3D viewport and some consoles (output and python).

So in my case I have a series of `hdf5` files, one for each time-step in the
simulation. Each snapshot file has the coordinates for 5000 particles,
representing a stellar clusters; and 1 particle representing a dwarf galaxy.
Here is how it starts:


``` python

import bpy
import sys
sys.path.append('/home/balbinot/.local/lib/python3.9/site-packages')
import h5py
from glob import glob
import numpy as np

C = bpy.context
D = bpy.data

scale = 10

simdir = '/home/balbinot/blender/' 
print(simdir+'*.hdf5')
fl = glob(simdir + '*.hdf5')

## Sort snapshots human-style numerically 
n = np.argsort(np.array([int(f.split('_')[-1].split('.')[0]) for f in fl]))
fl = np.array(fl)[n]

src_obj = C.active_object   # Uses the currently selected 3d object
                            # as the particle type

```

The `bpy` module is what controls Blender, and the `C` (context) and `D` (data)
objects are shorthand for some useful controls. It is useful to append your
`PYTHONPATH` to include already installed packages in your system. It can be
tricky to install custom packages inside Blender's python interpreter, but this
gets around it nicely. The rest of this script just initializes some useful
variables and reorders the snapshot file list so its ordered in time by
filename.

Now, the first important bit, the `src_obj` becomes whatever object was
currently selected in the user interface. This means that if you had a solid
cube selected, your particles in the animation will be cubes. So, this is the
time to create this particle (anywhere in the viewport) and make it look like
what you want. In my case, I use small cubes that emit light in a diffuse halo
around them. This gives a good enough star representation without using a lot of
vertices, as this could lead to a very slow rendering time later. 

When you are happy with your 'star' object, you can duplicate it for each
particle in your first snapshot.

``` python

def read_snap(_f, npar=400):

    f = h5py.File(_f, 'r')
    xyz_stream = f['PartType1']['Coordinates'][:]
    xyz_Sgr = f['PartType2']['Coordinates'][:]
    
    np.random.seed(10)
    j = np.random.randint(xyz_stream.shape[0], size=npar)
    print(xyz_stream.shape)
    
    _xo = xyz_stream[j, 0]/scale
    _yo = xyz_stream[j, 1]/scale
    _zo = xyz_stream[j, 2]/scale
    _n =  np.arange(0, npar).astype('int')

    _xc = xyz_Sgr[:,0]/scale
    _yc = xyz_Sgr[:,1]/scale
    _zc = xyz_Sgr[:,2]/scale
    
    return j, _xo, _yo, _zo, _xc, _yc, _zc

def init_particles(n=0, npar=400):
    _f = fl[n]
    
    j, x, y, z, xc, yc, zc = read_snap(_f, npar=npar)
    
    collection = D.collections.new("Stars")
    C.scene.collection.children.link(collection)
    
    for _x, _y, _z in zip(x, y, z):
    
        new_obj = src_obj.copy()
        new_obj.data = src_obj.data.copy()
        new_obj.animation_data_clear()
        new_obj.location.xyz = (_x, _y, _z)
        collection.objects.link(new_obj)
```

`read_snap` just read your snapshot. If you are just running some tests, it is
useful to use only a few particles (set by `npar`). With `init_particles` we
put the particles at the right position for the first snapshot. We also keep
things tidy by place them under a `collection` called Stars.


Finally we can animate this! We define a new function `animate` (see below)
that goes through the snapshots and updates the location of each of the
particles. This is done by defining a `keyframe`. Notice that the location of
the particles can be interpolated in-between frames, so to make things lighter
I am skipping every other snapshot (`snapskip=2`)

``` python
def animate(snapskip=2, npar=400):
    
    stars = D.collections['Stars'].objects
    ksnap = fl[::snapskip]

    fnum = 0 
    for _f in ksnap:
        j, x, y, z, xc, yc, zc = read_snap(_f, npar=npar)
        for _x, _y, _z, star in zip(x, y, z, stars):
            star.location = (_x, _y, _z)
            star.keyframe_insert(data_path="location", frame=fnum)
        fnum += 1
```

## The Camera object 

What gets rendered in your final animation is what the camera object sees.
There are many things that can be set here (e.g. frame size, focal length,
etc..). But in my case I want the camera to be pointed at the right location
during the whole animation, regardless of its location. This is done by
creating `constraints` on the camera object.

I am not getting into too many details here, but you can check out this YouTube
video explaining it very well.

<center>
<iframe
src="https://www.youtube.com/embed/LeYUk3Ob5W8" title="YouTube video player"
frameborder="0" allow="accelerometer; autoplay; clipboard-write;
encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>
</center>

## Adding some cool background

What I usually miss in these types of simulations is the central galaxy. So you
can take some ready-made models from the Blender community and add it to your
animation. You can do it yourself, see the tutorial below:

<center>
<iframe 
src="https://www.youtube.com/embed/3s2gh0BjAN4" title="YouTube video player"
frameborder="0" allow="accelerometer; autoplay; clipboard-write;
encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>
</center>

On the video description there is a download link, considering giving this guy
a tip ;).


## Render the thing 

Now you can setup for rendering, and hopefully you have a nice GPU to speed-up
the process. It is worth mentioning that you can render remotely using a
VirtualGL setup, or simply render via command-line ins a machine that has a GPU
using:

``` bash
./blender -b ../your_animation.blend -a -- --cycles-device GPU
```

Here is my output from this example:




<center>
<iframe
src="https://www.youtube.com/embed/qD9KwpXDVic" title="YouTube video player"
frameborder="0" allow="accelerometer; autoplay; clipboard-write;
encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>
</center>