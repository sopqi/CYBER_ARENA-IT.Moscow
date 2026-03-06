from django.contrib.auth import login
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib import messages
import datetime
from django.db import transaction
from .forms import SignUpForm, TournamentForm
from .models import Computer, Booking, User, Reputation, ProfileComment, Zone, Tournament, TournamentRegistration
from .services import get_student_schedule, get_groups_by_building
from .logic import generate_available_slots
from django.contrib.auth.decorators import user_passes_test
from django.views.decorators.http import require_POST




#admin?
def is_admin(user):
    return user.is_staff or user.is_superuser


# all tyrnir
def tournament_list(request):
    tournaments = Tournament.objects.all().order_by('-date')
    return render(request, 'tournaments/list.html', {'tournaments': tournaments})

#create tyrnir admin only
@user_passes_test(is_admin)
def tournament_create(request):
    if request.method == 'POST':
        form = TournamentForm(request.POST, request.FILES)

        if form.is_valid():
            tournament = form.save(commit=False)
            tournament.created_by = request.user
            tournament.save()
            messages.success(request, "Турнир успешно создан!")
            return redirect('tournament_list')

    else:
        form = TournamentForm()
    return render(request, 'tournaments/create.html', {'form': form})



def tournament_detail(request, pk):
    tournament = get_object_or_404(Tournament, pk=pk)
    is_registered = False

    if request.user.is_authenticated:
        is_registered = TournamentRegistration.objects.filter(user=request.user, tournament=tournament).exists()

    return render(request, 'tournaments/detail.html', {
        'tournament': tournament,
        'is_registered': is_registered
    })


@login_required
@require_POST
def tournament_register(request, pk):
    tournament = get_object_or_404(Tournament, pk=pk)

    if tournament.is_full:
        messages.error(request, "К сожалению, мест больше нет!")
        return redirect('tournament_detail', pk=pk)
    if TournamentRegistration.objects.filter(user=request.user, tournament=tournament).exists():
        messages.warning(request, "Вы уже зарегистрированы на этот турнир.")
        return redirect('tournament_detail', pk=pk)


    TournamentRegistration.objects.create(user=request.user, tournament=tournament)
    messages.success(request, "Вы успешно зарегистрировались на турнир! Удачи!")
    return redirect('tournament_detail', pk=pk)

def home(request):
    return render(request, 'index.html')


def map_view(request):
    zones = Zone.objects.all()
    active_zone_slug = request.GET.get('zone')

    if active_zone_slug:
        current_zone = get_object_or_404(Zone, slug=active_zone_slug)
    else:
        current_zone = zones.first()

    now = timezone.localtime(timezone.now())

    user_schedule = []
    if request.user.is_authenticated:
        user_schedule = get_student_schedule(request.user.group_number, now.date())

    computers_qs = Computer.objects.filter(zone=current_zone).order_by('number')

    computers_data = []
    for pc in computers_qs:
        status = pc.get_status()

        available_slots = []
        if request.user.is_authenticated:
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            pc_bookings = pc.bookings.filter(
                end_time__gt=now,
                start_time__gte=today_start,
                is_cancelled=False,
                is_no_show=False
            )
            available_slots = generate_available_slots(user_schedule, pc_bookings)

        computers_data.append({
            'obj': pc,
            'is_busy': status['is_busy'],
            'free_at': status['free_at'],
            'slots': available_slots
        })

    return render(request, 'map.html', {
        'zones': zones,
        'current_zone': current_zone,
        'computers': computers_data
    })


@login_required
def book_computer(request, pc_id):
    user = request.user

    if request.method == 'POST':
        if user.strikes >= 3:
            messages.error(request, "⛔ Доступ заблокирован! У вас 3 или более штрафов.")
            return redirect('profile')

        start_str = request.POST.get('start_time')
        end_str = request.POST.get('end_time')

        try:
            start_dt = timezone.make_aware(datetime.datetime.strptime(start_str, "%Y-%m-%dT%H:%M"))
            end_dt = timezone.make_aware(datetime.datetime.strptime(end_str, "%Y-%m-%dT%H:%M"))
        except (ValueError, TypeError):
            messages.error(request, "Ошибка формата времени.")
            return redirect('map')

        now = timezone.now()

        try:
            with transaction.atomic():
                pc = get_object_or_404(Computer.objects.select_for_update(), id=pc_id)
                if Booking.objects.filter(user=user, end_time__gt=now, is_cancelled=False, is_no_show=False).exists():
                    messages.warning(request, "У вас уже есть активная бронь!")
                    return redirect('profile')

                if Booking.objects.filter(computer=pc, start_time__lt=end_dt, end_time__gt=start_dt, is_cancelled=False,
                                          is_no_show=False).exists():
                    messages.error(request, "Это время уже успели занять. Выберите другой слот.")
                    return redirect('map')
                Booking.objects.create(
                    user=user,
                    computer=pc,
                    start_time=start_dt,
                    end_time=end_dt
                )

        except Exception as e:
            messages.error(request, f"Критическая ошибка базы: {e}")
            return redirect('map')

        messages.success(request, f"Успешно забронировано! Ждем вас в {start_dt.strftime('%H:%M')}")
        return redirect('profile')

    return redirect('map')


@login_required
def profile(request):
    now = timezone.now()
    active_bookings = request.user.bookings.filter(end_time__gt=now, is_cancelled=False,is_no_show=False ).order_by('start_time')
    history_bookings = request.user.bookings.exclude(id__in=active_bookings.values('id')).order_by('-start_time')
    return render(request, 'profile.html', {
        'active_bookings': active_bookings,
        'history_bookings': history_bookings
    })

def profile_view(request, username):
    user_obj = get_object_or_404(User, username=username)
    comments = user_obj.profile_comments.all().order_by('-created_at')
    return render(request, 'public_profile.html', {
        'profile_user': user_obj,
        'comments': comments
    })

@login_required
@require_POST
def toggle_reputation(request, user_id):
    target_user = get_object_or_404(User, id=user_id)
    if target_user == request.user:
        return redirect('profile_view', username=target_user.username)

    action = request.POST.get('action')
    value = 1 if action == 'plus' else -1

    rep, created = Reputation.objects.get_or_create(from_user=request.user, to_user=target_user, defaults={'value': value})
    if not created:
        if rep.value == value:
            rep.delete()
        else:
            rep.value = value
            rep.save()

    return redirect('profile_view', username=target_user.username)


@login_required
@require_POST
def add_profile_comment(request, username):
    target_user = get_object_or_404(User, username=username)
    text = request.POST.get('text')
    if text:
        ProfileComment.objects.create(author=request.user, profile_owner=target_user, text=text)
    return redirect('profile_view', username=username)


def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Добро пожаловать!")
            return redirect('/profile')
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form})


def get_groups_ajax(request):
    campus = request.GET.get('campus')
    groups = get_groups_by_building(campus) if campus else []
    return JsonResponse({'groups': groups})


@login_required
@require_POST
def cancel_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)

    if booking.end_time > timezone.now():
        booking.is_cancelled = True
        booking.save()
        messages.success(request, "Бронь успешно отменена! Место свободно для других.")
    else:
        messages.error(request, "Эту бронь уже нельзя отменить.")

    return redirect('profile')



@login_required
@require_POST
def tournament_unregister(request, pk):
    tournament = get_object_or_404(Tournament, pk=pk)
    reg = TournamentRegistration.objects.filter(user=request.user, tournament=tournament)
    if reg.exists():
        reg.delete()
        messages.success(request, "Вы отменили участие в турнире.")
    return redirect('tournament_detail', pk=pk)