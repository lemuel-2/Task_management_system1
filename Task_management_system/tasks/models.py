from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class Task(models.Model):
    PRIORITY_LOW = 1
    PRIORITY_MEDIUM = 2
    PRIORITY_HIGH = 3

    PRIORITY_CHOICES = [
        (PRIORITY_LOW, 'Low'),
        (PRIORITY_MEDIUM, 'Medium'),
        (PRIORITY_HIGH, 'High'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    assigned_to = models.CharField(max_length=100, blank=True, default='')
    priority = models.IntegerField(choices=PRIORITY_CHOICES, default=PRIORITY_MEDIUM)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(blank=True, null=True)
    due_date = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    MAX_DUE_YEARS = 10

    class Meta:
        ordering = ['completed', '-priority', '-created_at']

    def __str__(self):
        return self.title

    def clean(self):
        super().clean()

        if self.due_date:
            today = timezone.localdate()
            if self.due_date < today:
                raise ValidationError({
                    'due_date': _('Due date cannot be before today.')
                })

            try:
                max_due = today.replace(year=today.year + self.MAX_DUE_YEARS)
            except ValueError:
                max_due = today.replace(year=today.year + self.MAX_DUE_YEARS, day=28)

            if self.due_date > max_due:
                raise ValidationError({
                    'due_date': _(
                        'Due date must be within %(years)d years from today.'
                    ) % {'years': self.MAX_DUE_YEARS}
                })

    def save(self, *args, **kwargs):
        if self.completed and self.completed_at is None:
            self.completed_at = timezone.now()
        if not self.completed:
            self.completed_at = None

        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def is_overdue(self):
        return bool(
            self.due_date and not self.completed and self.due_date < timezone.localdate()
        )

    @property
    def due_status(self):
        if self.is_overdue:
            return _('Overdue')
        return _('Completed') if self.completed else _('Open')

    def get_absolute_url(self):
        return reverse('tasks:task-detail', kwargs={'pk': self.pk})
