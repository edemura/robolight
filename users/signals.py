from django.db.models.signals import post_save
from django.dispatch import receiver
from users.models import Orders
from users.tasks import R7FromOrders

@receiver(post_save, sender=Orders)
def create_robo7task_from_order(sender, instance, created, **kwargs):
    if created:
        R7FromOrders.delay(instance.id) 