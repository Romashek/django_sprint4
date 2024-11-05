from django import forms
from django.utils import timezone

from .models import Post, Comment


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text', ]


class PostForm(forms.ModelForm):

    class Meta:
        model = Post
        exclude = ('author', 'is_published', 'location')
        widgets = {
            'pub_date': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'value': timezone.now().strftime('%Y-%m-%dT%H:%M')}),
        }
