from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import User, Computer, Booking, Reputation, ProfileComment
from django.contrib import admin, messages


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('computer', 'user', 'start_time', 'end_time', 'is_cancelled', 'is_no_show')
    list_filter = ('start_time', 'is_cancelled', 'is_no_show')
    actions = ['mark_as_no_show']

    @admin.action(description="Страйк за неявку")
    def mark_as_no_show(self, request, queryset):
        count = 0
        for booking in queryset:
            if not booking.is_no_show and not booking.is_cancelled:
                booking.is_no_show = True
                booking.save()
                booking.user.strikes += 1
                booking.user.save()
                count += 1

        self.message_user(request, f"{count} броней отмечены как 'Неявка'. Пользователям выданы штрафы.", level=messages.SUCCESS)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'fio', 'group_number', 'campus', 'reputation_score', 'is_staff')
    list_filter = ('campus', 'is_staff')
    search_fields = ('username', 'fio', 'group_number')
    fieldsets = UserAdmin.fieldsets + (
        ('Студенческие данные', {'fields': ('fio', 'campus', 'group_number')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Студенческие данные', {'fields': ('fio', 'campus', 'group_number')}),
    )

@admin.register(Computer)
class ComputerAdmin(admin.ModelAdmin):
    list_display = ('zone','number', 'status_colored', 'coords')
    search_fields = ('number', 'specs')

    def status_colored(self, obj):
        status = obj.get_status()
        if status['is_busy']:
            return format_html('<span style="color: red;">⛔ Занят до {}</span>', status['free_at'].strftime('%H:%M'))
        return format_html('<span style="color: lime;">✅ Свободен</span>')

    status_colored.short_description = "Статус"

    def coords(self, obj):
        return f"X:{obj.x_pos} Y:{obj.y_pos}"


admin.site.register(Reputation)
admin.site.register(ProfileComment)