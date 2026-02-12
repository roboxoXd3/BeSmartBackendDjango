from django.core.management.base import BaseCommand
from django.utils import timezone
from vendors.models import EscrowTransaction

class Command(BaseCommand):
    help = 'Process held escrow transactions and release funds if due.'

    def handle(self, *args, **options):
        now = timezone.now()
        held_transactions = EscrowTransaction.objects.filter(
            status='held',
            release_date__lte=now
        )
        
        count = held_transactions.count()
        if count == 0:
            self.stdout.write(self.style.SUCCESS('No transactions to release.'))
            return

        self.stdout.write(f'Processing {count} transactions...')
        
        updated_count = held_transactions.update(status='released')
        
        self.stdout.write(self.style.SUCCESS(f'Successfully released {updated_count} transactions.'))
