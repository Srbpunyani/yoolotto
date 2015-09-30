from django.conf.urls import patterns, include, url
from yoolotto.lottery.feed.manual_push import ManualNotification, FindTickets,\
    FindUser, FindLastUser
from yoolotto.lottery.views import *
from yoolotto.lottery.ticket.views import *


urlpatterns = patterns('',
    url('^game/(?P<id>\d+)$', Game.as_view()),
    url('^game/draw/(?P<_id>\d+)/check$', GameCheck.as_view()),
    url('^game$', Game.as_view()),
    url('^play$', Play_Game.as_view()),
    url('^submit$', SubmitAgain.as_view()),
    url('^edit$', EditData.as_view()),
    url('^ticket/(?P<_id>\d+)/check', TicketCheck.as_view()),
    url('^ticket/(?P<_id>\d+)/share', TicketShare.as_view()),
    url('^ticket/(?P<_id>\d+)/delete', TicketDelete.as_view()),
    url('^ticket', Ticket.as_view()),
    url('^manual_notification/last_user',FindLastUser.as_view()),
    url('^manual_notification/find_tickets',FindTickets.as_view()),
    url('^manual_notification/find_user',FindUser.as_view()),
    url('^manual_notification',ManualNotification.as_view()),
    url('^winner',Winner.as_view()),
    
    
#    url('^login$', UserLogin.as_view()),
)
