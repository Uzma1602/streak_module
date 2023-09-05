from django.shortcuts import render
from .serializers import *
from rest_framework.viewsets import ModelViewSet
from .models import *
from rest_framework import status
from rest_framework.response import Response
from .service import *
# from response import CustomJsonRender
from rest_framework.permissions import IsAuthenticated
from datetime import datetime, timedelta
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.decorators import api_view
from django.http import JsonResponse
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.db.models import Prefetch
from datetime import datetime, timedelta
from django.db.models import Q

def save_user_coins(user, coins):
    coins_obj, created = Coins.objects.get_or_create(user=user)
    coins_obj.coins = coins
    coins_obj.save()

def get_user_coins(user):
    coins, created = Coins.objects.get_or_create(user=user)
    return coins.coins

def get_user_streak(user):
    streaks = Streaks.objects.filter(user=user)
    if streaks.exists():
        latest_streak = streaks.latest('updated_at')
        return latest_streak
    else:
        return None

# This class contains the function to get the streak 

class StreakViewSet(ModelViewSet):
    # permission_classes = [IsAuthenticated]
    # renderer_classes = (CustomJsonRender,)
    queryset = Streaks.objects.all()
    serializer_class = StreakSerializer

    def get_queryset(self):
        # user = self.request.user.id
        user=1
        print(user)
        streaks = Streaks.objects.filter(user=user)
        return streaks
    
    def get(self, request, *args, **kwargs):
        streaks = self.get_queryset()
        serializer = StreakSerializer(streaks, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
      
# This class contains the badges function

class BadgesViewSet(APIView):
    def get(self, request):
        # user = request.user
        user=1
        all_badges = Badges.objects.all()
        user_badges = UserBadge.objects.filter(user=user)
        
        badge_dict = {}
        for badge in all_badges:
            badge_data = BadgeSerializer(badge).data
            badge_id = badge.id
            badge_data['earned'] = any(ub.badge.id == badge_id for ub in user_badges)
            if badge_data['earned']:
                user_badge = user_badges.get(badge=badge)
                badge_data['earned_at'] = user_badge.created_at
            badge_dict[badge_id] = badge_data
        badge_list = list(badge_dict.values())
        
        return Response({
            "status": 200,
            "data": badge_list
        }, status=status.HTTP_200_OK)


# This class contains the function for streaksaver

class StreaksaverViewSet(ModelViewSet):
    queryset = Streaks.objects.all()
    serializer_class = StreaksaverSerializer
    # permission_classes = [IsAuthenticated]

    def create(self, request,*args, **kwargs):
        user=1
        # user = self.request.user.id
        coins_needed = 50  # Coins needed for streak saver
        data=request.data
        data["user"]=str(user)
        user_coins = get_user_coins(user)
        if user_coins >= coins_needed:
            streak = get_user_streak(user)
            if streak.current_streak > 0:
                # Use the streak saver
                user_coins -= coins_needed
                save_user_coins(user, user_coins)  # Save updated coins
                # reset_streak(streak)  # Reset streak
                # Save the date when the streak saver was used
                streak.streak_saver_used = True
                previous_date = datetime.now().date() - timedelta(days=1)  # Subtract one day from the current date
                streak.streak_saver_used_datetime.append(previous_date)
                streak.save()
                return Response({"success": status.HTTP_200_OK,
                                 "message": "Streak saver used successfully."},
                                 status=status.HTTP_200_OK)
            else:
                return Response({"success": status.HTTP_200_OK,
                                 "message": "No streak progress to save."},
                                 status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"success": status.HTTP_200_OK,
                             "message": "Insufficient coins."},
                             status=status.HTTP_400_BAD_REQUEST)


# This class contains the function for the calender part


class CalenderViewSet(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def sign_up_date(self, user):
        return user.date_joined.date()
    
    def get(self, request):
        user = request.user
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        week_number = int(request.query_params.get('week_number', 0))        
        if week_number:
            date = user.streak.week_start_date
            current_week = user.streak.current_streak
            start_date = date - timedelta(days=(current_week - week_number) * 7)
            end_date = start_date + timedelta(days=6)
        data = calender_data(user, start_date, end_date)

        # Filter badges based on the date range

        badge_earned = UserBadge.objects.filter(
            user=user,
            created_at__range=[start_date, end_date]  
        )
        badge_serializer = UserBadgeSerializer(badge_earned, many=True)
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        streak_instances = Streaks.objects.filter(user=user)
        streak_saver_used_dates = []
        for streak_instance in streak_instances:
            for date in streak_instance.streak_saver_used_datetime:
                if start_date <= date <= end_date:
                    streak_saver_used_dates.append(date)
        streak_saver_used_dates_serialized = [
            date.strftime('%Y-%m-%d') for date in streak_saver_used_dates
        ]
        sign_up = self.sign_up_date(user)
        return Response({
            "success": status.HTTP_200_OK,
            "data": {
                "sign_up_date": sign_up,
                "entries_this_month": data,
                "badge_earned": badge_serializer.data,
                "streak_saver_used_dates": streak_saver_used_dates_serialized
            }
        })

# This class contains the function to calculate total coins

class CoinViewSet(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]   
    def get(self, request):
        user = request.user
        try:
            user_coins = Coins.objects.get(user=user)
            total_coins = user_coins.coins
            return Response({"total_coins": total_coins},status=status.HTTP_200_OK)
        except Coins.DoesNotExist:
            return Response({"total_coins": 0},status=status.HTTP_200_OK)
        

# This class contains the coindetails function

class CoindetailViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated]
    # renderer_classes = (CustomJsonRender,) 
    queryset = Coindetails.objects.all()
    serializer_class = CoindetailSerializer
    queryset1=Coins.objects.all()

    def get_total_coins(self, user):
        try:
            user_coins = Coins.objects.get(user=user)
            total_coins = user_coins.coins
        except Coins.DoesNotExist:
            total_coins = 0
        return total_coins

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)

        total_coins = self.get_total_coins(request.user)
        response_data = {
            "total_coins": total_coins,
            "coindetails": serializer.data
        }
        return Response(response_data, status=status.HTTP_200_OK)
   
   
   





 



    
   
    




  





    

