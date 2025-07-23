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
                'description': 'Perfect for researchers and individual users exploring watershed impact analysis',
                'features': [
                    'Access to 5 village level LULC analysis per month',
                    'Village level Cropping Intensity historical trends',
                    'IMD Gridded Rainfall historical data',
                    'Data Export limited to 5 villages',
                    'Community Support'
                ],
                'limitations': [],
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
            # Update existing plan
            basic_plan.description = 'Perfect for researchers and individual users exploring watershed impact analysis'
            basic_plan.features = [
                'Access to 5 village level LULC analysis per month',
                'Village level Cropping Intensity historical trends',
                'IMD Gridded Rainfall historical data',
                'Data Export limited to 5 villages',
                'Community Support'
            ]
            basic_plan.limitations = []
            basic_plan.save()
            self.stdout.write(self.style.WARNING('Updated Basic plan'))

        # Pro Plan (₹1000)
        pro_plan, created = Plan.objects.get_or_create(
            name='pro',
            defaults={
                'display_name': 'Pro',
                'price': 1000.00,
                'currency': 'INR',
                'duration_days': 30,  # Monthly subscription
                'description': 'Ideal for professionals, NGOs, and small organizations needing comprehensive analysis',
                'features': [
                    'Access to unlimited village level LULC analysis per month',
                    'Village level Cropping Intensity historical trends',
                    'Farm parcel level Cropping Intensity historical trends',
                    'Unlimited Data Export',
                    'Priority 24h support'
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
            # Update existing plan
            pro_plan.description = 'Ideal for professionals, NGOs, and small organizations needing comprehensive analysis'
            pro_plan.features = [
                'Access to unlimited village level LULC analysis per month',
                'Village level Cropping Intensity historical trends',
                'Farm parcel level Cropping Intensity historical trends',
                'Unlimited Data Export',
                'Priority 24h support'
            ]
            pro_plan.limitations = []
            pro_plan.save()
            self.stdout.write(self.style.WARNING('Updated Pro plan'))

        # Enterprise Plan (Contact Sales)
        enterprise_plan, created = Plan.objects.get_or_create(
            name='enterprise',
            defaults={
                'display_name': 'Enterprise',
                'price': None,  # Contact for pricing
                'currency': 'INR',
                'duration_days': None,  # Custom contract
                'description': 'Designed for large organizations, research institutions, and donors requiring advanced features',
                'features': [
                    'Everything in Pro',
                    'Unlimited API calls',
                    'Batch Village level Cropping Intensity historical trends (useful for research/donors portfolio impact assessment)',
                    'Custom Integrations to your org website/dashboard',
                    'Dedicated support team'
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
            # Update existing plan
            enterprise_plan.description = 'Designed for large organizations, research institutions, and donors requiring advanced features'
            enterprise_plan.features = [
                'Everything in Pro',
                'Unlimited API calls',
                'Batch Village level Cropping Intensity historical trends (useful for research/donors portfolio impact assessment)',
                'Custom Integrations to your org website/dashboard',
                'Dedicated support team'
            ]
            enterprise_plan.limitations = []
            enterprise_plan.save()
            self.stdout.write(self.style.WARNING('Updated Enterprise plan'))

        self.stdout.write(
            self.style.SUCCESS('Successfully created/updated all pricing plans')
        ) 