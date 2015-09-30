from django.conf.urls import patterns, include, url
from yoolotto.promo.views import PromoLanding
from yoolotto.communication.views import Notification
from yoolotto.util.views import *
from yoolotto.openx_adunits.views import in_app_fuel, SCACoins,YooGames
# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url('^ad', include('yoolotto.ad.urls')),
    url('^coupon/', include('yoolotto.coupon.urls')),
    url('^second_chance/', include('yoolotto.second_chance.urls')),
    url('^lottery/', include('yoolotto.lottery.urls')),
    url('^user/', include('yoolotto.user.urls')),
    url('^games', include('yoolotto.games.urls')),
    url('^coingames', include('yoolotto.games.urls')),
    url('^promo$', PromoLanding.as_view()),
    url('^promo/(?P<mode>.*)', PromoLanding.as_view()),
    
    url('^private/communication/notification', Notification.as_view()),
    url('^_util/version', BuildVersion.as_view()),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^analytics/', 'yoolotto.analytics.views.generate_report', name="analytics"),
    url(r'^notification/', 'yoolotto.analytics.views.notifications', name="notifications"),
    url(r'^winnings/', 'yoolotto.analytics.views.winnings', name="winnings"),
    url('^openx/', include('yoolotto.openx_adunits.urls')),
    url('^other/in_app_fuel',in_app_fuel.as_view()),
    url(r'^dte_images/', 'yoolotto.yoolotto_debug.views.data_entry_images'),
    url(r'^bulk_notification/', 'yoolotto.yoolotto_debug.views.send_bulk_notification'),
    url(r'^debug/', 'yoolotto.yoolotto_debug.views.debug_home'),
    url('^sca_coins',SCACoins.as_view()),
    url(r'^yoo_games', YooGames.as_view()),

    
    
)

