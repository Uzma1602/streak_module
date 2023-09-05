# Register your models here.
from django.contrib import admin
from .models import *
admin.site.register(User)
admin.site.register(Journal)
admin.site.register(Streaks)
admin.site.register(Badges)
admin.site.register(UserBadge)
admin.site.register(Coins)
admin.site.register(Coindetails)