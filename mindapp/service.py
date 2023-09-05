from .models import *
# from journal.models import Journal
from django.db.models import Count
from datetime import datetime, timedelta

def calculate_coins(entry_type, entry_length):
    if entry_type == 'text':
        if 10 <= entry_length <= 50:
            return 5
        elif 51 <= entry_length <= 200:
            return 10
        elif entry_length > 200:
            return 15
    elif entry_type == 'audio':
        if 30 <= entry_length <= 60:
            return 5
        elif 61 <= entry_length <= 180:
            return 10
        elif entry_length > 180:
            return 15
    return 0

def update_badges(user, streak):
    badges_earned = Badge.objects.filter(streak_length__lte=streak.current_streak)
    for badge in badges_earned:
        UserBadge.objects.get_or_create(user=user, badge=badge)

def save_user_coins(user, coins):
    coins_obj, created = Coins.objects.get_or_create(user=user)
    coins_obj.coins = coins
    coins_obj.save()

def get_user_streak(user):
    streak, created = Streak.objects.get_or_create(user=user)
    return streak

# def reset_streak(streak):
#     streak.current_streak += 1
#     streak.save()

def calender_data(user, start_date, end_date):
    queryset = Journal.objects.filter(
        user=user,
        created_at__range=[start_date, end_date]
    ).values("created_at__date").annotate(entry_count=Count("created_at__date"))
    data = []
    for entry in queryset:
        formatted_date = entry['created_at__date'].strftime('%Y-%m-%d')
        entry_count = entry['entry_count']
        data.append({
            "Streak_date": formatted_date,
            "No._of _entries": entry_count
        })
    return data
    

