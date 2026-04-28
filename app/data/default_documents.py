"""
Default documents for seeding the Customer Support Assistant knowledge base.
Contains policy, support, and scheduling information for demonstration.
"""

from typing import List, Dict

DEFAULT_DOCUMENTS: List[Dict[str, str]] = [
    {
        'chunk_id': 'policy_returns_v1',
        'source': 'https://help.example.com/return-policy',
        'text': (
            'Return Policy\n\n'
            'You can return unworn items within 30 days of purchase with original receipt. '
            'Items must be in original condition with tags attached.\n\n'
            'IMPORTANT: Items over $200 require manual approval for returns. Please email '
            'support@company.com with your order details for items over $200.\n\n'
            'Exceptions: Final sale items, customized products, and intimate apparel cannot '
            'be returned. Shoes must be unworn with original box.\n\n'
            'Refunds will be processed to original payment method within 5-7 business days '
            'after we receive your return.'
        )
    },
    {
        'chunk_id': 'policy_shipping_v1',
        'source': 'https://help.example.com/shipping',
        'text': (
            'Shipping Information\n\n'
            'Free standard shipping on orders over $50. Standard shipping takes 3-5 business '
            'days. Express shipping available for $9.99 (1-2 business days).\n\n'
            'International shipping available to select countries. Shipping costs calculated '
            'at checkout based on destination and weight.\n\n'
            'Orders placed before 2 PM EST ship same day. Weekend orders ship on the next '
            'business day.'
        )
    },
    {
        'chunk_id': 'sizing_guide_v1',
        'source': 'https://help.example.com/sizing',
        'text': (
            'Size Guide\n\n'
            'Clothing sizes run true to size. Please refer to our size chart for measurements.\n\n'
            'For shoes: If between sizes, we recommend sizing up for comfort. Athletic shoes '
            'may run small - consider sizing up half a size.\n\n'
            'Exchanges for different sizes are free within 30 days. Use our online size guide '
            'tool for personalized recommendations.'
        )
    },
    {
        'chunk_id': 'support_contact_v1',
        'source': 'https://help.example.com/contact',
        'text': (
            'Customer Support\n\n'
            'Contact us Monday-Friday 9 AM - 6 PM EST:\n'
            '- Email: support@example.com\n'
            '- Phone: 1-800-555-0123\n'
            '- Live chat available on our website\n\n'
            'For order issues, have your order number ready. Response time is typically '
            'within 24 hours for email inquiries.\n\n'
            'You can also track your order status online using your order number and email address.'
        )
    },
    {
        'chunk_id': 'scheduling_consultation_v1',
        'source': 'https://help.example.com/scheduling/consultations',
        'text': (
            'Consultation Meeting Policy\n\n'
            'Standard consultation calls are 30 minutes in duration. Extended consultations '
            '(60 minutes) are available upon request.\n\n'
            'All consultation meetings must be scheduled at least 24 hours in advance. '
            'Same-day appointments are not available.\n\n'
            'Meetings are conducted via video call. A calendar invitation with the meeting '
            'link will be sent to all attendees.\n\n'
            'Cancellation policy: Please cancel or reschedule at least 4 hours before the '
            'scheduled time.'
        )
    },
    {
        'chunk_id': 'scheduling_demo_v1',
        'source': 'https://help.example.com/scheduling/demos',
        'text': (
            'Product Demo Scheduling\n\n'
            'Product demonstration sessions are 45 minutes long and include a live walkthrough '
            'of features.\n\n'
            'Demos are available Monday through Friday, between 9 AM and 5 PM EST. No weekend '
            'demos available.\n\n'
            'For group demos (more than 3 attendees), please schedule at least 48 hours in advance.\n\n'
            'After the demo, attendees will receive a follow-up email with resources and next steps.'
        )
    },
    {
        'chunk_id': 'scheduling_support_v1',
        'source': 'https://help.example.com/scheduling/support',
        'text': (
            'Technical Support Calls\n\n'
            'Technical support calls are 30 minutes by default. Complex issues may require '
            'follow-up sessions.\n\n'
            'Priority support is available for enterprise customers with guaranteed 4-hour '
            'response time.\n\n'
            'Before scheduling a support call, please gather:\n'
            '- Your account/order number\n'
            '- Description of the issue\n'
            '- Screenshots if applicable\n\n'
            'Support calls are available 24/7 for critical issues.'
        )
    },
    {
        'chunk_id': 'scheduling_timezone_v1',
        'source': 'https://help.example.com/scheduling/timezones',
        'text': (
            'Timezone Information\n\n'
            'All meeting times are displayed in your local timezone when booking through our system.\n\n'
            'Our team operates primarily in EST (Eastern Standard Time). For international clients, '
            'we offer early morning (7 AM EST) and late afternoon (6 PM EST) slots.\n\n'
            'When scheduling, please confirm your timezone to avoid confusion. Calendar invitations '
            'will include timezone information.\n\n'
            'Default timezone for all meetings is America/New_York (EST/EDT).'
        )
    },
]
