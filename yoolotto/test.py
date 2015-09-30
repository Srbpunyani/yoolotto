'''import ox3apiclient
from yoolotto.coupon.models import CouponVendor as CouponVendorModel
from yoolotto.coupon.models import Coupon as CouponModel
import json
email = 'jimmy@yoolotto.com'
password = 'Shae1973'
domain = 'ox-ui.yoolotto.com'
realm = 'yoolotto'
consumer_key = '9d975f29a35fdd0f1002f373b529b0d6c492936c'
consumer_secret = '65ecca223b1d3b5470246951afc8eb12cbd45345'

ox = ox3apiclient.Client(
    email=email,
    password=password,
    domain=domain,
    realm=realm,
    consumer_key=consumer_key,
    consumer_secret=consumer_secret,
    api_path='/ox/4.0'
    )

ox.logon(email, password)

#ads = ox.get('http://ox-ui.yoolotto.com/ox/4.0/account?value1=4,6')
pay = {'lifetime_click_cap': 1300}
print ox.put('http://ox-ui.yoolotto.com/ox/4.0/lineitem/537179569',pay)

'''
'''import ox3apiclient
from yoolotto.coupon.models import CouponVendor as CouponVendorModel
from yoolotto.coupon.models import Coupon as CouponModel
import json
email = 'jimmy@yoolotto.com'
password = 'Shae1973'
domain = 'ox-ui.yoolotto.com'
realm = 'yoolotto'
consumer_key = '9d975f29a35fdd0f1002f373b529b0d6c492936c'
consumer_secret = '65ecca223b1d3b5470246951afc8eb12cbd45345'

ox = ox3apiclient.Client(
    email=email,
    password=password,
    domain=domain,
    realm=realm,
    consumer_key=consumer_key,
    consumer_secret=consumer_secret,
    api_path='/ox/4.0'
    )

ox.logon(email, password)

#ads = ox.get('http://ox-ui.yoolotto.com/ox/4.0/account?value1=4,6')


print ox.get('http://ox-ui.yoolotto.com/ox/4.0/creative')['objects'][0]


order = {
    'status': 'Active',
    'name': 'OX3APIClient Object Creation Test2',
    'account_uid': '2003291b-accf-fff1-8123-2448be',
    'start_date': '2014-06-17 00:00:00'}

new_order = ox.post('http://ox-ui.yoolotto.com/ox/4.0/order', data=order)'''



