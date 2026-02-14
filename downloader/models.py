from django.db import models
from django.utils import timezone

class TorrentTask(models.Model):
    STATUS_CHOICES = [
        ('queued', 'Queued'),
        ('checking', 'Checking'),
        ('downloading', 'Downloading'),
        ('seeding', 'Seeding'),
        ('paused', 'Paused'),
        ('error', 'Error'),
        ('completed', 'Completed'),
    ]

    name = models.CharField(max_length=255, blank=True)
    info_hash = models.CharField(max_length=40, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='queued')
    progress = models.FloatField(default=0.0)
    download_speed = models.IntegerField(default=0, help_text="Bytes per second")
    upload_speed = models.IntegerField(default=0, help_text="Bytes per second")
    total_size = models.BigIntegerField(default=0)
    eta = models.IntegerField(default=0, help_text="Estimated time in seconds")
    save_path = models.CharField(max_length=1024)
    added_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name or self.info_hash
