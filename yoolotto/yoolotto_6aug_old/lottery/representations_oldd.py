import json
import uuid 
from yoolotto.user.models import *
from yoolotto.coin.models import *
from django.db.models import F

class TicketRepresentation(object):
    def __init__(self, ticket):
        self.ticket = ticket
        self.plays = self.ticket.plays.all()
        
class TicketRepresentationShortList(TicketRepresentation):
    def __call__(self, *args, **kwargs):
        import datetime
        from yoolotto.lottery.enumerations import EnumerationManager
        from yoolotto.lottery.models import LotteryGameComponent
        draw = self.ticket.draw
        plays = self.ticket.plays.exclude(play=None)
        handler = draw.component.parent.handler
        lg_obj = LotteryGameComponent.objects.filter(parent=draw.component.parent.pk)[0]
        state = self.ticket.division.remote_id   
        fantasy = self.ticket.fantasy
        
        _result = {
            "game": {
                "id": draw.component.parent.pk,
                "name": draw.component.parent.name,
                "gameType": EnumerationManager.game_reverse(draw.component.parent.pk),
                "state":state,
            },
            "current_date":datetime.date.today().strftime("%Y-%m-%d"),
            #"plays": self.ticket.plays.count(),
            "plays": [],
            "draw": draw.representation(ticket=self.ticket),
            "ticket_id": self.ticket.pk,
            "winnings": str(self.ticket.winnings) if self.ticket.winnings is not None else None,
            "coins": self.ticket.coin_representation(),
            "checked": self.ticket.all_checked,
            "representation": self.__class__.__name__,
            "fantasy":fantasy
        }
        '''pending = False
        try:
            if not self.ticket.ticket_submissions.all()[0].available and not self.ticket.ticket_submissions.all()[0].rejected:
                pending = True
        except:
            pending = True'''
        if fantasy == False:
            try:
                if not self.ticket.all_checked and not self.ticket.draw.result:
                    _result["gameState"] = 0
                elif not self.ticket.all_checked and self.ticket.draw.result :
                    _result["gameState"] = 1
                elif self.ticket.all_checked and self.ticket.draw.result and not self.ticket.ticket_submissions.all()[0].pending:
                    _result["gameState"] = 2
                elif self.ticket.ticket_submissions.all()[0].rejected:
                    _result["gameState"] = 3
                elif not self.ticket.ticket_submissions.all()[0].available and not self.ticket.ticket_submissions.all()[0].rejected:
                    _result["gameState"] = 4
            except:
                pass
            _result["game"].update(handler.get_game_meta(draw.component))
            for play in plays:
                ticket_image = self.ticket.ticket_submissions.all()
                if ticket_image :
                    image = str(ticket_image[0].image_first)
                else:
                    image = None
                try:
                    play_data = json.loads(play.play)
                    raw = handler.postprocess_play(play_data)
                except:
                    play_data = json.loads(json.dumps(play.play))
                    raw = handler.postprocess_play(play_data)
                try:
                    raw_data = json.loads(raw)
                except:
                    raw_data = eval(str(raw))
                    _play = {
                        "play_id": play.pk,
                        "winnings": str(play.winnings) if play.winnings is not None else None,
                        "play": raw_data,
                        "checked":play.submission.checked,
                        "submission": play.submission_old,
                "image": image,
                    }
                    
                    _play["baseWinnings"] = str(play.winnings_base) if play.winnings_base else _play["winnings"]
                    _play["sumWinnings"] = str(play.winnings_sum) if play.winnings_sum else None
                    
                _result["plays"].append(_play)
        else:
            count = 0
            for play in plays:
                try:
                    play_data = json.loads(play.play)
                    raw = handler.postprocess_play(play_data)
                except:
                    play_data = json.loads(json.dumps(play.play))
                    raw = handler.postprocess_play(play_data)
                try:
                    raw_data = json.loads(raw)
                except:
                    raw_data = eval(str(raw))
                    _play = {
                        "play_id": play.pk,
                        "winnings": str(play.winnings) if play.winnings is not None else None,
                        "play": raw_data,
                        "checked":play.submission.checked,
                        "submission": play.submission_old,
                    }
                count = count + 1   
                _result["plays"].append(_play)
            device_info = self.ticket.ticket_submissions.all()[0].device
            print device_info
            email_info = UserClientLogin.objects.filter(device = device_info)[0]
            print "email id",email_info.device
            print "device id is ################################################3", device_info
            print email_info.client_login
            device_coins = DeviceCoins.objects.filter(device_id = device_info)[0]
            coins_info = EmailCoins.objects.filter(email = email_info.client_login)[0]
            from yoolotto.lottery.models import LotteryTicketAvailable
            if self.ticket.ticket_submissions.all()[0].pending == 1:
                if self.ticket.ticket_submissions.all()[0].gameType == 0 or self.ticket.ticket_submissions.all()[0].gameType == 13:
                    if device_coins.coins + coins_info.coins >= count *1:
                        if coins_info.coins >= count * 1:    
                            coins_info = F('coins')- count *1
                            coins_info.save()
                        else:
                            emailcoinsdeducted = coins_info.coins
                            coins_info.coins = 0.0
                            coins_info.save()
                            device_coins = F('coins') - (count *1 - emailcoinsdeducted)
                            device_coins.save()
                        ticket_available = LotteryTicketAvailable.objects.filter(ticket_id = self.ticket.id)[0]
                        ticket_available.pending = 0
                        ticket_available.save()
                else:
                    if device_coins.coins + coins_info.coins >= count *2:
                        if coins_info.coins >= count * 2:    
                            coins_info.coins = coins_info.coins - count *2
                            coins_info.save()
                            ticket_available = LotteryTicketAvailable.objects.filter(ticket_id = self.ticket.id)[0]
                            ticket_available.pending = 0
                            ticket_available.save()  
                        else:
                            emailcoinsdeducted = coins_info.coins
                            coins_info.coins = 0.0
                            coins_info.save()
                            device_coins.coins = device_coins.coins - (count *2 - emailcoinsdeducted)
                            device_coins.save()
                            ticket_available = LotteryTicketAvailable.objects.filter(ticket_id = self.ticket.id)[0]
                            ticket_available.pending = 0
                            ticket_available.save()            
            else:
                pass
            #try:
                #if self.ticket.ticket_submissions.all()[0].available and self.ticket.ticket_submissions.all()[0].pending:
                 #   _result["gameState"] = 4
                #el
            print "ticket_id",self.ticket.id
            print "checked",self.ticket.all_checked
            print "draw result",self.ticket.draw.result
            print "pending",self.ticket.ticket_submissions.all()[0].pending
            if self.ticket.ticket_submissions.all()[0].pending and self.ticket.ticket_submissions.all()[0].available:
                _result["gameState"] = 4
            elif not self.ticket.all_checked and not self.ticket.draw.result and not self.ticket.ticket_submissions.all()[0].pending: #and coins complete
                _result["gameState"] = 0
            elif not self.ticket.all_checked and self.ticket.draw.result and not self.ticket.ticket_submissions.all()[0].pending: # coins complete
                _result["gameState"] = 1
            elif self.ticket.all_checked and self.ticket.draw.result and not self.ticket.ticket_submissions.all()[0].pending and self.ticket.ticket_submissions.all()[0].available:
                _result["gameState"] = 2
            #print "result of gamestate",_result["gameState"]
            #except:
            #    pass
        return _result
        
class TicketRepresentationShortList1(TicketRepresentation):
    def __call__(self, *args, **kwargs):
        import datetime
        from yoolotto.lottery.enumerations import EnumerationManager
        from yoolotto.lottery.models import LotteryGameComponent
        ticket = self.ticket
        draw = self.ticket.draw
        plays = self.ticket.plays.exclude(play=None)
        handler = draw.component.parent.handler
        lg_obj = LotteryGameComponent.objects.filter(parent=draw.component.parent.pk)[0]
        state = self.ticket.division.remote_id   
        _result = {
            "game": {
                "id": draw.component.parent.pk,
                "name": draw.component.parent.name,
                "gameType": EnumerationManager.game_reverse(draw.component.parent.pk),
                "state":state,
            },
            "current_date":datetime.date.today().strftime("%Y-%m-%d"),
            #"plays": self.ticket.plays.count(),
            "plays": [],
            "draw": draw.representation(ticket=self.ticket),
            "ticket_id": self.ticket.pk,
            "winnings": str(self.ticket.winnings) if self.ticket.winnings is not None else None,
            "coins": self.ticket.coin_representation(),
            "checked": self.ticket.all_checked,
            "representation": self.__class__.__name__
        }
        pending = False
        try:
            if not self.ticket.ticket_submissions.all()[0].available and not self.ticket.ticket_submissions.all()[0].rejected:
                pending = True
        except:
            pending = True

        if not self.ticket.all_checked and not self.ticket.draw.result: #and not self.ticket.ticket_submissions.all()[0].pending :
            _result["gameState"] = 0
        elif not self.ticket.all_checked and self.ticket.draw.result:# and not self.ticket.ticket_submissions.all()[0].pending :
            _result["gameState"] = 1
        else:
            _result["gameState"] = 2
        
        _result["game"].update(handler.get_game_meta(draw.component))
        for play in plays:
            ticket_image = self.ticket.ticket_submissions.all()
            if ticket_image :
                image = str(ticket_image[0].image_first)
            else:
                image = None
            try:
                play_data = json.loads(play.play)
                raw = handler.postprocess_play(play_data)
            except:
                play_data = json.loads(json.dumps(play.play))
                raw = handler.postprocess_play(play_data)
            try:
                raw_data = json.loads(raw)
            except:
                raw_data = eval(str(raw))
            _play = {
                "play_id": play.pk,
                "winnings": str(play.winnings) if play.winnings is not None else None,
                "play": raw_data,
                "checked":play.submission.checked,
                "submission": play.submission_old,
        "image": image,
            }
              
            _play["baseWinnings"] = str(play.winnings_base) if play.winnings_base else _play["winnings"]
            _play["sumWinnings"] = str(play.winnings_sum) if play.winnings_sum else None
            
            _result["plays"].append(_play)
        return _result

    
