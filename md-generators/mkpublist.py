#!/usr/bin/env python
from astroquery import nasa_ads as na

with open('ads_token', 'r') as fin:
    tk = fin.read().strip()
    na.ADS.TOKEN = tk

na.ADS.NROWS = 200
na.ADS.SORT = 'asc bibcode'
na.ADS.ADS_FIELDS = ['author', 'title', 'pubdate', 'bibcode', 'citation_count', 'doctype', 'bibstem']
results = na.ADS.query_simple('Balbinot, Eduardo doctype:article')
results.sort(['pubdate'], reverse=True)

for n, (res) in enumerate(results):
    a = res['author']
    pd = res['pubdate']

    author_order = [i for i, s in enumerate(a) if 'Balbinot' in s]
    if author_order[0] > 9:
        auth = '; '.join(a[0:9]) + 'et al. with Balbinot, E'
    else:
        auth = '; '.join(a[0:8])

    auth = auth.replace('Balbinot, E.', '**Balbinot, E.**')
    auth = auth.replace('Balbinot, Eduardo', '**Balbinot, E.**')

    pyear = pd.split('-')[0]
    try:
        if pyear==opyear:
            pass
        else:
            print(f'### {pyear}')
            opyear=pyear
    except:
            opyear=pyear
            print(f'### {pyear}')
    url = f"https://ui.adsabs.harvard.edu/abs/{res['bibcode']}/abstract"

    print(f"{n+1}. [*{res['title'][0]}*]({url}){{:target='_blank'}} <br/> {auth} \
          ({res['bibstem'][0]}; {res['citation_count']} citations)")
