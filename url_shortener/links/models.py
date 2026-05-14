from django.db import models
from django.utils.text import slugify
import string
import random

class Link(models.Model):
    original_url = models.URLField(max_length=2000)
    short_code = models.CharField(max_length=10, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    clicks = models.IntegerField(default=0)
    qr_scans = models.IntegerField(default=0)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.short_code} -> {self.original_url}"

    @staticmethod
    def generate_short_code():
        """Generate a unique 6-character short code"""
        chars = string.ascii_letters + string.digits
        while True:
            code = ''.join(random.choice(chars) for _ in range(6))
            if not Link.objects.filter(short_code=code).exists():
                return code

    def save(self, *args, **kwargs):
        if not self.short_code:
            self.short_code = self.generate_short_code()
        super().save(*args, **kwargs)
