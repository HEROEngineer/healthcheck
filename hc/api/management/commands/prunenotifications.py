from django.core.management.base import BaseCommand
from django.db.models import Min

from hc.api.models import Notification, Check


class Command(BaseCommand):
    help = 'Prune stored notifications'

    def handle(self, *args, **options):
        total = 0

        q = Check.objects.filter(n_pings__gt=100)
        q = q.annotate(min_ping_date=Min("ping__created"))
        for check in q:
            qq = Notification.objects.filter(owner_id=check.id,
                                             created__lt=check.min_ping_date)

            num_deleted, _ = qq.delete()
            total += num_deleted

        return "Done! Pruned %d notifications." % total
