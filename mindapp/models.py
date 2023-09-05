from django.db import models
import uuid
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from django.dispatch import receiver
from django.db.models.signals import pre_delete
from django.core.exceptions import PermissionDenied
from django.contrib.auth.hashers import make_password
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils import timezone
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.db import models
from django.utils import timezone
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from .service import calculate_coins 
from rest_framework.response import Response
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin , Group , Permission
import uuid
from .service import *
from django.db.models import Q
from collections import defaultdict
from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.utils import timezone
from django.contrib.postgres.fields import ArrayField
from mutagen.mp3 import MP3
from django.core.files.base import ContentFile


class AccountManager(BaseUserManager):
    use_in_migrations = True

    def create_superuser(self, phone, password, **kwargs):
        user = self.model(phone=phone, is_staff=True, is_superuser=True, is_admin=True, **kwargs)
        user.password = make_password(password)
        user.save()
        return user


def nameFile(instance, filename):
    return '/'.join(['images/profile', str(instance.username), filename])


class User(AbstractBaseUser, PermissionsMixin):
    # id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    username = models.CharField(max_length=50, unique=True)
    full_name = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(unique=True, blank=True, null=True)
    phone = models.CharField(max_length=50, unique=True,  blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=10, choices=(('Male', 'Male'), ('Female', 'Female'),('Others','Others')), blank=True)
    picture = models.ImageField(upload_to=nameFile, null=True, blank=True)
    zodiac_sign = models.CharField(max_length=50, blank=True, null=True)
    fcm_token = ArrayField(models.CharField(max_length=1000), null=True, blank=True,default=list)
    bio = models.TextField(blank=True, null=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    user_timezone = models.CharField(max_length=50, null=True, blank=True)
    user_timezone_name = models.CharField(max_length=150, null=True, blank=True)
    last_login = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    groups = models.ManyToManyField(
        Group,
        verbose_name=_('groups'),
        blank=True,
        help_text=_(
            'The groups this user belongs to. A user will get all permissions '
            'granted to each of their groups.'
        ),
        related_name='mindapp_users_groups'  
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name=_('user permissions'),
        blank=True,
        help_text=_('Specific permissions for this user.'),
        related_name='mindapp_users_permissions'  
    )

    objects = AccountManager()

    class Meta:
        db_table = 'User'
        indexes = [
            models.Index(fields=[
                'username'   
            ])
        ]

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['phone']

    def _str_(self):
        return self.username


# prevent superuser to delete itself
@receiver(pre_delete, sender=User)
def delete_user(sender, instance, **kwargs):
    if instance.is_superuser:
        raise PermissionDenied
    
def name_file(instance, filename):
    return '/'.join(['media', str(instance.id), filename])

class Journal(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    # id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    title = models.CharField(max_length=250, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    transcript = models.TextField(null=True, blank=True)
    audio = models.FileField(upload_to=name_file, null=True, blank=True)
    image = models.ImageField(upload_to=name_file, null=True, blank=True)
    emotions = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    text_to_speech = models.BooleanField(default=True)
    entry_type = models.CharField(max_length=10, choices=[('audio', 'Audio'), ('text', 'Text')],null=True)
    entry_length = models.FloatField(null=True)

    def save(self, *args, **kwargs):
        if not self.entry_type:  
            if self.description:
                self.entry_type = 'text'
                # self.entry_length = len(self.description)
                self.entry_length= len(self.description.split())

            elif self.audio:
                self.entry_type = 'audio'
                self.entry_length = self.calculate_audio_length()
        super().save(*args, **kwargs)

    def calculate_audio_length(self):
        try:
            audio_content = self.audio.open().read()  # Read the content of the audio file
        except Exception as e:
            # Handle the exception, e.g., log or raise a more specific error
            return None

        audio_content_file = ContentFile(audio_content)  # Create a ContentFile
        audio_length_seconds = self.get_audio_length(audio_content_file)
        return audio_length_seconds

    def get_audio_length(self, audio_content_file):
        audio = MP3(audio_content_file)
        audio_length_seconds = audio.info.length
        return int(audio_length_seconds)
  
    class Meta:
        db_table = 'Journal'

    def __str__(self):
        return f"{self.user} - {self.created_at}" 
        # return {str(self.user)- str(self.created_at)}


def name_file(instance, filename):
    return '/'.join(['badge', str(instance.label), filename])

class Streaks(models.Model): 
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    current_streak = models.IntegerField(default=0 , null=True)  # Streak weeks completed before start of this week
    highest_streak = models.IntegerField(default=0, null=True, blank=True)  # Highest streak achieved
    week_start_date = models.DateField(default=timezone.now)  # Start date of current streak week
    updated_at = models.DateTimeField(auto_now=True)
    last_entry_date = models.DateField(null=True,blank=True)
    streak_saver_used = models.BooleanField(default=False)
    streak_saver_used_datetime= ArrayField(models.DateField(), default=list,null=True,blank=True)
    entry_type = models.CharField(max_length=10, choices=(('text', 'Text'), ('audio', 'Audio')),null=True,blank=True)
    entry_length = models.IntegerField(null=True)
    journals = models.ManyToManyField(Journal, blank=True)

    class Meta:
        db_table = 'Streaks'

    def __str__(self):
        return self.user.username


@receiver(post_save, sender=Journal)
def create_streak(sender, instance, created, **kwargs):
    user=instance.user
    entry_type = instance.entry_type
    entry_length = instance.entry_length
    flag = user_exist(user)
    if flag==True:
        streak=update_streak(user,entry_length,entry_type)       
    else:
        streak,created = Streaks.objects.get_or_create(user=instance.user,entry_type=entry_type,entry_length=entry_length)
    coins=calculate_coins(entry_type, entry_length)   
    if coins > 0:
        existing_coin = Coins.objects.filter(user=user).first()
        if existing_coin:
            existing_coin.coins += coins
            existing_coin.save()
        else:
            coin = Coins(user=user, coins=coins)
            coin.save()
    update_last_entry_date(streak)
    return streak


class Badges(models.Model):
    label = models.CharField(max_length=100, null=True, blank=True) 
    logo = models.ImageField(upload_to=name_file, null=True, blank=True)
    streak_length = models.IntegerField(unique=True)  # Number of weeks to achieve badge
    users = models.ManyToManyField(User, through="UserBadge", related_name="badges")

    class Meta:
        db_table = 'Badges'
        ordering = ["streak_length"]

    def __str__(self):
        return self.label  


class UserBadge(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    badge = models.ForeignKey(Badges, on_delete=models.CASCADE)
    created_at = models.DateField(auto_now_add=True)

    class Meta:
        db_table = 'UserBadges'

    def __str__(self):
        return f"{self.user.username} - {self.badge}"   


@receiver(post_save, sender=Journal)
def create_badges(sender, instance, created, **kwargs):
    streakuser = instance.user
    current_streaks = Streaks.objects.filter(user=streakuser).values_list('current_streak', flat=True)
    badges_earned = Badges.objects.filter(streak_length__in=current_streaks).order_by('-streak_length')
    if len(badges_earned) == 0:
        return Response({"Message": "No Badge for this entry"})
    else:
        UserBadge.objects.get_or_create(user=streakuser,badge=badges_earned[0])
       

class Coins(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE) 
    coins = models.IntegerField(default=0)

    class Meta:
        db_table = 'Coins'
    
    def __str__(self):
        return f"Coins for {self.user.username}"
    

@receiver(post_save, sender=User)
def create_coins(sender, instance, created, **kwargs):
    if created and not Coins.objects.filter(user=instance).exists():
        Coins.objects.create(user=instance)


class Coindetails(models.Model):
    label=models.CharField(max_length=100, null=True, blank=True) 
    description=models.CharField(max_length=500, null=True, blank=True)
    Image = models.ImageField(upload_to=name_file, null=True, blank=True)
    coinvalue=models.IntegerField(null=True)
    entryrange=models.CharField(max_length=100,null=True)
    coinvalue1=models.IntegerField(null=True,blank=True)
    entryrange1=models.CharField(max_length=100,null=True,blank=True)
    coinvalue2=models.IntegerField(null=True,blank=True)
    entryrange2=models.CharField(max_length=100,null=True,blank=True)

    class Meta:
        db_table = 'Coindetails'

    def __str__(self):
        return self.label
    
# Other Function
def user_exist(user):
    user1=Streaks.objects.filter(Q(user=user))
    if len(user1) == 0 :
        return False
    else:
        return True  
    
def update_streak(user,entry_length,entry_type):
    streak = Streaks.objects.get(user=user)

    # Check if the entry is being made on a new day
    current_date = timezone.now().date()
    if streak.last_entry_date != current_date:
        # streak.current_streak += 1
        streak.last_entry_date = current_date
    streak.entry_length = entry_length
    streak.entry_type = entry_type
    streak.save()
    return streak

def update_last_entry_date(streak):
    streak.last_entry_date = timezone.now().date()
    streak.save()

def update_user_badges(user): 
    badges_dict = defaultdict(list)
    badges_earned = UserBadge.objects.filter(user=user).select_related('badge')
    for user_badge in badges_earned:
        badge_name = user_badge.badge.label
        earned_date = user_badge.created_at.date()
        badges_dict[badge_name].append(earned_date)
    return badges_dict
   
def get_total_coins(self, user):
    try:
        user_coins = Coins.objects.get(user=user)
        total_coins = user_coins.coins
    except Coins.DoesNotExist:
        total_coins = 0
    return total_coins