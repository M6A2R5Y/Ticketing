from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from .models import Ticket, TicketNote, TicketHistory
from .forms import TicketForm, TicketNoteForm, TicketUpdateForm
import json
import google.generativeai as genai
from django.conf import settings


def signup(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Account created successfully for {user.username}!")
            return redirect('dashboard')
    else:
        form = UserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})


@login_required
def dashboard(request):
    # Base Queryset based on role
    if request.user.is_staff:
        tickets_qs = Ticket.objects.all()
        # Stats for Admin/Agent dashboard
        stats = {
            'total': tickets_qs.count(),
            'open': tickets_qs.filter(status='open').count(),
            'pending': tickets_qs.filter(status='pending').count(),
            'on_hold': tickets_qs.filter(status='on_hold').count(),
            'solved': tickets_qs.filter(status='solved').count(),
        }
    else:
        tickets_qs = Ticket.objects.filter(created_by=request.user)
        stats = None

    # Filtering
    status_filter = request.GET.get('status')
    priority_filter = request.GET.get('priority')
    search_query = request.GET.get('q')

    if status_filter:
        tickets_qs = tickets_qs.filter(status=status_filter)
    if priority_filter:
        tickets_qs = tickets_qs.filter(priority=priority_filter)
    if search_query:
        tickets_qs = tickets_qs.filter(
            Q(title__icontains=search_query) | Q(description__icontains=search_query)
        )

    context = {
        'tickets': tickets_qs,
        'stats': stats,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'search_query': search_query,
    }
    return render(request, 'tickets/dashboard.html', context)


@login_required
def ticket_create(request):
    if request.method == 'POST':
        form = TicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.created_by = request.user
            ticket.save()
            
            # Log history
            TicketHistory.objects.create(
                ticket=ticket,
                changed_by=request.user,
                change_summary="Ticket created."
            )
            
            messages.success(request, f"Ticket #{ticket.id} created successfully!")
            return redirect('ticket_detail', pk=ticket.id)
    else:
        form = TicketForm()
    return render(request, 'tickets/ticket_form.html', {'form': form})


@login_required
def ticket_detail(request, pk):
    if request.user.is_staff:
        ticket = get_object_or_404(Ticket, pk=pk)
        # Agents see all notes
        notes = ticket.notes.all()
    else:
        ticket = get_object_or_404(Ticket, pk=pk, created_by=request.user)
        # Regular users see only public notes
        notes = ticket.notes.filter(is_internal=False)

    history = ticket.history.all()

    if request.method == 'POST':
        # Check which form was submitted: note or ticket update
        if 'submit_note' in request.POST:
            note_form = TicketNoteForm(request.POST)
            if note_form.is_valid():
                note = note_form.save(commit=False)
                note.ticket = ticket
                note.author = request.user
                # Prevent non-staff from posting internal notes
                if not request.user.is_staff:
                    note.is_internal = False
                note.save()
                messages.success(request, "Note added successfully!")
                return redirect('ticket_detail', pk=ticket.id)
        
        elif 'submit_update' in request.POST and request.user.is_staff:
            update_form = TicketUpdateForm(request.POST, instance=ticket)
            if update_form.is_valid():
                # Detect what changed to build log summary
                changes = []
                orig = Ticket.objects.get(pk=pk)
                
                if orig.status != update_form.cleaned_data['status']:
                    changes.append(f"status from '{orig.get_status_display()}' to '{update_form.get_status_display()}'")
                if orig.priority != update_form.cleaned_data['priority']:
                    changes.append(f"priority from '{orig.get_priority_display()}' to '{update_form.get_priority_display()}'")
                if orig.assigned_to != update_form.cleaned_data['assigned_to']:
                    orig_assignee = orig.assigned_to.username if orig.assigned_to else "Unassigned"
                    new_assignee = update_form.cleaned_data['assigned_to'].username if update_form.cleaned_data['assigned_to'] else "Unassigned"
                    changes.append(f"assignee from '{orig_assignee}' to '{new_assignee}'")
                
                update_form.save()
                
                if changes:
                    summary = "Changed " + ", ".join(changes)
                    TicketHistory.objects.create(
                        ticket=ticket,
                        changed_by=request.user,
                        change_summary=summary
                    )
                messages.success(request, "Ticket updated successfully!")
                return redirect('ticket_detail', pk=ticket.id)
    
    note_form = TicketNoteForm()
    update_form = TicketUpdateForm(instance=ticket) if request.user.is_staff else None

    context = {
        'ticket': ticket,
        'notes': notes,
        'history': history,
        'note_form': note_form,
        'update_form': update_form,
    }
    return render(request, 'tickets/ticket_detail.html', context)


@login_required
def chatbot_api(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    if not user_message:
        return JsonResponse({'reply': "Hello! Please send a message."})

    msg_lower = user_message.lower()

    # 1. Automated Ticket Creation Helper via format: "ticket: Title | Description"
    if msg_lower.startswith('ticket:'):
        parts = user_message[7:].split('|')
        if len(parts) >= 2:
            title = parts[0].strip()
            desc = parts[1].strip()
            priority = 'medium'
            if len(parts) >= 3:
                p_candidate = parts[2].strip().lower()
                if p_candidate in ['low', 'medium', 'high', 'urgent']:
                    priority = p_candidate
            
            ticket = Ticket.objects.create(
                title=title,
                description=desc,
                priority=priority,
                created_by=request.user
            )
            TicketHistory.objects.create(
                ticket=ticket,
                changed_by=request.user,
                change_summary="Ticket created via Chatbot."
            )
            return JsonResponse({
                'reply': f"🎉 **Success!** Ticket **#{ticket.id}** has been created with title *'{title}'*."
            })
        else:
            return JsonResponse({
                'reply': "It looks like you want to create a ticket! Please use this exact format:\n`ticket: Title | Description | (optional: low/medium/high/urgent)`"
            })

    # 2. Live Gemini API integration
    if settings.GEMINI_API_KEY:
        try:
            # Query user's recent tickets to construct database context
            if request.user.is_staff:
                user_tickets = Ticket.objects.all()[:15]
            else:
                user_tickets = Ticket.objects.filter(created_by=request.user)[:15]

            tickets_context = []
            for t in user_tickets:
                tickets_context.append(
                    f"- Ticket #{t.id}: '{t.title}' | Status: {t.get_status_display()} | Priority: {t.get_priority_display()} | Created by: {t.created_by.username} | Assigned to: {t.assigned_to.username if t.assigned_to else 'None'}"
                )
            tickets_context_str = "\n".join(tickets_context) if tickets_context else "No active tickets."

            system_instruction = (
                "You are FlowBot, a professional support assistant for FlowDesk ticketing system.\n"
                f"The current user is {request.user.username}.\n"
                f"The user's role is {'Staff/Agent' if request.user.is_staff else 'Customer'}.\n\n"
                "Here are the active tickets related to the user in the database:\n"
                f"{tickets_context_str}\n\n"
                "Instructions:\n"
                "- If the user asks about a ticket's status, assignee, or priority, look up the database list above and summarize the details.\n"
                "- If the user wants to submit or create a new ticket, instruct them to use this exact syntax: "
                "`ticket: Short Title | Detailed Description` so the system can file it instantly.\n"
                "- Keep answers clear, professional, and relatively concise. Answer in markdown."
            )

            genai.configure(api_key=settings.GEMINI_API_KEY)
            model = genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                system_instruction=system_instruction
            )
            
            response = model.generate_content(user_message)
            return JsonResponse({'reply': response.text})
        except Exception as e:
            # Fall back to rule-based responder if API fails
            pass

    # 3. Fallback Smart Rule-Based Responder (Sandbox Mode)
    # Ticket status check query (e.g. "status of ticket #5" or "status #5")
    import re
    status_match = re.search(r'(?:status of ticket|ticket|status|#)\s*#?(\d+)', msg_lower)
    if status_match:
        ticket_id = status_match.group(1)
        try:
            if request.user.is_staff:
                ticket = Ticket.objects.get(pk=ticket_id)
            else:
                ticket = Ticket.objects.get(pk=ticket_id, created_by=request.user)
            return JsonResponse({
                'reply': f"Ticket **#{ticket.id}: {ticket.title}** is currently **{ticket.get_status_display()}** with priority **{ticket.get_priority_display()}**."
            })
        except Ticket.DoesNotExist:
            return JsonResponse({
                'reply': f"I couldn't find a ticket with ID #{ticket_id} belonging to you."
            })

    if 'create ticket' in msg_lower or 'new ticket' in msg_lower or 'submit ticket' in msg_lower:
        return JsonResponse({
            'reply': "I can help you file a new ticket! You can either click **Create Ticket** in the navigation bar or type it here directly using the following format:\n\n`ticket: Short Title | Detailed description here`"
        })
    elif 'hello' in msg_lower or 'hi' in msg_lower or 'hey' in msg_lower:
        return JsonResponse({
            'reply': f"Hello {request.user.username}! I am FlowBot, your Support Assistant. How can I help you today? You can check ticket statuses or create new tickets."
        })
    elif 'list' in msg_lower or 'my tickets' in msg_lower:
        tickets = Ticket.objects.filter(created_by=request.user)[:5]
        if not tickets.exists():
            return JsonResponse({'reply': "You don't have any tickets yet. Type `create ticket` if you'd like to make one!"})
        
        reply_lines = ["Here are your recent tickets:"]
        for t in tickets:
            reply_lines.append(f"- **#{t.id}**: {t.title} ({t.get_status_display()})")
        return JsonResponse({'reply': "\n".join(reply_lines)})
    else:
        return JsonResponse({
            'reply': "I am not sure I understand that. You can:\n- Type `hello` to greet me.\n- Ask for `status of ticket #123`.\n- Say `list` to see your recent tickets.\n- Type `ticket: Title | Description` to file a new support request."
        })

