from django import forms
from .models import Ticket, TicketNote
from django.contrib.auth.models import User

class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['title', 'description', 'priority']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Enter ticket title', 'class': 'form-control'}),
            'description': forms.Textarea(attrs={'placeholder': 'Describe your issue in detail...', 'rows': 5, 'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
        }


class TicketNoteForm(forms.ModelForm):
    class Meta:
        model = TicketNote
        fields = ['content', 'is_internal']
        widgets = {
            'content': forms.Textarea(attrs={'placeholder': 'Type your message/note here...', 'rows': 3, 'class': 'form-control'}),
            'is_internal': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class TicketUpdateForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['status', 'priority', 'assigned_to']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'assigned_to': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show agents/staff in the assigned_to field
        self.fields['assigned_to'].queryset = User.objects.filter(is_staff=True)
        self.fields['assigned_to'].empty_label = "Unassigned"
