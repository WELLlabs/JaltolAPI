from django.core.management.base import BaseCommand
from gee_api.models import Plan

class Command(BaseCommand):
    help = 'Create default pricing plans: Basic, Pro, Enterprise'

    def handle(self, *args, **options):
        # Basic Plan (Free)
        basic_plan, created = Plan.objects.get_or_create(
            name='basic',
            defaults={
                'display_name': 'Basic',
                'price': 0.00,
                'currency': 'INR',
                'duration_days': None,  # Lifetime
                'description': 'Free plan with basic access to Jaltol features',
                'features': [
                    'Access to basic maps',
                    'View up to 5 villages per month',
                    'Basic rainfall data',
                    'Community support',
                    'Basic API access (50 calls/day)'
                ],
                'limitations': [
                    'Limited village views (5/month)',
                    'Limited API calls (50/day)',
                    'No data export',
                    'No priority support'
                ],
                'max_api_calls_per_day': 50,
                'max_village_views_per_month': 5,
                'max_projects': 3,
                'is_active': True,
                'is_default': True
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('Created Basic plan'))
        else:
            self.stdout.write(self.style.WARNING('Basic plan already exists'))

        # Pro Plan (₹1000)
        pro_plan, created = Plan.objects.get_or_create(
            name='pro',
            defaults={
                'display_name': 'Pro',
                'price': 1000.00,
                'currency': 'INR',
                'duration_days': 30,  # Monthly subscription
                'description': 'Professional plan with unlimited access and advanced features',
                'features': [
                    'Unlimited village access',
                    'Advanced LULC analysis',
                    'Historical data (2000-present)',
                    'Data export (CSV, JSON)',
                    'Unlimited API access',
                    'Email support',
                    'Custom polygon analysis',
                    'Advanced rainfall analytics',
                    'Unlimited projects',
                    'Priority support'
                ],
                'limitations': [],
                'max_api_calls_per_day': None,  # Unlimited
                'max_village_views_per_month': None,  # Unlimited
                'max_projects': None,  # Unlimited
                'is_active': True,
                'is_default': False
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('Created Pro plan'))
        else:
            self.stdout.write(self.style.WARNING('Pro plan already exists'))

        # Enterprise Plan (Contact Sales)
        enterprise_plan, created = Plan.objects.get_or_create(
            name='enterprise',
            defaults={
                'display_name': 'Enterprise',
                'price': None,  # Contact for pricing
                'currency': 'INR',
                'duration_days': None,  # Custom contract
                'description': 'Enterprise plan with everything in Pro plus custom integrations and dedicated support',
                'features': [
                    'Everything in Pro',
                    'Unlimited API calls',
                    'Custom integrations',
                    'Dedicated support team',
                    'Training sessions',
                    'White-label options',
                    'SLA guarantee',
                    'Custom data sources',
                    'On-premise deployment options',
                    'Custom reporting',
                    'Multi-user team management',
                    'Advanced analytics dashboard'
                ],
                'limitations': [],
                'max_api_calls_per_day': None,  # Unlimited
                'max_village_views_per_month': None,  # Unlimited
                'max_projects': None,  # Unlimited
                'is_active': True,
                'is_default': False
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('Created Enterprise plan'))
        else:
            self.stdout.write(self.style.WARNING('Enterprise plan already exists'))

        self.stdout.write(
            self.style.SUCCESS('Successfully created/verified all pricing plans')
        ) 