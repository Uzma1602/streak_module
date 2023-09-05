from django.urls import path
from django.conf.urls.static import static
from .views import *
from rest_framework.routers import SimpleRouter

router = SimpleRouter()
router.register('streaks1', StreakViewSet)
router.register('streaksaver', StreaksaverViewSet)
router.register('coindetail',CoindetailViewSet)

urlpatterns = [
    path('calender/', CalenderViewSet.as_view(), name="login POST"),
    path('coins/', CoinViewSet.as_view(), name="login POST"),
    path('badges/', BadgesViewSet.as_view(), name="login POST"),
]
urlpatterns += router.urls

