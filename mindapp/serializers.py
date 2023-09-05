from rest_framework import serializers
from .models import *
from datetime import datetime
from rest_framework import status
from datetime import datetime, timedelta
from collections import Counter
from django.http import JsonResponse
from django.core.serializers.json import DjangoJSONEncoder 
import json
from django.http import HttpResponse
from datetime import date
from dateutil.relativedelta import relativedelta
   
def calculate_next_allowed_date(missed_date, days):

    current_date = missed_date

    while days > 0:
        current_date += timedelta(days=1)
        current_date += relativedelta(days=0)  # Use relativedelta to handle month changes
        days -= 1
    return current_date   


class StreakSerializer(serializers.ModelSerializer):
    current_week = serializers.SerializerMethodField()
    current_day = serializers.SerializerMethodField()
    entries_this_week = serializers.SerializerMethodField()
    total_coins = serializers.SerializerMethodField()
    highest_streak = serializers.SerializerMethodField()
    can_use_streak_saver =serializers.SerializerMethodField()
    streak_saver_timeline =serializers.SerializerMethodField()
    
    class Meta:
        model = Streaks
        fields = ['entries_this_week','streak_saver_timeline','can_use_streak_saver','current_streak','streak_saver_used','total_coins','highest_streak', 'week_start_date', 'entry_type', 'entry_length','current_week','current_day']
    
    def get_current_week(self, request):
        user = request.user
        try:
            streak = Streaks.objects.get(user=user)
            current_date = timezone.now().date()
            days_difference = (current_date - streak.week_start_date).days
            current_week = (days_difference // 7) + 1
            return current_week
        except Streaks.DoesNotExist:
            return None
        
    def get_streak_saver_timeline(self,request):
        user = request.user
        streak = Streaks.objects.get(user=user)  # Assuming you have a Streaks model for the user
        date_dict = streak_count_daywise(streak)
        reference_date = streak.week_start_date
        missed_date=None

        if streak.streak_saver_used_datetime:
            last_usage_date = max(streak.streak_saver_used_datetime)
            next_allowed_date = last_usage_date + timedelta(days=6)
            
        else:
            for day, status in date_dict.items():
                if status == "False" and missed_date is None:
                    day_number = int(day)
                    missed_date = reference_date.replace(day=day_number)
                    if missed_date < streak.week_start_date:
                        missed_date = missed_date.replace(month=missed_date.month + 1)
                    break  # Stop searching after finding the first "False" status

            if missed_date:
                next_allowed_date = calculate_next_allowed_date(missed_date, 6)
            else:
                next_allowed_date = None    
                    
        return next_allowed_date
                
    def get_can_use_streak_saver(self,request): 
        user = request.user
        streak = Streaks.objects.get(user=user)
        current_date = timezone.now().date()
        week_start_date = current_date - timedelta(days=current_date.weekday())
        streak_saver_dates = streak.streak_saver_used_datetime
        
        if not streak_saver_dates:
            return True
    
        last_usage_date = max(streak_saver_dates)
        days_since_last_usage = (current_date - last_usage_date).days
        return days_since_last_usage > 7
            
    def get_entries_this_week(self, request):
        user=request.user.id
        streak = Streaks.objects.get(user=user)
        data = streak_count_daywise(streak)
        return data

    def get_current_day(self, instance):
        data = datetime.today().date()
        return data

    
    def get_total_coins(self, request):
        user = request.user
        try:
            user_coins = Coins.objects.get(user=user)
            total_coins = user_coins.coins
        except Coins.DoesNotExist:
            total_coins = 0
        return total_coins
    
    def get_highest_streak(self,request):
        user=request.user.id
        streak = Streaks.objects.get(user=user)
        if streak.current_streak > streak.highest_streak:
            streak.highest_streak = streak.current_streak
        streak.save()    
        return streak.highest_streak    

class BadgeSerializer(serializers.ModelSerializer):   
    class Meta:
        model = Badges
        fields = ['label','logo','streak_length']     

class UserBadgeSerializer(serializers.ModelSerializer):
    badge_label = serializers.ReadOnlyField(source='badge.label')
    badge_logo = serializers.ImageField(source='badge.logo', read_only=True)
    badge_streak_length = serializers.ReadOnlyField(source='badge.streak_length')
    

    class Meta:
        model = UserBadge
        fields = ['badge_label', 'badge_logo','badge_streak_length', 'created_at']
            

class StreaksaverSerializer(serializers.ModelSerializer):   
    class Meta:
        model = Coins
        fields = '__all__'

class CoindetailSerializer(serializers.ModelSerializer):
    coinvalue_entryrange_mapping = serializers.SerializerMethodField()
    class Meta:
        model = Coindetails
        fields = '__all__'

# # Absolutly Working Fine for S4
# def streak_count_daywise(request):
#     user = request.user
#     streak = Streaks.objects.get(user=user)
#     st_date = streak.week_start_date
#     today = timezone.now().date()  # Get today's date
#     journal_counter_datewise = Counter(Journal.objects.filter(
#         user=user, created_at__gte=st_date
#     ).values_list("created_at__day", flat=True))

#     date_dict = {}

#     for i in range(6, -1, -1):  # Iterate from 6 to 0 (last 7 days including today)
#         day = str((today - timedelta(days=i)).day)  # Calculate the day using the correct logic

#         if st_date <= today - timedelta(days=i):  # Check if within streak period
#             if today.day == int(day):
#                 if journal_counter_datewise[int(day)] > 0:
#                     date_dict[day] = "True"
#                 elif today < timezone.now().replace(hour=0, minute=0, second=0, microsecond=0).date():
#                     date_dict[day] = "False"
#                 else:
#                     date_dict[day] = "null"  
#             else:  # For days before the current day
#                 if journal_counter_datewise[int(day)] > 0:
#                     date_dict[day] = "True"
#                 else:            
#                     date_dict[day] = "False"
#         else:
#             date_dict[day] = "null"

#     return date_dict
# #Absolutely working


# # Absolutly Working Fine for S5
# def streak_count_daywise(request):
#     user = request.user
#     streak = Streaks.objects.get(user=user)
#     st_date = streak.week_start_date
#     today = timezone.now().date()
#     journal_counter_datewise = Counter(Journal.objects.filter(
#         user=user, created_at__gte=st_date
#     ).values_list("created_at__day", flat=True))

#     date_dict = {}

#     for i in range(6, -1, -1):  # Iterate from 6 to 0 (last 7 days including today)
#         day = str((today - timedelta(days=i)).day)

#         if st_date <= today - timedelta(days=i):  # Check if within streak period
#             if today.day == int(day):
#                 if journal_counter_datewise[int(day)] > 0:
#                     date_dict[day] = "True"
#                 elif today < timezone.now().replace(hour=0, minute=0, second=0, microsecond=0).date():
#                     date_dict[day] = "False"
#                 else:
#                     date_dict[day] = "null"
#             else:  # For days before the current day
#                 if journal_counter_datewise[int(day)] > 0:
#                     date_dict[day] = "True"
#                 else:
#                     # Check if Streak saver was used on the same date
#                     if today - timedelta(days=i) in streak.streak_saver_used_datetime:
#                         date_dict[day] = "SS"
#                     else:
#                         date_dict[day] = "False"
#         else:
#             date_dict[day] = "null"

#     return date_dict


# # Absolutly Working Fine for S5

# #Working for S6
# def streak_count_daywise(request):
#     user = request.user
#     streak = Streaks.objects.get(user=user)
#     st_date = streak.week_start_date
#     today = timezone.now().date()
#     journal_counter_datewise = Counter(Journal.objects.filter(
#         user=user, created_at__gte=st_date
#     ).values_list("created_at__day", flat=True))

#     date_dict = {}
#     encountered_false = False  # Initialize a flag to track if a "False" entry is encountered

#     for i in range(6, -1, -1):  # Iterate from 6 to 0 (last 7 days including today)
#         day = str((today - timedelta(days=i)).day)

#         if st_date <= today - timedelta(days=i):  # Check if within streak period
#             if today.day == int(day):
#                 if journal_counter_datewise[int(day)] > 0:
#                     if encountered_false:
#                         date_dict[day] = "Frozen_True"  # Mark as "Frozen_True" if a "False" entry was encountered
#                     else:
#                         date_dict[day] = "True"
#                 elif today < timezone.now().replace(hour=0, minute=0, second=0, microsecond=0).date():
#                     date_dict[day] = "False"
#                     encountered_false = True  # Set the flag to True when a "False" entry is encountered
#                 else:
#                     date_dict[day] = "null"
#             else:  # For days before the current day
#                 if journal_counter_datewise[int(day)] > 0:
#                     if encountered_false:
#                         date_dict[day] = "Frozen_True"  # Mark as "Frozen_True" if a "False" entry was encountered
#                     else:
#                         date_dict[day] = "True"
#                 else:
#                     # Check if Streak saver was used on the same date
#                     if today - timedelta(days=i) in streak.streak_saver_used_datetime:
#                         date_dict[day] = "SS"
#                     else:
#                         date_dict[day] = "False"
#                         encountered_false = True  # Set the flag to True when a "False" entry is encountered
#         else:
#             date_dict[day] = "null"

#     return date_dict

#Working for S6

#in the form of function working to convert frozen entries into true after using streak saver


from datetime import timedelta

def get_journal_entries_datewise(user, start_date, end_date):
    return set(
        Journal.objects.filter(user=user, created_at__range=(start_date, end_date))
        .values_list("created_at__day", flat=True)
    )

def is_today(date):
    return date == timezone.now().date()

def is_future(date):
    return date < timezone.now().replace(hour=0, minute=0, second=0, microsecond=0).date()

def is_streak_saver_used(streak, date):
    return date in streak.streak_saver_used_datetime

def process_frozen_true(date_dict):
    processed_dict = date_dict.copy()
    encountered_false = False

    for day, status in date_dict.items():
        if status == "Frozen_True":
            encountered_false = False  # Reset the flag when "Frozen_True" is encountered
        elif status == "False":
            encountered_false = True
        elif status == "True" and encountered_false:
            processed_dict[day] = "Frozen_True"

    return processed_dict

def process_false_after_frozen_true(date_dict):
    processed_dict = date_dict.copy()
    encountered_frozen_true = False

    for day, status in date_dict.items():
        if status == "Frozen_True":
            encountered_frozen_true = True
        elif status == "False" and encountered_frozen_true:
            processed_dict = process_black_falses(processed_dict)
            break  # Stop processing when a "False" after "Frozen_True" is encountered
    
    return processed_dict

def process_black_falses(date_dict):
    processed_dict = date_dict.copy()

    for day, status in date_dict.items():
        if status == "Frozen_True":
            break  # Stop processing when a "Frozen_True" is encountered
        elif status == "False":
            processed_dict[day] = "BlackFalse"
    return processed_dict

def process_black_true(date_dict):
    processed_dict = date_dict.copy()
    black_false_encountered = False

    for day in reversed(processed_dict):
        if processed_dict[day] == "BlackFalse":
            black_false_encountered = True
        elif processed_dict[day] == "True" and black_false_encountered:
            processed_dict[day] = "BlackTrue"
    
    return processed_dict

def convert_frozen_true_to_true(date_dict):
    encountered_black_false = False
    S9 = False

    for day, status in date_dict.items():
        if S9 == "False":
            if status == "Frozen_True":
                date_dict[day] = "True"
                S9 = True
        if S9 == "True" and status == "Frozen_True":
            date_dict[day] = "True"  
        if status == "False":
            break
        if status == "BlackFalse":
            encountered_black_false = True
        elif status == "Frozen_True" and encountered_black_false:
            date_dict[day] = "True"
    
    return date_dict


def process_ss_after_false(date_dict):
    processed_dict = date_dict.copy()
    encountered_false = False
    ss_encountered = False

    for day, status in reversed(date_dict.items()):
        if status == "False":
            encountered_false = True
        elif status == "SS" and encountered_false:
            processed_dict[day] = "BlackSS"
            ss_encountered = True
        elif status == "True" and encountered_false and ss_encountered:
            processed_dict[day] = "BlackTrue"
        
    return processed_dict


def streak_count_daywise(request):
    user = request.user
    streak = Streaks.objects.get(user=user)
    st_date = streak.week_start_date
    today = timezone.now().date()
    # today = date(2023,9,6)
    
    journal_counter_datewise = Counter(Journal.objects.filter(
        user=user, created_at__gte=st_date
    ).values_list("created_at__day", flat=True))

    date_dict = {}
    encountered_false = False  # Initialize a flag to track if a "False" entry is encountered
    ss_used = False  # Initialize a flag to track if "SS" replaces "False"
    
    for i in range(6, -1, -1):  # Iterate from 6 to 0 (last 7 days including today)
        day = str((today - timedelta(days=i)).day)

        if st_date <= today - timedelta(days=i):  # Check if within streak period
            if is_today(today - timedelta(days=i)):
                if journal_counter_datewise[int(day)] > 0:
                    if ss_used:
                        date_dict[day] = "True"  # Convert "Frozen_True" back to "True" if "SS" used
                    else:
                        date_dict[day] = "Frozen_True" if encountered_false else "True"
                elif is_future(today):
                    if ss_used:
                        date_dict[day] = "True"  # Convert "Frozen_True" back to "True" if "SS" used
                    else:
                        date_dict[day] = "False"
                        encountered_false = True  # Set the flag to True when a "False" entry is encountered
                else:
                    date_dict[day] = "null"
            else:  # For days before the current day
                if journal_counter_datewise[int(day)] > 0:
                    if ss_used:
                        date_dict[day] = "True"  # Convert "Frozen_True" back to "True" if "SS" used
                    else:
                        date_dict[day] = "Frozen_True" if encountered_false else "True"
                else:
                    # Check if Streak saver was used on the same date
                    if is_streak_saver_used(streak, today - timedelta(days=i)):
                        date_dict[day] = "SS"
                        ss_used = True  # Set the flag to True when "SS" replaces "False"
                    else:
                        date_dict[day] = "False"
                        encountered_false = True  # Set the flag to True when a "False" entry is encountered
        else:
            date_dict[day] = "null"
    date_dict = process_frozen_true(date_dict)        
    date_dict = process_false_after_frozen_true(date_dict)
    date_dict = process_black_true(date_dict)
    date_dict = convert_frozen_true_to_true(date_dict)
    date_dict = process_ss_after_false(date_dict)
    #Add current streak count 
    return date_dict





