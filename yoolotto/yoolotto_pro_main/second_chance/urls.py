
from django.conf.urls import patterns, include, url

from yoolotto.second_chance.views import *

urlpatterns = patterns('',
    url('^wallet/(?P<filter>.+)$', AdCoupons.as_view()),    
    url('^vendor', Advertisors.as_view()),
    url('^faq', FrequentQuestions.as_view()),
    url('^redeem_ad', AdRedeem.as_view()),
    url('^timer_ad', TimerAd.as_view()),
    url('^invitation', InviteFriends.as_view()),
    url('^android_game', AndroidGame.as_view()),
    url('^android_numbers', AndroidNumbers.as_view()),
    url('^add_coins', AddCoins.as_view()),
    url('^ad_colony',AdColony.as_view()),
    url('^screen_ads', ScreenAds.as_view()),
    url('^social_message',SocialMessage.as_view()),
    url('^sca',SCA_url.as_view()),
    url('^in_app_fuel_callback/(?P<userID>.+)/(?P<currency>.+)/(?P<game_id>.+)/(?P<sig>.+)$',InAppFuelCallback.as_view()),
)
