from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Ticket, TicketNote, TicketHistory
import json

class TicketingSystemTests(TestCase):
    def setUp(self):
        # Create a customer and an agent
        self.customer = User.objects.create_user(username='customer1', password='password123')
        self.agent = User.objects.create_user(username='agent1', password='password123', is_staff=True)
        
        # Test ticket
        self.ticket = Ticket.objects.create(
            title="Unable to connect to printer",
            description="The printer displays offline error.",
            status="open",
            priority="medium",
            created_by=self.customer
        )
        
        # Clients for request simulation
        self.client_customer = Client()
        self.client_customer.login(username='customer1', password='password123')
        
        self.client_agent = Client()
        self.client_agent.login(username='agent1', password='password123')

    def test_ticket_creation(self):
        # Test that setup ticket exists
        self.assertEqual(Ticket.objects.count(), 1)
        self.assertEqual(self.ticket.status, 'open')
        self.assertEqual(str(self.ticket), f"#{self.ticket.id} - Unable to connect to printer (Open)")

    def test_note_permissions(self):
        # Create a public note
        note_public = TicketNote.objects.create(
            ticket=self.ticket,
            author=self.agent,
            content="Check if the USB cable is connected.",
            is_internal=False
        )
        # Create an internal note
        note_internal = TicketNote.objects.create(
            ticket=self.ticket,
            author=self.agent,
            content="Customer seems grumpy today.",
            is_internal=True
        )

        # Customer view: only sees public notes
        self.client_customer.login(username='customer1', password='password123')
        response = self.client_customer.get(reverse('ticket_detail', args=[self.ticket.id]))
        notes_in_context = response.context['notes']
        self.assertIn(note_public, notes_in_context)
        self.assertNotIn(note_internal, notes_in_context)

        # Agent view: sees all notes
        response = self.client_agent.get(reverse('ticket_detail', args=[self.ticket.id]))
        notes_in_context = response.context['notes']
        self.assertIn(note_public, notes_in_context)
        self.assertIn(note_internal, notes_in_context)

    def test_chatbot_interaction(self):
        # 1. Test greeting response
        url = reverse('chatbot_api')
        response = self.client_customer.post(
            url, 
            data=json.dumps({'message': 'hello there'}), 
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('Support Assistant', data['reply'])

        # 2. Test status check of ticket
        response = self.client_customer.post(
            url,
            data=json.dumps({'message': f'status of ticket #{self.ticket.id}'}),
            content_type='application/json'
        )
        data = response.json()
        self.assertIn('Open', data['reply'])

        # 3. Test auto ticket creation via FlowBot format
        response = self.client_customer.post(
            url,
            data=json.dumps({'message': 'ticket: Network slow | Wifi download speed is 1mbps'}),
            content_type='application/json'
        )
        data = response.json()
        self.assertIn('has been created', data['reply'])
        
        # Verify ticket was actually created in database
        self.assertEqual(Ticket.objects.count(), 2)
        new_ticket = Ticket.objects.get(title="Network slow")
        self.assertEqual(new_ticket.created_by, self.customer)
        self.assertEqual(new_ticket.description, "Wifi download speed is 1mbps")
