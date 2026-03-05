import os
import django
from core.models import Computer, Zone


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'arena.settings')
django.setup()


def create_arena():
    Computer.objects.all().delete()
    Zone.objects.all().delete()
    training_zone = Zone.objects.create(name="Кабинет тренировок", slug="training")
    general_zone = Zone.objects.create(name="Общий зал", slug="general")

    print("Расставляем тренировочный зал")
    for i in range(1, 6):
        Computer.objects.create(
            zone=training_zone,
            number=i,
            specs='RTX 4090 / i9',
            x_pos=10 + (i * 13),
            y_pos=45
        )

    print("Расставляем общий зал")
    pc_num = 1
    for row in [30, 60]:
        for col in range(5):
            Computer.objects.create(
                zone=general_zone,
                number=pc_num,
                specs='RTX 3060 / i5',
                x_pos=15 + (col * 15),
                y_pos=row
            )
            pc_num += 1

    print("✅ Готово! 2 зала созданы.")


if __name__ == '__main__':
    create_arena()