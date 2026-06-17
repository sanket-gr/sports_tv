import sys, urllib.parse, requests
sys.stdout.reconfigure(encoding='utf-8')

raw_url = 'https://saq.velonovahealth.sbs/v4/is9/bs9o1/cf-master.1781525424.txt'
ref     = 'https://zfatwqf.vidplayer.live/'

proxy_url = (
    'http://192.168.100.61:8000/api/proxy'
    '?url=' + urllib.parse.quote(raw_url, safe='')
    + '&referer=' + urllib.parse.quote(ref, safe='')
)
print('Proxied HLS URL for TV:')
print(proxy_url)
print()

# Update stream 22 in the DB with this working URL
from database import get_db, Stream
db = next(get_db())
stream = db.query(Stream).filter_by(id=22).first()
if stream:
    stream.hls_url = raw_url
    stream.iframe_url = 'https://zfatwqf.vidplayer.live/#bs9o1'
    stream.cf_domain = 'zfatwqf.vidplayer.live'
    db.commit()
    print(f'Updated stream 22 hls_url to: {raw_url[:70]}')
    print(f'Updated iframe_url to: {stream.iframe_url}')
db.close()

# Verify the API now returns correct proxy URL
data = requests.get('http://192.168.100.61:8000/api/streams/22').json()
print()
print('API hls_url:', data.get('hls_url','')[:100])
