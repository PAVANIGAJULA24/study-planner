from django.db import models
from django.contrib.auth.models import User

class Task(models.Model):

    PRIORITY_HIGH = 'High'
    PRIORITY_MEDIUM = 'Medium'
    PRIORITY_LOW = 'Low'

    PRIORITY_CHOICES = [
        (PRIORITY_HIGH, 'High'),
        (PRIORITY_MEDIUM, 'Medium'),
        (PRIORITY_LOW, 'Low'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    title = models.CharField(max_length=200)
    subject = models.CharField(max_length=100)
    deadline = models.DateField()
    priority = models.CharField(max_length=6, choices=PRIORITY_CHOICES, default=PRIORITY_MEDIUM)
    completed = models.BooleanField(default=False)

    def __str__(self):
        return self.title