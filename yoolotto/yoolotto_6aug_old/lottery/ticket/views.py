import json
import uuid
import datetime
import ast
from django.db.models import F
from django.db import transaction
from django.views.generic import View

from yoolotto.rest import exceptions
from yoolotto.rest.decorators import rest, Authenticate
from yoolotto.lottery.models import LotteryCountryDivision
from yoolotto.user.models import UserClientLogin,Device
from yoolotto.coin.models import CoinTransaction, CoinShareTransaction
from yoolotto.lottery.enumerations import EnumerationManager
from yoolotto.lottery.game.base import LotteryPlayInvalidException
#from yoolotto.lottery.game.manager import GameManager
from yoolotto.lottery.models import LotteryDraw, LotteryTicket, LotteryTicketPlay, \
    LotteryTicketSubmission, LotteryTicketClient, LotteryTicketAvailable,LotteryTicketEdit, LotteryGameComponent
from yoolotto.second_chance.models import *
from yoolotto.user.models import *
from yoolotto.coin.models import *
from yoolotto.lottery import representations
from yoolotto.util.serialize import dumps
import ast
import urllib2
import json
from  ctypes import *
import thread
from yoolotto.communication.apn import APNSender
from yoolotto.communication.gcm_sender import GCMSender

def send_data_to_det(success,ticket,play,game_type,image_data,state,old_version,data):
    if success:

        DET_GAMES = {11: 1,1: 1,13: 2,0: 2,2: 3,3: 5,4: 6,5: 7,6: 4,7: 8,}
	try:
	    multiDraw =  data[0]['multiDraw']
            StartDate =  str(ticket.draw.date)
            Consecutive = data[0]['Consecutive']
	except:
	    pass
	RetailerNo = ''
        try:
            if data[0]['multiDrawEndDate'] is not None or "null":
                EndDate = data[0]['multiDrawEndDate']
        except:
             EndDate = "null"
      	if state == 'TX' and old_version == False:
            ocr_lib = cdll.LoadLibrary("/home/ubuntu/current/yobackend/yoolotto/yoolotto/OCR-OCR_server/YoolottoOCR/libOCR.so") # pass the path of .so file
            ocr_lib.OCR_Call_server.argtypes = [POINTER(c_ubyte),c_int,c_char_p,c_int,c_int,c_char_p,c_int,c_char_p,c_char_p]
            img = (c_ubyte*len(image_data))(*(image_data))
            img_length = len(image_data) # length of data
            lib_prt_path ="/home/ubuntu/current/yobackend/yoolotto/yoolotto/OCR-OCR_server"
            gameType = DET_GAMES[game_type]
            state = 1
            string_buffer = create_string_buffer(4096)
            buffer_length = 4096
            error = create_string_buffer(500)
            img_name = create_string_buffer("image_test.jpg")
            ret = ocr_lib.OCR_Call_server(img,img_length,lib_prt_path,gameType,state,string_buffer,buffer_length,error,img_name)
            print "ret ", ret
            if ret >= 0:
                buff= string_buffer.raw
                buff = "".join([buff.rsplit("}" , 1)[0] , "}"])
                try:
                    json_data = json.loads(buff)
                    #print "json_data",json_data
                except:
		    availability = LotteryTicketAvailable.objects.get(ticket = ticket,play = play)
		   # availability.pending = False
		    availability.rejected = True
		    availability.save()
                    send_reject_notification(ticket,"Image is rejected","Please retake the photo")
                    raise exceptions.WebServiceException("Image is Rejected.")
            elif ret == 177:
		availability = LotteryTicketAvailable.objects.get(ticket = ticket,play = play)
		#availability.pending = False
		availability.rejected = True
		availability.save()
                send_reject_notification(ticket,"Image is rejected","Please retake the photo")
                raise exceptions.WebServiceException("Image is Rejected.")

            lines = json_data['lines']
            multiDraw =  json_data['multiDraw']
            StartDate =  json_data['drawdateFrom']# or str(ticket.draw.date)
	    RetailerNo = json_data['retnum']
            EndDate = json_data['drawdateTo'] #or data[0]["multiDrawEndDate"] or None
            if data[0]['gameType'] == 3 or data[0]['gameType'] == 4 or data[0]['gameType']==8:
                try:
		    if Consecutive == 1:
                        enddrawTime = json_data['drawTimeTo']
                    else:
                        enddrawTime = None
		except:
		    enddrawTime = None
            else:
                enddrawTime = None

            if game_type in [3,4]:
                for item in lines:
                    item["multiplier"] = json_data["ismultiplier"]
            else:
                for item in lines:
                    item["multiplier"] = json_data["ismultiplier"]
                    item.pop('sumAmount')
                    item.pop('sumitUp')
                    item.pop('amount')
                    item.pop('lineType')
            
            updated_ocr_data = str({"lines":lines,"drawTime":json_data['drawTime'],"enddrawTime":enddrawTime})
            updated_ocr_data = updated_ocr_data.replace("None","null")
            updated_ocr_data = updated_ocr_data.replace("u'","'")
            updated_ocr_data = updated_ocr_data.replace("False","0")
            updated_ocr_data = updated_ocr_data.replace("True","1")
            updated_ocr_data = updated_ocr_data.replace("'lineType': 0","'lineType': 9")
        else:
            updated_ocr_data = ""
        valid_data_entry_game_type = DET_GAMES[game_type]
        url = 'http://52.6.245.123/TestService/DataEntryTool.WcfService.TicketService.svc/AddTicket'
        try:
            if multiDraw and Consecutive == 1:
                data = {"StateId":ticket.division_id,"DrawDate":str(ticket.draw.date),"GameTypeId":valid_data_entry_game_type,"PlayId":play.id,"ImageName":str(play.id)+"_1.jpg","OCRRowData":updated_ocr_data,"TicketId":ticket.id,"StartDate":StartDate,"EndDate":EndDate,"MultiCheck":multiDraw,"Consecutive":1,"RetailerNo":RetailerNo}
            elif multiDraw:
                data = {"StateId":ticket.division_id,"DrawDate":str(ticket.draw.date),"GameTypeId":valid_data_entry_game_type,"PlayId":play.id,"ImageName":str(play.id)+"_1.jpg","OCRRowData":updated_ocr_data,"TicketId":ticket.id,"StartDate":StartDate,"EndDate":EndDate,"MultiCheck":multiDraw,"Consecutive":0,"RetailerNo":RetailerNo}    
	    else:
                data = {"StateId":ticket.division_id,"DrawDate":str(ticket.draw.date),"GameTypeId":valid_data_entry_game_type,"PlayId":play.id,"ImageName":str(play.id)+"_1.jpg","OCRRowData":updated_ocr_data,"TicketId":ticket.id,"StartDate":"null","EndDate":"null","MultiCheck":0,"Consecutive":0,"RetailerNo":RetailerNo}
        except:           
            data = {"StateId":ticket.division_id,"DrawDate":str(ticket.draw.date),"GameTypeId":valid_data_entry_game_type,"PlayId":play.id,"ImageName":str(play.id)+"_1.jpg","OCRRowData":'',"TicketId":ticket.id,"StartDate":"null","EndDate":"null","MultiCheck":0,"Consecutive":0,"RetailerNo":''}

        headers = {"Content-Type": "application/json"}
        '''import logging

        LOG_FILENAME = 'logging_example.out'
        logging.basicConfig(filename=LOG_FILENAME,
                    level=logging.DEBUG,
                    )

        logging.debug(json.dumps(data))
        print 232323232323232323'''
        print "json_data",json.dumps(data)
        #aa = urllib2.Request(url,json.dumps(data),headers)
        #urllib2.urlopen(aa)
        
        return
    else:
        pass


def send_reject_notification(ticket_info,text,reason):
    log = ''
    user_devices = ticket_info.user.devices.all()
    try:
      for device in user_devices:
        if not device.device_token:
            log += "\nSkipped Device, No Token"
            continue

        if device.is_ios():
            apn = APNSender(device.device_token, text=text,custom={"code": "data_entry", "msg": reason,})
            apn.send()
            log += "\nAPN Outbound: %s" % device.device_token

        elif device.is_android():
            gcm = GCMSender(to=[device.device_token], data={"text": text,"code": "data_entry", "gameType": ticket_info.draw.component_id,"state":ticket_info.division.remote_id,"drawId":ticket_info.draw_id,"ticket_id":ticket_info.id,"msg":reason,})
            gcm.send()
            log += "\nGCM Outbound: %s" % device.device_token
    except:
      pass

class Play_Game(View):
    @rest
    @Authenticate(create=False)
    def post(self, request):
        
        from base64 import b64decode
        from django.core.files.base import ContentFile
        common_games=[0,1]# 0/Megamillion(TX),1/Powerball(TX)
        user = request.yoo["user"]
        #user = request.yoo["user"]
        #version = request.META["HTTP_YOO_APP_VERSION"]
        #global version
        old_version = False
        # Short-Circuit for Authentication Errors caused by invalid Device IDs
        if not request.yoo["user"] and request.yoo["auth"].get("__internal__reject__", False):
            raise exceptions.WebServiceAuthorizationFailed()
        try:
            data = process_req_body(json.loads(request.body)) 
            if not isinstance(data, list):
                raise RuntimeError()
        except:
            raise exceptions.WebServiceException("Invalid Ticket Data Format")

        if data[0]['state'] == 'CA' and data[0]['gameType'] == 0:
                game_type = 13
        elif data[0]['state'] == 'CA' and data[0]['gameType'] == 1:
                game_type = 11
        else:
            game_type = data[0]['gameType']
        games = {}
        success = False
        ticket = None
        for ticket in data:
            try:
                games[game_type] = EnumerationManager.game(game_type)
            except ValueError as e:
                raise exceptions.WebServiceException(str(e))
        tickets = {}
        allocated = {}
        plays = []
        result = []
        submission = uuid.uuid4().hex[:16]
        
        if ( request.META["HTTP_YOO_APP_VERSION"] in ['3.0.2','4.2.2'] and data[0]['state'] == 'TX' ) or not request.yoo['new_version']:
            for record in data:
                game_type=record["gameType"]
                game = games[game_type]#LotteryGame Obj
                handler = game.handler
                component = handler.get_component(record)
                try:
                    if not component:
                        component = game.components.all()[0]
                except:
                    continue

                date = datetime.datetime.strptime(record["drawingDate"], "%Y-%m-%d").date()
            if game_type in common_games:
                    common_division = LotteryCountryDivision.objects.get(remote_id="TX")
                    local_division = LotteryCountryDivision.objects.get(remote_id=record['state'])#TX,NY,AZ...(44)

                    # Retrieve Draw
		    try: 
                        common_draw = LotteryDraw.objects.filter(component=component, date=date,division_id=common_division.id)[0]
                    except:
		        try:
                            common_draw, created = LotteryDraw.objects.get_or_create(component=component, date=date,division_id=common_division.id)
	                except:
			    common_draw = LotteryDraw.objects.get(component=component, date=date,division_id=common_division.id)
		    print "the commmon draw is ###############################", common_draw.id
                    # Retrieve Ticket
                    ticket = LotteryTicket(user=user,draw=common_draw,division_id=local_division.id)
                    ticket.save()
                    submission_record = None
                    print "the user is ###############################", user.id
                    print "the ticket is ###############################", ticket.id

                    ticket_client, created = LotteryTicketClient.objects.get_or_create(device=str(request.yoo['device']).split(":")[1],draw=common_draw,email=client_login_record.client_login)

                    tickets[ticket.pk] = ticket


                    record = handler.preprocess_ticket(record)
                    invalid = []
                    #print "recorddd",record
                    for _play in record["lines"]:
                        # Sanitize Data
                        try:
                            handler.validate_play(_play)
                        except Exception as e:
                            invalid.append([_play, e])
                            continue

                        serialized = dumps(_play)

                        # Retrieve Play
                        play, created = LotteryTicketPlay.objects.get_or_create(ticket=ticket,
                            play=serialized,division_id=local_division.id)

                        _saved = False
                        if created:#new Play
                            if not submission_record:
                                submission_record, created = LotteryTicketSubmission.objects.get_or_create(
                                    submission=submission, ticket=ticket)
                                submission_record.save()

                            play.submission_old = submission
                            play.submission = submission_record

                        # Calculate Winnings (if applicable)
                        play.update_winnings(save=True)

                    if invalid:
                        raise LotteryPlayInvalidException(["%s: %s" % (x[0]["numbers"], x[1].args[0]) for x in invalid])
            else:
                    division = LotteryCountryDivision.objects.get(remote_id=record['state'])
            # Retrieve Draw
		    try:
                        draw, created = LotteryDraw.objects.get_or_create(component=component, date=date,division_id=division.id)
	            except:
		        draw = LotteryDraw.objects.get(component=component, date=date,division_id=division.id)

                    # Retrieve Ticket
                    ticket = LotteryTicket(user=user, draw=draw,division_id=division.id)
                    ticket.save()
                    submission_record = None

                    tickets[ticket.pk] = ticket


                    record = handler.preprocess_ticket(record)


                    invalid = []

                    for _play in record["lines"]:
                # Sanitize Data
                        try:
                            handler.validate_play(_play)
                        except Exception as e:
                            invalid.append([_play, e])
                            continue

                        serialized = dumps(_play)

                        # Retrieve Play
                        play, created = LotteryTicketPlay.objects.get_or_create(ticket=ticket,
                            play=serialized,division_id=division.id)

                        _saved = False
                        if created:
                            if not submission_record:
                                submission_record, created = LotteryTicketSubmission.objects.get_or_create(
                                    submission=submission, ticket=ticket)
                        play.submission_old = submission
                        play.submission = submission_record

                        # Calculate Winnings (if applicable)
                        play.update_winnings(save=True)

                    if invalid:
                        raise LotteryPlayInvalidException(["%s: %s" % (x[0]["numbers"], x[1].args[0]) for x in invalid])

            # Refresh Tickets
            for ticket in tickets.values():

                allocated[ticket.pk] = ticket.update(request.yoo["device"],client_login_record.client_login)
            # Return Tickets
            result = map(lambda x: x.representation(request.yoo["device"],request.META['HTTP_YOO_EMAIL_ID'],allocated=allocated), tickets.values())
            for _result in result:
                coins = allocated.get(_result["ticket_id"], None)
                if coins < 1:
                    coins = None

                _result["coins"] = coins

            return result





        else:
            try:
                image_data = bytearray(eval(data[0]['image']))
            except:
                from base64 import b64decode
                image_data = b64decode(data[0]['image'])
                old_version = True

            if data[0]['gameType'] == 3:
                data[0]['lines'] = [{"baseWager":"0.50","lineType":"ANY","numbers":[],"sum":None,"sumWager":None,"totalWager":"0.50"}]
            else:
                data[0]['lines'] = [{'amount': u'0.5', u'raceTime': u'', u'numbers': [], u'lineType': 0, u'multiplier': False}]
            for record in data:
                game = games[game_type]#LotteryGame Obj
                handler = game.handler
                component = handler.get_component(record)
                
                record.pop('image', 0)
                try:
                    if not component:
                        component = game.components.all()[0]
                except:
                    continue
                date = datetime.datetime.strptime(record["drawingDate"], "%Y-%m-%d").date()
                if game_type in common_games:
                    common_division = LotteryCountryDivision.objects.get(remote_id="TX")
                    local_division = LotteryCountryDivision.objects.get(remote_id=record['state'])#TX,NY,AZ...(44)
                    # Retrieve Draw
		    try:
			common_draw = LotteryDraw.objects.filter(component=component, date=date,division_id=common_division.id)[0]
		    except:
		        try:
                            common_draw, created = LotteryDraw.objects.get_or_create(component=component, date=date,division_id=common_division.id)
	                except:
			    common_draw = LotteryDraw.objects.get(component=component, date=date,division_id=common_division.id)
                    # Retrieve Ticket
                    ticket = LotteryTicket(user=user,draw=common_draw,division_id=local_division.id,deleted=False)
                    ticket.save()
                    #ticket_client, created = LotteryTicketClient.objects.get_or_create(device=request.yoo['device'],draw=common_draw,email=client_login_record.client_login)
                    play= LotteryTicketPlay.objects.create(ticket=ticket,division_id=local_division.id)
                    play.save()

                    available, created = LotteryTicketAvailable.objects.get_or_create(ticket=ticket,play=play,defaults={"json":record,"device":str(request.yoo['device'])})
                    available.image_first = ContentFile(image_data, str(play.id)+"_1.jpg")
                    available.gameType = game_type
                    available.save()
                else:
                    division = LotteryCountryDivision.objects.get(remote_id=record['state'])
                    # Retrieve Draw
		    try:
                        draw = LotteryDraw.objects.filter(component=component, date=date,division_id=division.id)[0]
		    except:
		        try:
		            draw, created = LotteryDraw.objects.get_or_create(component=component, date=date,division_id=division.id)
	                except:
			    draw = LotteryDraw.objects.get(component=component, date=date,division_id=division.id)
		    #Retrieve Ticket

                    ticket = LotteryTicket(user=user, draw=draw,division_id=division.id,deleted=False)
                    ticket.save()
                    #ticket_client, created = LotteryTicketClient.objects.get_or_create(device=request.yoo['device'],draw=draw,email=client_login_record.client_login)
                    play= LotteryTicketPlay.objects.create(ticket=ticket,division_id=division.id)
                    play.save()

                    available, created = LotteryTicketAvailable.objects.get_or_create(ticket=ticket,play=play,defaults={"json":record,"device":str(request.yoo['device'])})
                    available.image_first = ContentFile(image_data, str(play.id)+"_1.jpg")
                    available.gameType = game_type
            available.save()                 

            success = True
            thread.start_new_thread( send_data_to_det, (success,ticket,play,game_type,image_data,data[0]['state'],old_version,data) )
            return {"success":success}



class SubmitAgain(View):

    def get_draws(self,all_dates,component,common_state,game_type,consecutive,end_component,handler):
        dates = [datetime.datetime.strptime(each_date, "%Y-%m-%d").date() for each_date in all_dates]
        print dates
        draws = []
        if game_type == 7 or game_type == 4 or game_type == 3:
            if consecutive:
                dates = dates[::-1]
                start_component = component
                end_component = end_component

                next_components = handler.get_next_components(start_component)
                previous_components = handler.get_previous_components(end_component)
                all_components = handler.get_all_components()

                for item in range(len(dates)):
                    if item != 0 and item != len(dates)-1:
                        for each_component in all_components:
                            try:
                                updated_draw = LotteryDraw.objects.filter(component=each_component,division_id=common_state,date=dates[item])
                            except:
                                try:
                                    updated_draw, created = LotteryDraw.objects.get_or_create(component=each_component,division_id=common_state,date=dates[item])
                                except:
                                    updated_draw = LotteryDraw.objects.get(component=each_component,division_id=common_state,date=dates[item])
                            draws.append(updated_draw)
                    elif item == 0:
                        for each_component in next_components:
                            print each_component
                            try:
                                updated_draw = LotteryDraw.objects.filter(component=each_component,division_id=common_state,date=dates[item])
                            except:
                                try:
                            	    updated_draw, created = LotteryDraw.objects.get_or_create(component=each_component,division_id=common_state,date=dates[item])
                                except:
                                    updated_draw =  LotteryDraw.objects.get(component=each_component,division_id=common_state,date=dates[item])
                            draws.append(updated_draw)

                    elif item == len(dates)-1:
                        for each_component in previous_components:
                            try:
                                updated_draw = LotteryDraw.objects.filter(component=each_component,division_id=common_state,date=dates[item])[0]
                            except:
                                try:
                                    updated_draw, created = LotteryDraw.objects.get_or_create(component=each_component,division_id=common_state,date=dates[item])
                                except:
                                    updated_draw = LotteryDraw.objects.get(component=each_component,division_id=common_state,date=dates[item])
                            draws.append(updated_draw)    
            else:
                all_dates.pop(0)
                for date in dates:
                    try:
                        updated_draw = LotteryDraw.objects.filter(component=component,division_id=common_state,date=date)[0]
                    except:
                        try:
                            updated_draw, created = LotteryDraw.objects.get_or_create(component=component,division_id=common_state,date=date)
                        except:
                            updated_draw = LotteryDraw.objects.get(component=component,division_id=common_state,date=date)
                    draws.append(updated_draw)
        else:
            print "aaaaaaaaaalllllllll",all_dates
            all_dates.pop(0)
            print "datesssssssssssssssssssss",dates
            for date in dates:
                print "componennnnnnnnnnnt",component.id
                print "coimmmmmmmmmmmm state",common_state
                print "dateeeeee",date
                try:
                    updated_draw = LotteryDraw.objects.filter(component=component,division_id=common_state,date=date)[0]
                    print "upddd",updated_draw
                except:
                    try:
                        updated_draw, created = LotteryDraw.objects.get_or_create(component=component,division_id=common_state,date=date)
                        print "iesisdjj",updated_draw
                    except:
                        updated_draw = LotteryDraw.objects.get(component=component,division_id=common_state,date=date)
                        print "asjjjjjjjjjjjjjj",updated_draw
                draws.append(updated_draw)
        return draws

    @rest
    def post(self,request):
      
        from yoolotto.util import currency
        import itertools
        end_component = 1
        # - parse json
        data = json.loads(request.body)
        print "dataaaaaaaaa",data
        valid = data['valid']
        state_codes={
             "TX":0,
             "CA":2,
             "AZ":3,
             "AR":4,
             "CO":5,
             "CT":6,
             "DE":7,
             "DC":8,
             "FL":9,
             "GA":10,
             "ID":11,
             "IL":12,
             "IN":13,
             "IA":14,
             "KS":15,
             "KY":16,
             "LA":17,
             "ME":18,
             "MD":19,
             "MA":20,
             "MI":21,
             "MN":22,
             "MO":23,
             "MT":24,
             "NE":25,
             "NH":26,
             "NJ":27,
             "NM":28,
             "NY":29,
             "NC":30,
             "ND":31,
             "OH":32,
             "OK":33,
             "OR":34,
             "PA":35,
             "RI":36,
             "SC":37,
             "SD":38,
             "TN":39,
             "VT":40,
             "VA":41,
             "WA":42,
             "WI":43,
             "WV":44,
         "WY":45
             }
        ticket_id = data['ticket']
    #version = request.META["HTTP_YOO_APP_VERSION"]
        try:
            ticket_info = LotteryTicket.objects.get(id=ticket_id,deleted=False)
        except:
            return
        user = ticket_info.user
        play_id = data['playid']
        availability = LotteryTicketAvailable.objects.filter(play=play_id)[0]
        data1 = ast.literal_eval(availability.json)
        ticket_device = availability.device
        # - if valid
        if valid:

            
            # - get ticket info
            
            availability.pending = 0
            availability.save()            
            all_dates1 = data['drawdate'].split(",")
            all_dates = all_dates1[::-1]            
            defected = data["imagequality"]
            defected_ticket = False
            if defected == "No":
                defected_ticket = True
            draw_date = all_dates[0]
            data['drawdate'] = all_dates[0]
            division = data['state']
            common_state = 1
            if division == 'CA':
                common_state = 2
            game_type_id = data['gametypeid']
            draw_time = data['drawTime']
            lines = []
            for item in data['lines']:
                lines.append(json.loads(json.dumps(item)))
            
            submission_record = None
            submission = uuid.uuid4().hex[:16]

            
            

            # - parse game type id
            if division == 'CA':
                game_types = {1:11,2:13}
                components = {1:"Powerballca",2:"MegaMillionsCA"}
            else:
                game_types = {1:1,4:6,8:7,7:5,6:4,3:2,5:3,2:0}
                components = {1:"Powerball",4:"TwoStep",7:"CashFive",3:"LottoTexas",2:"MegaMillions"}

            # - get game type
            game_type = game_types[game_type_id]

            # - get handler
            games = {}
            record = {}
            allocated = {}
            tickets = {}
            games[game_type] = EnumerationManager.game(game_type)
            game = games[game_type]#LotteryGame Obj
            handler = game.handler

            # - get component

            if game_type == 7 or game_type == 4 or game_type == 3:
                record = {'drawTime':draw_time}
                component = handler.get_component(record)
                end_component = None
                if data["Consecutive"]:
                    print "hey there....................."
                    record_copy = record
                    print "hey there....................."
                    record_copy["drawTime"] = data["enddrawTime"]
                    print "hey there....................."
                    end_component = handler.get_component(record_copy)
                    print "hey there....................."
                #baseWager, sum, sumWager
                if game_type == 3:
                    enums = {1: "SUM",8: "ANY",9: "COMBO",10: "EXT",11: "EXTANY",}
                elif game_type == 4:
                    enums = {1: "SUM",2: "STR",3: "BOX",4: "STRBOX",5: "FRONT",6: "MID",7: "BACK",9: "COMBO"}
                
                if game_type == 3:
                    for line in lines:
                        line['sum'] = line.pop('sumitUp')
                        line['sumWager'] = line.pop('sumAmount')
                        line['baseWager'] = line['amount']
                        line['lineType'] = enums[line['lineType']]
                        line['totalWager'] = line['amount']

                    if line["lineType"] == "COMBO":
                                    numbers = line['numbers']
                                    if line['sum'] != None:
                                        numbers = [line['sum']]
                                        line["baseWager"] = currency.format(float(line["amount"]) / len(set(itertools.permutations(numbers))))
                    elif line["lineType"] in ["STRBOX", "EXTANY"]:
                        line["baseWager"] = currency.format(float(line["amount"]) / 2)
                    else:
                        line["baseWager"] = currency.format(line["amount"])

                elif game_type == 4:

                    for line in lines:
                        line['sum'] = line.pop('sumitUp')
                        line['sumWager'] = line.pop('sumAmount')
                        line['baseWager'] = line['amount']
                        line['lineType'] = enums[line['lineType']]
                        line['totalWager'] = line['amount']

                    if line["lineType"] == "FRONT":
                        line["numbers"] = line["numbers"][0:2]+[0,0]
                    elif line["lineType"] == "MID":
                        line["numbers"] = [0]+line["numbers"][1:3]+[0]
                    elif line["lineType"] == "BACK":
                        line["numbers"] = [0,0]+line["numbers"][2:4]

                    if line["lineType"] == "COMBO":
                        numbers = line['numbers']
                        if line['sum'] != None:
                            numbers = [line['sum']]
                            line["baseWager"] = currency.format(float(line["amount"]) / len(set(itertools.permutations(numbers))))
                        elif line["lineType"] in ["STRBOX", "EXTANY"]:
                            line["baseWager"] = currency.format(float(line["amount"]) / 2)
                        else:
                            line["baseWager"] = currency.format(line["amount"])

                else:
                        for line in lines:
                            line['sum'] = line.pop('sumitUp')
                            line['sumWager'] = line.pop('sumAmount')
                            line['baseWager'] = line['amount']
                            line['totalWager'] = line['amount']

            

            else:
                        component = LotteryGameComponent.objects.get(identifier=components[game_type_id])
                        for line in lines :
                            line.pop('sumitUp')
                            line.pop('sumAmount')
                            line.pop('lineType')
                            line.pop('amount')
                            line['multiplier'] = data['ismultiplier']


            # - get updated draw
            date = datetime.datetime.strptime(draw_date, "%Y-%m-%d").date()
	    try:
                updated_draw = LotteryDraw.objects.filter(component=component,division_id=common_state,date=date)[0]
            except:
	        try:
		    updated_draw, created = LotteryDraw.objects.get_or_create(component=component,division_id=common_state,date=date)
	        except:
		    updated_draw = LotteryDraw.objects.get(component=component,division_id=common_state,date=date)
	    ticket_user = ticket_info.user

            # - get record
            # - perform validation
            handler.preprocess_ticket(data)
            for item in lines :
                handler.validate_play(item)
            if data["multiCheck"] != 1 and data["Consecutive"] != 1:
            # - if draw is diffrent
                if updated_draw.id != ticket_info.draw.id :
                    print "Ticket is Created in the outer function"
                    ticket_info.delete()
                    availability.delete()
                    ticket_info = LotteryTicket(deleted=False,user=ticket_user,draw=updated_draw,division=LotteryCountryDivision.objects.get(remote_id=division))
                    ticket_info.save()
                    valid_draw = updated_draw.id
                    draw_done = updated_draw
                    valid_ticket = ticket_info.id
                    tickets[valid_ticket] = ticket_info
                    new_ticket_info = ticket_info
                    notified_ticket = ticket_info.id
                    notified_draw = ticket_info.draw.id

                    submission_record, created = LotteryTicketSubmission.objects.get_or_create(submission=submission, ticket_id=valid_ticket)
                    submission_record.save()
                    print "the ticket id is ", new_ticket_info.id
                    #previous_play = LotteryTicketPlay.objects.get(id=play_id)
                    #previous_play.delete()
                    # create new play
                    for line in lines:
                        serialized = dumps(line)
                        play_record, created = LotteryTicketPlay.objects.get_or_create(play=serialized,ticket=new_ticket_info,division=LotteryCountryDivision.objects.get(remote_id=division))
                        play_record.submission_old = submission
                        play_record.submission = submission_record
                        print "the play id is ", play_record.id
                        play_record.update_winnings(save=True)


                        line['gameType'] = game_type
                        try:
                            req_json = {"gameType": data["gametypeid"], "state": data["state"], "drawingDate": draw_done.date.strftime('%Y-%m-%d'), "Consecutive": data["Consecutive"], "multiDraw": data["multiCheck"], "drawTime": data["drawTime"], "RetailerNo": data["RetailerNo"], "multiDrawEndDate": data1["multiDrawEndDate"], "drawTimeTo": data1["drawTimeTo"]}
                        except:
                            req_json = {"gameType": data["gametypeid"], "state": data["state"], "drawingDate": draw_done.date.strftime('%Y-%m-%d'), "Consecutive": data["Consecutive"], "multiDraw": data["multiCheck"], "drawTime": data["drawTime"], "RetailerNo": data["RetailerNo"], "drawTimeTo": data1["drawTimeTo"]}
                        available_record, created = LotteryTicketAvailable.objects.get_or_create(ticket_id= valid_ticket, play_id=play_record.id)
                        available_record.available = True
                        req_json["lines"] = line
                        available_record.json = req_json
                        available_record.device = availability.device
                        available_record.image_first = "static/ticket/"+str(play_id)+"_1.jpg"
                        available_record.defected = defected_ticket
                        available_record.pending = False
                        available_record.gameType = game_type
                        available_record.device = ticket_device
                        available_record.save()

                    date = datetime.datetime.strptime(draw_date, "%Y-%m-%d").date()
		    try:
                        updated_draw = LotteryDraw.objects.filter(component=component,division_id=common_state,date=date)
		    except:
		        try:
			    updated_draw, created = LotteryDraw.objects.get_or_create(component=component,division_id=common_state,date=date)
	                except:
                            updated_draw = LotteryDraw.objects.get(component=component,division_id=common_state,date=date)
                else:	
                    print "Ticket is Created in the outer function"
                    print "in the other function"
                    valid_draw = ticket_info.draw.id
                    ticket_info.delete()
                    ticket_info = LotteryTicket(deleted=False,user=ticket_user,draw=updated_draw,division=LotteryCountryDivision.objects.get(remote_id=division))
                    ticket_info.save()
                    valid_draw = ticket_info.draw.id
                    valid_ticket = ticket_info.id
                    tickets[valid_ticket] = ticket_info
                    print "i'm also till here"
                    submission_record, created = LotteryTicketSubmission.objects.get_or_create(submission=submission, ticket_id=valid_ticket)
                    submission_record.save()
                    print "i cleared the first hurdle"
                    print "the play id till here is", play_id
                    #previous_play = LotteryTicketPlay.objects.get(id=play_id)
                    #previous_play.delete()
                    availability.delete()
                    notified_ticket = ticket_info.id
                    notified_draw = ticket_info.draw.id
                    # create new play
                    print "hey i got till here.. hooray...!!!!"
                    for line in lines:
                        serialized = dumps(line)
                        
                        play_record, created = LotteryTicketPlay.objects.get_or_create(play=serialized,ticket=ticket_info,division=LotteryCountryDivision.objects.get(remote_id=division))
                        play_record.submission_old = submission
                        play_record.submission = submission_record
                        play_record.update_winnings(save=True)
                        line['gameType'] = game_type
                        print "the play id is ", play_record.id
                        try:    
                            req_json = {"gameType": data["gametypeid"], "state": data["state"], "drawingDate": data["drawdate"], "Consecutive": data["Consecutive"], "multiDraw": data["multiCheck"], "drawTime": data["drawTime"], "RetailerNo": data["RetailerNo"], "multiDrawEndDate": data1["multiDrawEndDate"], "drawTimeTo": data1["drawTimeTo"]}
                        except:
                            req_json = {"gameType": data["gametypeid"], "state": data["state"], "drawingDate": data["drawdate"], "Consecutive": data["Consecutive"], "multiDraw": data["multiCheck"], "drawTime": data["drawTime"], "RetailerNo": data["RetailerNo"], "drawTimeTo": data1["drawTimeTo"]}
                        available_record, created = LotteryTicketAvailable.objects.get_or_create(ticket_id= valid_ticket, play_id=play_record.id)
                        available_record.available = True
                        available_record.json = line
                        available_record.device = availability.device
                        available_record.image_first = "static/ticket/"+str(play_id)+"_1.jpg"
                        available_record.defected = defected_ticket
                        available_record.pending = False
                        available_record.gameType = game_type
                        available_record.device = ticket_device
                        available_record.save()
                    print "till here also"
                # - send notification
            draws = []
            if data["Consecutive"]:
               print "i'm here"
               draws = self.get_draws(all_dates,component,common_state,game_type,data['Consecutive'],end_component,handler)
               previous_play = LotteryTicketPlay.objects.get(id=play_id)
               previous_play.delete()
               availability.delete()
               ticket_old = LotteryTicket.objects.get(id=ticket_id,deleted=False)
               ticket_old.delete()
               for draw in draws:
                  lines1 = lines[:]
                  print "ticket created inside multi....."
                  multi_ticket_info = LotteryTicket(deleted=False,user=ticket_user,draw=draw,division=LotteryCountryDivision.objects.get(remote_id=division))
                  multi_ticket_info.save()
                  ticket_info = multi_ticket_info
                  valid_ticket = multi_ticket_info.id
                  valid_draw = multi_ticket_info.draw.id
                  print "the ticket id is ", multi_ticket_info.id
                  print lines1
                  tickets[mutli_ticket_info.id] = multi_ticket_info

                  submission_record, created = LotteryTicketSubmission.objects.get_or_create(submission=submission, ticket_id=valid_ticket)
                  submission_record.save()
                  for line in lines1:
                      try:
                          line.pop("gameType")
                      except:
                          pass
                      serial = dumps(line)
                      
                      play_record, created = LotteryTicketPlay.objects.get_or_create(play=serial,ticket=multi_ticket_info,division=LotteryCountryDivision.objects.get(remote_id=division))
                      play_record.submission_old = submission
                      play_record.submission = submission_record
                      print "the play id is ", play_record.id
                      play_record.update_winnings(save=True)
                      try:
                        req_json = {"gameType": data["gametypeid"], "state": data["state"], "drawingDate": draw.date.strftime('%Y-%m-%d'), "Consecutive": data["Consecutive"], "multiDraw": data["multiCheck"], "drawTime": data["drawTime"], "RetailerNo": data["RetailerNo"], "multiDrawEndDate": data1["multiDrawEndDate"], "drawTimeTo": data1["drawTimeTo"]}
                      except:
                        req_json = {"gameType": data["gametypeid"], "state": data["state"], "drawingDate": draw.date.strftime('%Y-%m-%d'), "Consecutive": data["Consecutive"], "multiDraw": data["multiCheck"], "drawTime": data["drawTime"], "RetailerNo": data["RetailerNo"], "drawTimeTo": data1["drawTimeTo"]}
                      available_record, created = LotteryTicketAvailable.objects.get_or_create(ticket=multi_ticket_info,play=play_record)
                      available_record.available = True
                      req_json["lines"] = line
                      available_record.json= req_json
                      available_record.device = availability.device
                      available_record.image_first = "static/ticket/"+str(play_id)+"_1.jpg"
                      available_record.pending=False
                      available_record.gameType = game_type
                      available_record.device = ticket_device
                      available_record.save()    

            
                      #print play_record.play
            
            if data["multiCheck"] and not data["Consecutive"]:
               draws = self.get_draws(all_dates,component,common_state,game_type,data['Consecutive'],end_component,handler)
               print "drawsssssssssssssssss in multidraw",draws
               previous_play = LotteryTicketPlay.objects.get(id=play_id)
               previous_play.delete()
               availability.delete()
               ticket_old = LotteryTicket.objects.get(id=ticket_id,deleted=False)
               ticket_old.delete()
               for draw in draws:
                  lines1 = lines[:]
                  print "ticket created inside multi....."
                  multi_ticket_info = LotteryTicket(deleted=False,user=ticket_user,draw=draw,division=LotteryCountryDivision.objects.get(remote_id=division))
                  multi_ticket_info.save()
                  ticket_info = multi_ticket_info
                  valid_ticket = multi_ticket_info.id
                  #valid_draw = multi_ticket_info.draw.id
                  print "the ticket id is ", multi_ticket_info.id
                  print lines1
                  print multi_ticket_info
                  tickets[valid_ticket] = multi_ticket_info
                  submission_record, created = LotteryTicketSubmission.objects.get_or_create(submission=submission, ticket_id=valid_ticket)
                  submission_record.save()
                  for line in lines1:
                      try:
                          line.pop("gameType")
                      except:
                          pass
                      serial = dumps(line)
                      
                      play_record, created = LotteryTicketPlay.objects.get_or_create(play=serial,ticket=multi_ticket_info,division=LotteryCountryDivision.objects.get(remote_id=division))
                      play_record.submission_old = submission
                      play_record.submission = submission_record
                      print "the play id is ", play_record.id
                      play_record.update_winnings(save=True)
                      try:
                        req_json = {"gameType": data["gametypeid"], "state": data["state"], "drawingDate": draw.date.strftime('%Y-%m-%d'), "Consecutive": data["Consecutive"], "multiDraw": data["multiCheck"], "drawTime": data["drawTime"], "RetailerNo": data["RetailerNo"], "multiDrawEndDate": data1["multiDrawEndDate"], "drawTimeTo": data1["drawTimeTo"]}
                      except:
                        req_json = {"gameType": data["gametypeid"], "state": data["state"], "drawingDate": draw.date.strftime('%Y-%m-%d'), "Consecutive": data["Consecutive"], "multiDraw": data["multiCheck"], "drawTime": data["drawTime"], "RetailerNo": data["RetailerNo"], "drawTimeTo": data1["drawTimeTo"]}
                      available_record, created = LotteryTicketAvailable.objects.get_or_create(ticket=multi_ticket_info,play=play_record)
                      available_record.available = True
                      req_json["lines"] = line
                      available_record.json= req_json
                      available_record.device = availability.device
                      available_record.image_first = "static/ticket/"+str(play_id)+"_1.jpg"
                      available_record.pending=False
                      available_record.gameType = game_type
                      available_record.device = ticket_device
                      available_record.save()

            user_devices = ticket_info.user.devices.all()
            text = 'your ticket is available'
            if game_type_id == 11:
                gameType = 1
            elif game_type_id == 13:
                gameType = 2
            else:
                gameType = game_type_id

            try:
                user_client_record, created = UserClientLogin.objects.get_or_create(device=availability.device)
            except:
                try:
                    user_client_record = UserClientLogin.objects.filter(device=availability.device)[0]
                except:
                    pass
            multicoin = 0
            countt = len(tickets)
            available_device = LotteryTicketAvailable.objects.filter(ticket_id = ticket_info.id)[0]
            device_id1 = available_device.device
            device_id2 = device_id1.split(":")
            device_id = device_id2[1]
            print 
            email = user.email
            dev_id = Device.objects.filter(device_id = device_id)[0]
            version = dev_id.app_version
            if version <= "5.0.1": 
                for ticket in tickets.values():
                        allocated[ticket.pk] = ticket.update(availability.device,user_client_record.client_login)
            else:
                for ticket in tickets.values():
                        allocated[ticket.pk] = ticket.update1(multicoin,countt,availability.device,user.email)
                        multicoin = 1
            if version <= "4.2.6":
                result = map(lambda x: x.representation1(ticket_device,allocated=allocated), tickets.values())
            else:
                result = map(lambda x: x.representation(email,allocated=allocated), tickets.values())
            for _result in result:
                    coins = allocated.get(_result["ticket_id"], None)
                    if coins < 1:
                        coins = None

                    _result["coins"] = coins             

            try:
	    	print "innnnnnnnnnn tryyyyyyyyyyyyyyyyyy"
                print "userrrrrrrrrrr devices",user_devices
                notify= 1
                print "ticketssssssssssss",tickets
                
                for tickt in tickets.values():
                    if notify == 1:
                        notified_ticket = tickt.id
                        print "notifiesdd",notified_ticket
                        notified_draw = tickt.draw.id
                        notify = 0

                for device in user_devices:
                    if device.device_token is not None:
                        if device.is_ios():
                            apn = APNSender(device.device_token, text=text,
                                            custom={"code": "data_entry", "gameType": gameType,
                                                    "drawId":notified_draw, "state":state_codes[division],"ticket_id":notified_ticket
                                                    })
                            apn.send()
                        elif device.is_android():
                            gcm = GCMSender(to=[device.device_token], data={"text": text,
                                                                            "code": "data_entry", "gameType": gameType,
                                                                            "state":division,
                                                                            "drawId":notified_draw,
                                                                            "ticket_id":notified_ticket
                                                                            })

                            gcm.send()
            except:
                pass

    
        else:
            # - if reject
            
            # - send notification
            reason = data['RejectReason']
        #availability.pending = False
            availability.rejected = True
        #availability.pending = False
            availability.reason = reason
            availability.save()

            text = 'Your Ticket is Rejected'
            send_reject_notification(ticket_info,text,reason,)
            

        return {"sucess":True}



class EditData(View):
    @rest
    @Authenticate(create=False)
    #@transaction.commit_on_success
    def post(self, request):
        # parse json
        try:
            data = json.loads(request.body)
        except:
            raise exceptions.WebServiceException("Invalid Ticket Data Format")

        # get game_type and division from lotteryticketavailable
        games = {}
        availability = LotteryTicketAvailable.objects.get(play_id=data['lines'][0]['playid'])
        game_type_id = int(availability.gameType)
	#game_type_id = availability.ticket.draw.component.parent_id

        # mask game types and get draw time
        division = availability.play.ticket.division_id

        if division == 2:
            #det_enum = {1:11, 0:13}
            game_type = game_type_id
        else:
            det_enum = {1:1,0:0,2:2,3:3,7:7,4:4,8:7,6:6,5:5}
            game_type = det_enum[game_type_id]

        
        # get handler
        games = {}
        games[game_type] = EnumerationManager.game(game_type)
        game = games[game_type]#LotteryGame Obj
        handler = game.handler
        # perform validation
        lines = data['lines']
        pre_play = None
        if game_type == 3 or game_type == 4:
            ENUM = {
                        1: "SUM",
                        8: "ANY",
                        9: "COMBO",
                        10: "EXT",
                        11: "EXTANY",
                    }
            if game_type_id == 4:
                ENUM = {
                    1: "SUM",
                    2: "STR",
                    3: "BOX",
                    4: "STRBOX",
                    5: "FRONT",
                    6: "MID",
                    7: "BACK",
                    9: "COMBO"
                }
            for line in lines:
                if line['playid']!=0:
                    play_record = LotteryTicketPlay.objects.get(id=line['playid'])
                    amount = line['amount']
                    numbers = line['numbers']
                    lineType = line['lineType']
                    try:
                        json_record = json.loads(play_record.play)
                    except:
                        json_record = ast.literal_eval(play_record.play)
                    json_record['totalWager'] = amount
                    invalid = []
                    try:
                        handler.validate_numbers(numbers)
                    except Exception as e:
                        invalid.append([numbers, e])
                        
                    if invalid:
                        raise LotteryPlayInvalidException(["%s: %s" % (x[0][0], x[1].args[0]) for x in invalid])
                    json_record['numbers'] = numbers
                    json_record['lineType'] = ENUM[lineType]
                    LotteryTicketPlay.objects.filter(id=line['playid']).update(play=json_record)
                    pre_play = line['playid']
                else:
                    play_record = LotteryTicketPlay.objects.get(id=pre_play)
                    sumAmount = line['amount']
                    sumNumber = line['numbers'][0]
                    try:
                        json_record = json.loads(play_record.play)
                    except:
                        json_record = ast.literal_eval(play_record.play)
                    json_record['sumWager'] = sumAmount
                    json_record['sum'] = sumNumber
                    LotteryTicketPlay.objects.filter(id=pre_play).update(play=json_record)

        else:
            for record in data['lines']:
                play = record['playid']
                numbers = record['numbers']
                invalid = []
                try:
                    handler.validate_numbers(record['numbers'])
                except Exception as e:
                    invalid.append([record['numbers'], e])
                    
                if invalid:
                    raise LotteryPlayInvalidException(["%s: %s" % (x[0][0], x[1].args[0]) for x in invalid])
                
                try:
                    play_info = LotteryTicketPlay.objects.get(id=play)
                    ticket_info = LotteryTicket.objects.get(id=play_info.ticket.id)
                except:
                    raise exceptions.WebServiceException("Invalid Ticket ID")

                availability = LotteryTicketAvailable.objects.get(play=play)

                record = ast.literal_eval(availability.json)
                games[game_type] = EnumerationManager.game(game_type)
                game = games[game_type]#LotteryGame Obj
                handler = game.handler 
                ticket_edit_record = LotteryTicketEdit(available=availability,numbers=numbers)
                ticket_edit_record.save()
                lottery_ticket_record = LotteryTicketPlay.objects.get(id=play)
                play_data = lottery_ticket_record.play
                
                #play_data["numbers"] = numbers
                try:
                    multiplier = str(record['lines'][0]['multiplier'])
                except:
                    multiplier = str(None)
                lottery_ticket_record.play = "{'numbers': "+str(numbers)+", 'multiplier': "+multiplier+"}"
                lottery_ticket_record.save()


            
        transaction.commit()
        return {"success":True}
        # update play record
class Ticket(View):
    @rest
    @Authenticate()
    def get(self, request):
        user = request.yoo["user"]
        
        # Short-Circuit for Authentication Errors caused by invalid Device IDs
        if not request.yoo["user"] and request.yoo["auth"].get("__internal__reject__", False):
            return []

            
        game_type = request.GET.get("gameType", None)
        draw_id = request.GET.get("drawId", None)
        division = request.GET.get("division", None)
        state = division
        division = LotteryCountryDivision.objects.get(remote_id=division)
        version = request.META["HTTP_YOO_APP_VERSION"]        

        _filter = request.GET.get("ticketArchive", None)
        if not _filter:
            _filter = None
        elif _filter == "false":
            _filter = False
        else:
            _filter = True
                
        if game_type is None and draw_id is None:        
            #tickets = list(user.tickets.filter(division_id=division.id).exclude(winnings=None).order_by("-draw__date"))
            tickets = list(user.tickets.filter(division_id=division.id,deleted=False).order_by("-draw__date") | user.tickets.filter(division_id=division.id,deleted=False).exclude(draw__result=None).order_by("-draw__date"))

        elif draw_id:
            draw = LotteryDraw.objects.get(pk=draw_id)
            try:
                    tickets = user.tickets.filter(draw=draw,division=division,deleted=False)[0]
            except:
                    tickets = LotteryTicket.objects.filter(draw=draw,division=division,deleted=False)[0]
        #tickets = [ticket for ticket in tickets if ticket.id not in unavailable_tickets]
        
        
        elif game_type:
            if state == 'CA':
                if game_type == '0':
                    game_type = '13'
                elif game_type == '1':
                    game_type = '11'

            game = EnumerationManager.game(int(game_type))
            
            #tickets = user.tickets.filter(draw__component__parent=game,division_id=division.id).exclude(winnings=None).order_by("-draw__date")
            tickets = user.tickets.filter(draw__component__parent=game,division_id=division.id,deleted=False).exclude(winnings=None).order_by("-draw__date") | user.tickets.filter(draw__component__parent=game,division_id=division.id,deleted=False).exclude(draw__result = None).order_by("-draw__date")
            tickets = list(tickets)
        # Workaround for Ticket Checking Bug
        if not isinstance(tickets, list):
            if not tickets.winnings and tickets.draw.result:
                tickets.calculate_winnings()
                tickets.update_winnings()        
                tickets = LotteryTicket.objects.get(pk=tickets.pk)
        else:
            for i, ticket in enumerate(tickets):
                if ticket.all_checked is False and ticket.winnings is not None and ticket.draw.result and ticket.winnings:
                    ticket.winnings = None
        if version <= "4.2.6":
            available_tickets = LotteryTicketAvailable.objects.filter(ticket__user=user,available = False,rejected=False).values_list('ticket_id', flat=True)# | LotteryTicketAvailable.objects.filter(ticket__user=user,rejected = False).values_list('ticket_id', flat=True)
            try:
                for ti in tickets:
                    if ti.id in available_tickets:
                        tickets.remove(ti)
                    else:
                        pass
            except:
                pass
        else:
            pass   
        result = self._representation(tickets,version)
        if game_type is None and draw_id is None and _filter is not None:
            if _filter:
                return filter(lambda x: x["draw"]["uncheckedPlayCount"] == 0, result)

            else:
                return filter(lambda x: x["draw"]["uncheckedPlayCount"] > 0, result)
        try:
          for item in result:
                if item['game']['gameType'] == 13:
                    item['game']['gameType'] = 0
                elif item['game']['gameType'] == 11:
                    item['game']['gameType'] = 1
                elif item['game']['gameType'] == 10:
                    item['game']['gameType'] = 4
        except:
            if result['game']['gameType'] == 13:
                result['game']['gameType'] = 0
            elif result['game']['gameType'] == 11:
                result['game']['gameType'] = 1
            elif result['game']['gameType'] == 10:
                result['game']['gameType'] = 4

            
        if not len(result):
            result.append({"current_date":datetime.date.today().strftime("%Y-%m-%d")})
        try:
            for record in result['plays']:
                if len(record['play']['numbers']) == 3:
                    ENUM = {
                            1: "SUM",
                            8: "ANY",
                            9: "COMBO",
                            10: "EXT",
                            11: "EXTANY",
                        }
                elif len(record['play']['numbers']) == 4:
                    ENUM = {
                        1: "SUM",
                        2: "STR",
                        3: "BOX",
                        4: "STRBOX",
                        5: "FRONT",
                        6: "MID",
                        7: "BACK",
                        9: "COMBO"
                    }
                for k, v in ENUM.iteritems():
                        if v == record['play']["lineType"]:
                            record['play']["lineType"] = k
                            break
        except:
            pass
        return result
            
    def _representation(self, tickets,version):
        if version <= "4.2.6":
            if not isinstance(tickets, list):            
                return tickets.representation1()
              
            return map(lambda x: x.representation1(
                representations.TicketRepresentationShortList1), tickets)
        else:
            if not isinstance(tickets, list):            
                return tickets.representation()
              
            return map(lambda x: x.representation_old(
                representations.TicketRepresentationShortList_Old), tickets)

class YooTicket(View):
    @rest
    @Authenticate()
    def get(self, request):
        user = request.yoo["user"]
        
        # Short-Circuit for Authentication Errors caused by invalid Device IDs
        if not request.yoo["user"] and request.yoo["auth"].get("__internal__reject__", False):
            return []

            
        game_type = request.GET.get("gameType", None)
        draw_id = request.GET.get("drawId", None)
        division = request.GET.get("division", None)
        state = division
        division = LotteryCountryDivision.objects.get(remote_id=division)
        version = request.META["HTTP_YOO_APP_VERSION"]        

        _filter = request.GET.get("ticketArchive", None)
        if not _filter:
            _filter = None
        elif _filter == "false":
            _filter = False
        else:
            _filter = True
                
        if game_type is None and draw_id is None:        
            tickets = list(user.tickets.filter(division_id=division.id).exclude(winnings=None).order_by("-draw__date"))
            #tickets = list(user.tickets.filter(division_id=division.id,deleted=False).order_by("-draw__date") | user.tickets.filter(division_id=division.id,deleted=False).exclude(draw__result=None).order_by("-draw__date"))

        elif draw_id:
            draw = LotteryDraw.objects.get(pk=draw_id)
            try:
                    tickets = user.tickets.filter(draw=draw,division=division,deleted=False,pk=int(request.GET.get("ticketId", None)))
            except:
                    tickets = LotteryTicket.objects.filter(draw=draw,division=division,deleted=False,pk=int(request.GET.get("ticketId", None)))#0]
        #tickets = [ticket for ticket in tickets if ticket.id not in unavailable_tickets]
        
        
        elif game_type:
            if state == 'CA':
                if game_type == '0':
                    game_type = '13'
                elif game_type == '1':
                    game_type = '11'

            game = EnumerationManager.game(int(game_type))
        
            #tickets = user.tickets.filter(draw__component__parent=game,division_id=division.id).exclude(winnings=None).order_by("-draw__date")
            tickets = user.tickets.filter(draw__component__parent=game,division_id=division.id,deleted=False).exclude(winnings=None).order_by("-draw__date") | user.tickets.filter(draw__component__parent=game,division_id=division.id,deleted=False).exclude(draw__result = None).order_by("-draw__date")
            tickets = list(tickets)
        print "the tickets are...", tickets
        tickets = list(tickets)
        print isinstance(tickets, list)
        # Workaround for Ticket Checking Bug
        if not isinstance(tickets, list):
            if not tickets.winnings and tickets.draw.result:
                tickets.calculate_winnings()
                tickets.update_winnings()        
                tickets = LotteryTicket.objects.get(pk=tickets.pk)
        else:
            for i, ticket in enumerate(tickets):
                if ticket.all_checked is False and ticket.winnings is not None and ticket.draw.result and ticket.winnings:
                    ticket.winnings = None
        if version <= "4.2.6":
            available_tickets = LotteryTicketAvailable.objects.filter(ticket__user=user,available = False,rejected=False).values_list('ticket_id', flat=True)# | LotteryTicketAvailable.objects.filter(ticket__user=user,rejected = False).values_list('ticket_id', flat=True)
            try:
                for ti in tickets:
                    if ti.id in available_tickets:
                        tickets.remove(ti)
                    else:
                        pass
            except:
                pass
        else:
            pass   
        result = self._representation(tickets,request.META['HTTP_YOO_EMAIL_ID'],version)
        if game_type is None and draw_id is None and _filter is not None:
            if _filter:
                return filter(lambda x: x["draw"]["uncheckedPlayCount"] == 0, result)

            else:
                return filter(lambda x: x["draw"]["uncheckedPlayCount"] > 0, result)
        try:
          for item in result:
                if item['game']['gameType'] == 13:
                    item['game']['gameType'] = 0
                elif item['game']['gameType'] == 11:
                    item['game']['gameType'] = 1
                elif item['game']['gameType'] == 10:
                    item['game']['gameType'] = 4
        except:
            if result['game']['gameType'] == 13:
                result['game']['gameType'] = 0
            elif result['game']['gameType'] == 11:
                result['game']['gameType'] = 1
            elif result['game']['gameType'] == 10:
                result['game']['gameType'] = 4

            
        if not len(result):
            result.append({"current_date":datetime.date.today().strftime("%Y-%m-%d")})
        try:
            for record in result['plays']:
                if len(record['play']['numbers']) == 3:
                    ENUM = {
                            1: "SUM",
                            8: "ANY",
                            9: "COMBO",
                            10: "EXT",
                            11: "EXTANY",
                        }
                elif len(record['play']['numbers']) == 4:
                    ENUM = {
                        1: "SUM",
                        2: "STR",
                        3: "BOX",
                        4: "STRBOX",
                        5: "FRONT",
                        6: "MID",
                        7: "BACK",
                        9: "COMBO"
                    }
                for k, v in ENUM.iteritems():
                        if v == record['play']["lineType"]:
                            record['play']["lineType"] = k
                            break
        except:
            pass
        return result
            
    def _representation(self,tickets,email,version):
        if version <= "4.2.6":
            if not isinstance(tickets, list):            
                return tickets.representation1(email)
              
            return map(lambda x: x.representation1(email,
                representations.TicketRepresentationShortList1), tickets)
        else:
            if not isinstance(tickets, list):            
                return tickets.representation(email)
              
            return map(lambda x: x.representation(email,
                representations.TicketRepresentationShortList), tickets)        

    
class TicketCheck(View):
    @rest
    @Authenticate(create=False)
    def post(self, request, _id):
        user = request.yoo["user"]
        print "~~~~id from frontend...... ", _id
        ticket = LotteryTicket.objects.get(pk=_id)
        print "ticket jo utha rhe hain.....", ticket.id
        if ticket.user_id != user:
            raise exceptions.WebServiceAuthorizationFailed()
        
        if ticket.draw.result:
            for submission in ticket.submissions.all():
                submission.checked = True
                submission.save()
        
        allocated = ticket.update(full=True)
        ticket = LotteryTicket.objects.get(pk=_id)
        
        _result = ticket.representation(request.yoo["device"],request.META['HTTP_YOO_EMAIL_ID'])
        
        _result["coins"] = allocated
            
        return _result
    
    def put(self, *args, **kwargs):
        return self.post(*args, **kwargs)
    
class TicketShare(View):
    @rest
    @Authenticate(create=True)
    def get(self, request, _id):
        user = request.yoo["user"]
        ticket = LotteryTicket.objects.get(pk=_id)
        
        if ticket.user != user:
            raise exceptions.WebServiceAuthorizationFailed()
        
        shares = ticket.coin_share_transaction.all()
        
        return map(lambda x: x.type, shares)
    
    @rest
    @Authenticate(create=False)
    def post(self, request, _id):
        user = request.yoo["user"]
        
        ticket = LotteryTicket.objects.get(pk=_id)
        
        if ticket.user != user:
            raise exceptions.WebServiceAuthorizationFailed()
        
        try:
            data = json.loads(request.body)
        except:
            data = {}
        
        type = data.get("type", None)
        if type not in ["facebook", "twitter"]:
            raise exceptions.WebServiceException("Unsupported Share Type")
        
        if not ticket.coin_share_transaction.filter(type=type).exists():
            parent = CoinTransaction(wallet=user.get_wallet())
            parent.save()
            
            transaction = CoinShareTransaction(ticket=ticket, type=type, transaction=parent)
            transaction.save()
            
            parent.amount = transaction.amount
            parent.save()
            
        return self.get(request, _id)
    
    def put(self, *args, **kwargs):
        return self.post(*args, **kwargs)


def process_req_body(req_body):
    '''
    ex:- daily3 drawTime:5
    [{u'drawTime': 3,
     u'state': u'CA',
     u'lines': [{u'amount': u'1.0', u'numbers': [2, 9, 3], u'lineType': 2, u'multiplier': False}],
     u'drawingDate': u'2014-01-24', u'gameType': 12}
    ]
    '''
    
    if req_body[0]['gameType']==12 and req_body[0]['drawTime']==5:
        
        return [{'drawTime': dt,
                  'state': req_body[0]['state'],
                  'lines': req_body[0]['lines'],
                  'drawingDate': req_body[0]['drawingDate'],
                  'gameType': 12} for dt in [3,4]]
        
    else:
        return req_body


class TicketDelete(View):
    @rest
    @Authenticate()
    def get(self, request, _id):
        user = request.yoo["user"]
        ticket = LotteryTicket.objects.get(pk=_id)
    
        if ticket.user != user:
            raise exceptions.WebServiceAuthorizationFailed()
        

        ticket.deleted = True
        ticket.save()
        
        return {"sucess":True}

class enumeration_data(View):
    @rest
    @Authenticate()
    def get(self,request):
        NUMBERS_MONEY={"Powerball":["5 numbers +ball $1,000,000 cash","5 numbers       $    5,000 cash","4 numbers +ball $      500 cash","4 numbers       $       10 cash","3 numbers +ball @   100 yoocoins","3 numbers      @    7 yoocoins","2 numbers +ball @    7 yoocoins","1 numbers +ball @    4 yoocoins","ball            @    4 yoocoins"],"Megamillion":["5 numbers +ball $1,000,000 cash","5 numbers       $    5,000 cash","4 numbers +ball $      500 cash","4 numbers       $       10 cash","3 numbers +ball @   50 yoocoins","3 numbers      @    5 yoocoins","2 numbers +ball @    5 yoocoins","1 numbers +ball @    2 yoocoins","ball            @    1 yoocoins"]}
        
        try:
            coins_record, created = EmailCoins.objects.get_or_create(email= request.META['HTTP_YOO_EMAIL_ID'], defaults={'coins': 0})
        except:
            coins_record = EmailCoins.objects.filter(email= request.META['HTTP_YOO_EMAIL_ID'])
        
        total_coins = coins_record.get_coins()
        dollar_amount = total_coins/50

        return {"numbers_money":NUMBERS_MONEY,"total_coins":total_coins,"dollar_amount":dollar_amount}


def fantasy_validate_numbers(numbers,game_type):
        if not numbers:
            raise LotteryPlayInvalidException("No number detected in white ball")
        
        if len(numbers)<5:
            raise LotteryPlayInvalidException("Please enter all white ball numbers")
        
        if len(numbers)==5:
            raise LotteryPlayInvalidException("Please enter Megaball number")
        white = numbers[0:5]
        powerball = numbers[5]
        if len(set(white)) != 5:
            raise LotteryPlayInvalidException("Duplicate Number %s" % white)
        if game_type == 0 or game_type == 13:#megamillion
            for number in white:
                if number not in xrange(1, 76):
                    raise LotteryPlayInvalidException("Please enter valid white ball number")
            
            if powerball not in xrange(1, 16):
                raise LotteryPlayInvalidException("Please enter valid Megaball number")    
              
        if game_type == 1 or game_type == 11:
            for number in white:
                    if number not in xrange(1, 60): 
                        raise LotteryPlayInvalidException("Invalid White Ball Number %s" % number)

                    if powerball != -1:
                
                        if powerball not in xrange(1, 36):
                            raise LotteryPlayInvalidException("Invalid Powerball Number %s" % powerball) 
        return True 

class QuickPick(View):
    @rest
    @Authenticate()
    def post(self,request):
        data = json.loads(request.body)
        game_type = data["game_type"]
        division = data['division']
        lines_no = data['lines']
        numbers = []
        if game_type == 0 or game_type == 13:#megamillion
            for line in range(0,lines_no):
                import random
                white_ball = random.sample(range(1,76),5)
                power_ball = random.sample(range(1,16),1)
                numbers1 = white_ball + power_ball
                numbers.append(numbers1)
        else:
            for line in range(0,lines_no):
                import random
                white_ball = random.sample(range(1,60),5)
                power_ball = random.sample(range(1,36),1)
                numbers1 = white_ball + power_ball
                numbers.append(numbers1)

        return {"numbers":numbers}

class SubmitNumbers(View):
    @rest
    @Authenticate()
    def post(self,request):
        data = json.loads(request.body)
        numbers = data['numbers']
        remove_play = data['remove_play']
        play_list = data['play_list']
    	game_type = data["game_type"]
    	lines_no = data["lines"]
        for i in numbers:
                fantasy_validate_numbers(i,game_type)
        if game_type == 0:
                coins = 1 * lines_no
        else:
                coins = 2 * lines_no
        if remove_play:
            remove_play_info = LotteryTicketPlay.objects.filter(id__in=play_list).delete()
            remove_available_info = LotteryTicketAvailable.objects.filter(play_id__in = play_list).delete()    
            coins_info = EmailCoins.objects.filter(email = request.META['HTTP_YOO_EMAIL_ID'])[0]
            total_coins = coins_info.coins 
            return {"success":True,"coins":coins,"total_coins":total_coins}
        else:
            numbers = data['numbers']
            
            user = request.yoo["user"]
            user_id = user.id
            game_type = data["game_type"]
            division = data["division"]
            draw_date = data["drawingDate"]
            if division == 'CA' and game_type == 0:
                    game_type = 13
            elif division == 'CA' and game_type == 1:
                    game_type = 11
            else:
                game_type = data["game_type"]
            games = {}
            try:
                    games[game_type] = EnumerationManager.game(game_type)
            except ValueError as e:
                    raise exceptions.WebServiceException(str(e))
            game = games[game_type]#LotteryGame Obj
            handler = game.handler
            component = handler.get_component1()
            try:
                if not component:
                    component = game.components.all()[0]
            except:
                pass
            if division =='CA':
                state_id = 2
            else:
                state_id = 1
            print "gameeetypeeeeee",game_type
            print "component iddsssssssssssssssssssssssssssssssd",component.id
            #handler.validate_numbers(numbers)
            submission_record = None
            submission = uuid.uuid4().hex[:16]
            date = datetime.datetime.strptime(draw_date, "%Y-%m-%d").date()
            division = LotteryCountryDivision.objects.get(remote_id = division)
	    try:            
		draw = LotteryDraw.objects.filter(component=component, date=date,division_id=state_id)[0]
            except:
	        try:
		    draw, created = LotteryDraw.objects.get_or_create(component=component, date=date,division_id=state_id)
                except:
		    draw = LotteryDraw.objects.get(component=component, date=date,division_id=state_id)
	    print "drawww",draw.id
            ticket_info = LotteryTicket(user_id = user_id,division_id = division.id,draw_id = draw.id,fantasy = True)
            ticket_info.winnings = 0
            ticket_info.save()
            print ticket_info.id
            submission_record, created = LotteryTicketSubmission.objects.get_or_create(submission=submission, ticket_id=ticket_info.id)
            submission_record.save()

            # create new play
            for line in numbers:
                lines =  {"multiplier":False,"numbers":line}
                serialized = dumps(lines)
                play_record = LotteryTicketPlay(play=serialized,ticket_id=int(ticket_info.id),division_id = division.id)
                play_record.submission_old = submission
                play_record.submission = submission_record
                play_record.save()
                ticket_available,created= LotteryTicketAvailable.objects.get_or_create(ticket_id = ticket_info.id,play_id = play_record.id,gameType = game_type,available = True,device = str(request.yoo['device']))
                play_record.update_winnings(save=True)
                play_record.save()
                winnings_money = float(play_record.winnings or 0)
                print "eiiiiiii",winnings_money
                winnings_coins1 = float(play_record.winnings_coins or 0)
                print "dnnnnnnnn",winnings_coins1
                if winnings_money > ticket_info.winnings:
                    print "ticket winngs",ticket_info.winnings
                    ticket_info.winnings = winnings_money
                    print ticket_info.winnings
                    ticket_info.winnings_coins = 0
                if winnings_coins1 > ticket_info.winnings_coins and ticket_info.winnings == 0:
                    ticket_info.winnings_coins = winnings_coins1
                ticket_info.save()
            game_coins = coins
            coins_info = EmailCoins.objects.filter(email = request.META['HTTP_YOO_EMAIL_ID'])[0]
            #coins_info.coins = coins_info.coins + float(play_record.winnings_coins)
            #coins_info.save()
            total_coins = coins_info.coins
            play_id_info = LotteryTicketPlay.objects.filter(ticket_id = ticket_info.id)
            play_id = []
            for i in play_id_info:
                id1 = i.id
                play_id.append(id1)
            print "playyyyyyyyyyyyyyyyyyyyyyyy",play_id
        return {"success":True,"coins":game_coins,"play_id_list":play_id,"total_coins":total_coins,"ticket_id":ticket_info.id}
