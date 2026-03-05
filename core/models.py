from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models import Sum
from django.utils import timezone

class Zone(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название зоны")
    slug = models.SlugField(unique=True, verbose_name="URL-метка (английскими)")
    description = models.TextField(blank=True, verbose_name="Описание")

    def __str__(self):
        return self.name

class User(AbstractUser):
    CAMPUSES = (
        ('Судостроительная', 'Судостроительная'),
        ('Коломенская', 'Коломенская'),
        ('Академика Миллионщикова', 'Академика Миллионщикова'),
        ('Бирюлёво', 'Бирюлёво'),
    )

    fio = models.CharField(max_length=150, verbose_name="ФИО", default="")
    campus = models.CharField(max_length=50, choices=CAMPUSES, verbose_name="Корпус", default='Академика Миллионщикова')
    group_number = models.CharField(max_length=50, verbose_name="Группа")

    @property
    def strikes(self):
        return self.bookings.filter(is_no_show=True).count()

    @property
    def reputation_score(self):
        result = self.reputations_received.aggregate(total=Sum('value'))['total']
        return result if result else 0


class Computer(models.Model):
    zone = models.ForeignKey(Zone, on_delete=models.CASCADE, related_name='computers', null=True)
    number = models.IntegerField()
    specs = models.CharField(max_length=200, default="RTX 4060 / i5")
    x_pos = models.IntegerField(default=0)
    y_pos = models.IntegerField(default=0)

    class Meta:
        unique_together = ('zone', 'number')

    def __str__(self):
        return f"PC #{self.number}"

    def get_status(self):
        now = timezone.now()
        active_booking = self.bookings.filter(start_time__lte=now, end_time__gt=now, is_cancelled=False, is_no_show=False).order_by('end_time').last()

        if active_booking:
            return {'is_busy': True, 'free_at': active_booking.end_time}
        return {'is_busy': False, 'free_at': None}


class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    computer = models.ForeignKey(Computer, on_delete=models.CASCADE, related_name='bookings')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_cancelled = models.BooleanField(default=False, verbose_name="Отменена пользователем")
    is_no_show = models.BooleanField(default=False, verbose_name="Не явка (СТРАЙК)")

    def __str__(self):
        return f"{self.user.username} - PC {self.computer.number}"


class Reputation(models.Model):
    VALUES = ((1, '+REP'), (-1, '-REP'))
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reputations_given')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reputations_received')
    value = models.SmallIntegerField(choices=VALUES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('from_user', 'to_user')


class ProfileComment(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='authored_comments')
    profile_owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='profile_comments')
    text = models.TextField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)


class Tournament(models.Model):
    GAMES = (
        ('CS2', 'Counter-Strike 2'),
        ('Dota 2', 'Dota 2'),
        ('Valorant', 'Valorant'),
        ('Apex', 'Apex Legends'),
        ('Other', 'Другое')
    )

    title = models.CharField(max_length=150, verbose_name="Название турнира")
    game = models.CharField(max_length=20, choices=GAMES, verbose_name="Дисциплина")
    image = models.ImageField(upload_to='tournaments/', verbose_name="Постер турнира")
    description = models.TextField(verbose_name="Описание и правила")
    max_participants = models.PositiveIntegerField(default=10, verbose_name="Макс. участников")
    date = models.DateTimeField(verbose_name="Дата проведения")

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    @property
    def current_participants_count(self):
        return self.registrations.count()

    @property
    def is_full(self):
        return self.current_participants_count >= self.max_participants

    def __str__(self):
        return self.title


class TournamentRegistration(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='registrations')
    registered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'tournament')