from rest_framework import serializers
from .models import Task


class TaskSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Task
        fields = ['id', 'user', 'title', 'subject', 'deadline', 'priority', 'completed']
        read_only_fields = ['id', 'user']
