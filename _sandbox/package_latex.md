---
title: "Make a nice package out of your Latex project"
excerpt: "Bundle-up all the necessary files to build a latex project, and produces a compressed archive ready for submission"
layout: single
author_profile: true
---

I got tired of removing `\textbf` and fixing absolute figure paths in my 
papers before submission. So I created this quick script to format, compress, and bundle
all necessary files to submit your paper. 

This has been tailored for Monthly Notices of the Royal Astronomical Society (MNRAS), but it should work
for other journals if you have the patience to make some adaptations. 

It basically uses [TexSoup](https://texsoup.alvinwan.com/) to track down
certain tags (e.g. `\textbf`) and remove them. In case you keep you figures and
tables in separate directories (a good practice!), it will remove the leading
directory. This is useful when submitting to [ArXiv.org](https://arxiv.org).
And if you are like me that keeps old and unused figures together with
final-version ones, the script will package only the necessary figures. 

The script is not perfect, it fails to remove bold-face inside figure captions
(not sure why). Here is the code:

``` python
#!/usr/bin/env python

import datetime
from TexSoup import TexSoup
from sys import argv
import os
import shutil
import re

now = datetime.date.today()
date = now.strftime('%y%m%d')

infile = argv[1]
outfile = infile.replace('.tex',f"_{date}.tex")

with open(infile, 'r') as f:
    soup = TexSoup(f)

figures = soup.find_all('includegraphics')
tables = soup.find_all('input')
bib = soup.find_all('bibliography')

rmRelative = True
rmBold = False

flist = open('.pack.txt', 'w')

# Get figure path, assumes all figures are in the same dir
figdir = '/'.join(figures[0].args[-1].string.split('/')[0:-1])

for figure in figures:
    figpath = figure.args[-1].string
    flist.write(figpath+"\n")
    if rmRelative:
        figure.args[-1].contents = [figpath.split('/')[-1]]
        #figpath = figure.args[-1].string
    print(figpath)

for table in tables:
    tblpath = table.args[-1].string+'.tex'
    flist.write(tblpath+"\n")
    if rmRelative:
        table.args[-1].contents = [tblpath.split('/')[-1]]
        #tblpath = table.args[-1].string
    print(tblpath+'.tex')

bibpath = f"{bib[0].args[-1].string}.bib"

flist.write(bibpath+"\n")
flist.write(outfile+"\n")

flist.close()

if rmBold:
    tb = soup.find_all('textbf')
    for t in tb:
        try:
            t.replace_with(t.args[0].string)
        except:
            print('Buggy')

with open(outfile, "w") as f:
    f.write(str(soup))

os.makedirs('.tmp', exist_ok=True)

with open('.pack.txt', 'r') as f:
    for line in f.readlines():
        shutil.copy(line.strip(), '.tmp/')

shutil.make_archive('to_submit', 'gztar', root_dir='.tmp', base_dir=".")

shutil.rmtree('.tmp')
os.remove('.pack.txt')
```

Finally, be careful when using this! It has some system commands to
delete/create files that may be important to you.
