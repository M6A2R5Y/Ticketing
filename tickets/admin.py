from django.contrib import admin
from .models import Ticket, TicketNote, TicketHistory

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'status', 'priority', 'created_by', 'assigned_to', 'created_at')
    list_filter = ('status', 'priority', 'created_at')
    search_fields = ('title', 'description', 'created_by__username', 'assigned_to__username')

@admin.register(TicketNote)
class TicketNoteAdmin(admin.ModelAdmin):
    list_display = ('id', 'ticket', 'author', 'is_internal', 'created_at')
    list_filter = ('is_internal', 'created_at')
    search_fields = ('content', 'ticket__title', 'author__username')

@admin.register(TicketHistory)
class TicketHistoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'ticket', 'changed_by', 'change_summary', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('change_summary', 'ticket__title', 'changed_by__username')
