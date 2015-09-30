import datetime
import math
import json
from django.db.models import Q
from django.views.generic import View
from django.shortcuts import render_to_response
from yoolotto.rest import exceptions
from yoolotto.rest.decorators import rest, Authenticate
from django.core.mail import send_mail
from yoolotto.coupon.geo.manager import GeoManager
from yoolotto.user.models import Device, UserCoinsDetails, UserClientLogin, UserCoinsDetails
from yoolotto.second_chance.sendemail import common_send_email
from yoolotto.lottery.models import LotteryTicket
from yoolotto.settings_local import COUPON_MAIL_CC, COUPON_REDEEM_DURATION
from yoolotto.second_chance.models import AdIssue
#from yoolotto.settings import AFTER_LOGON_OX, ox, email, password, domain, realm, consumer_key, consumer_secret
from yoolotto.second_chance.models import FAQ as FaqModel
from yoolotto.second_chance.models import Advertisor as AdvertisorModel, AdInventory as InventoryModel
from django.http.response import HttpResponse
from django.conf import settings
from django.db.models import F
from yoolotto.coin.models import EmailCoins, DeviceCoins

def login_openx():
    import ox3apiclient

    ox = ox3apiclient.Client(
        email=email,
        password=password,
        domain=domain,
        realm=realm,
        consumer_key=consumer_key,
        consumer_secret=consumer_secret,
        api_path='/ox/4.0'
        )

    AFTER_LOGON_OX=ox.logon(email, password)

    return AFTER_LOGON_OX

class InAppFuelCallback(View):
	@rest
	
	def get(self,request,userID,currency,game_id,sig):
		return {"result":0}

# class to fetch the coupons of a second chance vendor
class AdCoupons(View):
    @rest
    @Authenticate()
    def get(self, request,filter="active"):
        cv_id = request.GET.get('cv_id', None)
        if filter == "active":
            adunits =  InventoryModel.objects.filter(inventory__gt = 0,account_id=cv_id,status='Active')
	    try:
            	return {'results':map(lambda x: x.representation(),adunits),"adunit_id":"537154909"}
	    except:
		return {'results':[]}
        else:
            raise exceptions.WebServiceException("Invalid Coupon Filter")

class AdColony(View):
    @rest
    @Authenticate()
    def get(self,request):
	if request.META["HTTP_YOO_DEVICE_TYPE"] == 'ANDROID':
		zone = "vz337c35351159410f8d"
	else:
        	zone = "vz3ee9d6022cef430bbb"
        return {"send_ticket":zone,"check_ticket":zone,"yoo_games":zone}

# Sample second chance game for android ( In place of In App Fuel of Iphone )        
class AndroidGame(View):
    @rest
    @Authenticate()
    def post(self, request):
        number = settings.GAME_NUMBER
        data = json.loads(request.body)
	if number == data['number']:
            return {'matched':True}
        else:
            return {'matched':False}

# class to provide range of numbers for android game 
class AndroidNumbers(View):
    @rest
    @Authenticate()
    def get(self,request):
        return {"Max":settings.ANDROID_GAME_MAX_NUMBER,"Min":settings.ANDROID_GAME_MIN_NUMBER}

# class to send fb, twitter message 
class SocialMessage(View):
    @rest
    @Authenticate()
    def get(self, request):
        return {"message":settings.SOCIAL_MESSAGE}

# class to generate unique url for sca 
class SCA_url(View):
    @rest
    @Authenticate()
    def post(self, request):
        import urllib2
        data = json.loads(request.body)
        client_login_record, created = UserClientLogin.objects.get_or_create(device=request.yoo['device'])
        if client_login_record.client_login == None:
            coins = DeviceCoins.objects.get(device_id=client_login_record.device).coins
        else:
            email_record, created = EmailCoins.objects.get_or_create(email=client_login_record.client_login, defaults={'coins': 0})
            coins = DeviceCoins.objects.filter(device_id=client_login_record.device)[0].coins + email_record.coins
        '''if data['add_coins']:
            url = " https://twittaboom.herokuapp.com/dplayurl/slotcloud?username=demo&password=secret&user="+str(client_login_record.id)+"&domain=qa&coins="+str(coins)+""
        else:
            url = "https://twittaboom.herokuapp.com/dplayurl/slotcloud?username=demo&password=secret"'''

	if data['add_coins']:
            if data['gameType'] == 'scratch':
                url = "https://twittaboom.herokuapp.com/dplayurl/yoolotto4?username=yoolotto&password=eE6xzvjG&user="+str(client_login_record.id)+"&domain=pro&coins="+str(coins)+""

            elif data['gameType'] == 'slot':
                url = "https://twittaboom.herokuapp.com/dplayurl/yoolotto3?username=yoolotto&password=eE6xzvjG&user="+str(client_login_record.id)+"&domain=pro&coins="+str(coins)+""
                #url = " https://twittaboom.herokuapp.com/dplayurl/slotcloud?username=demo&password=secret&user="+str(client_login_record.id)+"&domain=qa&coins="+str(coins)+""
        else:
            url = "https://twittaboom.herokuapp.com/dplayurl/yoolottoaer?username=yoolotto&password=yoolotto739"

        req = urllib2.Request(url)
        res = urllib2.urlopen(req)
        dynamic_url = res.read()

        return {"url":dynamic_url}

# class to show dynamic ads for every screen
class ScreenAds(View):
    @rest
    @Authenticate()
    def get(self,request):              
	import random
        adunits_list = []
        sections_list = []
        result = []
	try:
           '''try:'''
           adunits =  AFTER_LOGON_OX.get('http://ox-ui.yoolotto.com/ox/4.0/adunit?limit=0')['objects']
	   '''except:
               AFTER_LOGON_OX = login_openx()
               adunits =  AFTER_LOGON_OX.get('http://ox-ui.yoolotto.com/ox/4.0/adunit?limit=0')['objects']'''

           sections =  AFTER_LOGON_OX.get('http://ox-ui.yoolotto.com/ox/4.0/sitesection?limit=0')['objects']

           for section in sections :
            if section['site_id'] == settings.OPENX_SITE_ID:
                sections_list.append({"section_id":section['id'],"site_id":section['site_id'],"name":section["name"]})

           for adunit in adunits:
            if adunit['site_id'] == settings.OPENX_SITE_ID:

                if adunit['type_full'] == 'adunit.mobile':
                    if adunit['primary_size'] == '320x50':
	                if adunit['tag_type'] == 'json':
                            adunit_type = 'adunit.bannerad'
                        elif adunit['tag_type'] == 'html':
                            adunit_type = 'adunit.text'
                    elif adunit['primary_size'] == '320x480':
                        adunit_type = 'adunit.image'
                else:
                    adunit_type = adunit['type_full']
		
                adunits_list.append({"adunit_id":adunit['id'],"section_id":adunit['sitesection_id'],"type":adunit_type})

           for index in sections_list:
            info = [{"adunit":item['adunit_id'],"screen":index["name"],"type":item["type"]} for item in adunits_list if item['section_id']==index['section_id']]
            if info:
                result.append(info[random.randint(0,len(info)-1)])

	   valid_screens = ["Yoo Games","Jackpot Result","ScanScreen"]
           valid_data = []
           for index in result:
               if index['screen'] in valid_screens:
                   valid_data.append(index)
           results =  {"ads":valid_data,"domain":"ox-d.yoolotto.com","video_ad_url":"http://ox-d.yoolotto.com/v/1.0/av?auid="}
	   return {"results":results}
	except:
	   return result
        
# class to add coins to device or email on invitation or message        
class InviteFriends(View):
    @rest
    @Authenticate()
    def post(self, request):
        data = json.loads(request.body)
	
        client_login_record, created = UserClientLogin.objects.get_or_create(device=request.yoo['device'])
        if client_login_record.client_login:
            coins_record, created = EmailCoins.objects.get_or_create(email=client_login_record.client_login,defaults={'coins': 0})
        else:
            coins_record, created = DeviceCoins.objects.get_or_create(device_id=request.yoo['device'], defaults={'coins': 0})
	
        if data['is_invite']:
	    coins_record.coins = F('coins') + int(data['count'])*40
	    coins_record.invites = F('invites')+int(data['count'])
	    coins_record.save()
        else:
            coins_record.coins = F('coins') + int(data['count'])*40
	    coins_record.messages = F('messages') + int(data['count'])
            coins_record.save()
        if client_login_record.client_login:
            coins = EmailCoins.objects.filter(email=client_login_record.client_login)[0].get_coins() +  DeviceCoins.objects.filter(device_id=request.yoo['device'])[0].get_coins()
        else:
            coins = DeviceCoins.objects.filter(device_id=request.yoo['device'])[0].get_coins()
            
        return {"total_coins":coins,"coins":str(int(data['count'])*40)}

# class to add coins to device or email, when user plays IPhone game (In App Fuel)        
class AddCoins(View):
    @rest
    @Authenticate()
    def post(self, request):
        data = json.loads(request.body)
	try:
        	client_login_record = UserClientLogin.objects.get(device=request.yoo['device'])
	except:
		return {"message":"Device is not registered with Yoolotto"}
        if client_login_record.client_login:
            coins_record = EmailCoins.objects.get(email=client_login_record.client_login)
        else:
            coins_record = DeviceCoins.objects.get(device_id=request.yoo['device'])
        coins_record.coins = F('coins') + int(data['coins'])
        coins_record.save()
        if client_login_record.client_login:
            coins = EmailCoins.objects.get(email=client_login_record.client_login).get_coins()
        else:
            coins = DeviceCoins.objects.get(device_id=request.yoo['device']).get_coins()
        if int(data['coins']) > 1:
            return {"total_coins":coins,"coins":data['coins'],'message':"You have got "+str(data['coins'])+" coins"}
        elif int(data['coins']) == 1:
            return {"total_coins":coins,"coins":data['coins'],'message':"You have got "+str(data['coins'])+" coin"}
        else:
           return {"total_coins":coins,"coins":data['coins'],'message':"Better luck next time"} 


class AdRedeem(View):
    @rest
    @Authenticate()
    def post(self, request):
	valid = False
        data = json.loads(request.body)
        return_data = {}	
        client_login_record = UserClientLogin.objects.filter(device = request.yoo['device'])[0]
        device_coins_record = DeviceCoins.objects.filter(device_id=request.yoo['device'])[0]
        device_coins = device_coins_record.coins

	if device_coins_record.get_coins() >= 20:
                    device_coins_record.coins = F('coins') - 20
                    device_coins_record.save()

	else:
                    if client_login_record.client_login:
                        email_coins_record = EmailCoins.objects.get(email=client_login_record.client_login)
                        if email_coins_record.get_coins() >= 20:
                            email_coins_record.coins = F('coins') - 20
                            email_coins_record.save()

	return {"success":True}


        '''if inventory > 0:
            if device_coins >= int(ad_data_source["coins"]):
                valid = True
            else:
                if client_login_record.client_login:
                    email_coins_record = EmailCoins.objects.filter(email=client_login_record.client_login)[0]
                    if email_coins_record.coins >= int(ad_data_source["coins"]):
                        valid = True

            if valid:
                if data["winner"]:
                    ad_data_source["inventory"] = inventory - 1
                    jsonString = json.dumps(ad_data_source)
                    info = {"source": jsonString}
                    AFTER_LOGON_OX.put('http://ox-ui.yoolotto.com/ox/4.0/ad/'+str(InventoryRecord.ad_id)+'',info) # update single lineitem
                    updated_inventory = inventory - 1
                else:
                    updated_inventory = inventory
                try:
                    InventoryRecord.ad_image = ad_data_source['ad_image']
                except:
                    InventoryRecord.ad_image = None
                try:
                    InventoryRecord.vendor = ad_data_source['vendor']
                except:
                    InventoryRecord.vendor = None
                try:
                    InventoryRecord.vendor_image = ad_data_source['vendor_image']
                except:
                    InventoryRecord.vendor_image = None
                try:
                    InventoryRecord.coins = ad_data_source['coins']
                except:
                    InventoryRecord.coins = 0
                try:
                    InventoryRecord.InventoryRecord.timer = ad_data_source['timer']
                except:
                    InventoryRecord.timer = False
                try:
                    InventoryRecord.ad_type = ad_data_source['type']
                except:
                    InventoryRecord.ad_type = None
                try:
                    InventoryRecord.video_url = ad_data_source['videourl']
                except:
                    InventoryRecord.video_url = None
                InventoryRecord.inventory = updated_inventory
                
                InventoryRecord.save()

                if InventoryRecord.type == 'physical':
                    AdIssueRecord = AdIssue(ad=InventoryRecord,address=data['address'],email=data['email'],device=request.yoo['device'],phone=data['phone'],won=data['winner'])
                else:
                    AdIssueRecord = AdIssue(ad=InventoryRecord,email=data['email'],device=request.yoo['device'],won=data['winner'])
                AdIssueRecord.save()

                if data['winner']:
                    subject = "Second Chance Ad"
                    context = {}
                    text_template_path = "second_chance_email.txt"
                    html_template_path = "second_chance_email.html"
                    context_data = {'second_chance_obj': InventoryRecord}
                    recipients = [data['email'], 'subodh.deoli@spa-systems.com', 'kapil.soni@spa-systems.com']
		    common_send_email(subject, text_template_path, html_template_path,context_data, recipients)
		    
                    return_data['email'] = 1
		    return_data['message'] = 'Email is sent'
                    return_data['screen'] = settings.SECOND_CHANCE_WINNING_MESSAGE 
                else:
                    return_data['email'] = 0
		    #return_data['message'] = 'Better luck next time'
		    return_data['screen'] = settings.SECOND_CHANCE_LOOSING_MESSAGE

                
                if device_coins_record.get_coins() >= 20:
                    device_coins_record.coins = F('coins') - 20
                    device_coins_record.save()

                    
                else:
                    if client_login_record.client_login:
                        email_coins_record = EmailCoins.objects.get(email=client_login_record.client_login)
                        if email_coins_record.get_coins() >= 20:
                            email_coins_record.coins = F('coins') - 20
                            email_coins_record.save()

            else:
                return_data['email'] = 0
                return_data['message'] = 'You do not have enough coins'
                return_data['screen'] = settings.SECOND_CHANCE_LOOSING_MESSAGE
                
                
        else:
            
	    return_data['email'] = 0
            return_data['message'] = 'No Inventory left for this ad in OpenX'
            return_data['screen'] = settings.SECOND_CHANCE_LOOSING_MESSAGE

	return return_data'''

#class to show the list of advertisors for second chance
class Advertisors(View):
    @rest
    @Authenticate()
    def get(self, request):
	user = request.yoo["user"]
        
        Inventories = InventoryModel.objects.filter(inventory__gt = 0,status='Active')
        Vendors = set([inventory.account for inventory in Inventories ])
        
        return map(lambda x: x.representation(),Vendors)

#class to show the list of frequently asked questions and answers
class FrequentQuestions(View):
    @rest
    def get(self, request):
        Faqs = FaqModel.objects.all()
        return map(lambda x: x.representation(), Faqs)
        
class TimerAd(View):
    @rest
    @Authenticate()
    def post(self, request):
        user = request.yoo["user"]
        data = json.loads(request.body)
        _id = int(data['id'])
        
        #issue = AdIssue.objects.get(pk=_id)
        
        try:
            #ad_stores = AdStoresModel.objects.filter(ad=issue.ad)
            result = []
            
            _result1 = {
                "name": "Dominos",
                "code": "Dominos",
                "address": "Sector q",
                "address_2": "Sector 18",
                "city": "Noida",
                "state": "Uttar Pradesh",
                "postal_code": "248001",
                "phone": "9999998899",
                "latitude": "28.646951",
                "longitude": "77.310984",
                "distance": "280"
            }
            
            result.append(_result1)
            
            _result2 = {
                "name": "KFC",
                "code": "KFC",
                "address": "Block A",
                "address_2": "Sector 1",
                "city": "Gurgaon",
                "state": "Haryana",
                "postal_code": "248332",
                "phone": "8989898898",
                "latitude": "28.644897",
                "longitude": "77.335583",
                "distance": "780"
            }
            
            result.append(_result2)     

            return result
        except:
            raise exceptions.WebServiceException("This is not a timer coupon")
            
            
