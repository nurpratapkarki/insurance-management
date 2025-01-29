# frontend-data.py
from .models import *
from django.db.models import Sum
from datetime import date

class Dashboard:
    """
    A model-like structure to fetch and display dashboard data with user-specific filtering.
    """
    def __init__(self, user):
        self.user = user
        self.user_branch = getattr(user, 'branch', None)
    
    def get_company_report(self):
        """Fetch company-wide or branch-specific aggregated data."""
        base_query = PolicyHolder.objects
        payments_query = PremiumPayment.objects
        agents_query = SalesAgent.objects

        if not self.user.is_superuser and self.user_branch:
            base_query = base_query.filter(branch=self.user_branch)
            payments_query = payments_query.filter(policy_holder__branch=self.user_branch)
            agents_query = agents_query.filter(branch=self.user_branch)

        return {
            'total_policy_holders': base_query.count(),
            'active_policy_holders': base_query.filter(status='Active').count(),
            'total_premiums': payments_query.aggregate(total=Sum('total_paid'))['total'] or 0,
            'outstanding_premiums': payments_query.filter(payment_status='Unpaid').aggregate(
                outstanding=Sum('remaining_premium')
            )['outstanding'] or 0,
            'total_agents': agents_query.count(),
        }

    def get_branch_reports(self):
        """Fetch data for all or specific branch."""
        if self.user.is_superuser:
            branches = Branch.objects.all()
        elif self.user_branch:
            branches = Branch.objects.filter(id=self.user_branch.id)
        else:
            return []

        branch_data = []
        for branch in branches:
            total_policies = PolicyHolder.objects.filter(branch=branch).count()
            total_premiums = PremiumPayment.objects.filter(
                policy_holder__branch=branch
            ).aggregate(total=Sum('total_paid'))['total'] or 0
            
            branch_data.append({
                'branch_name': branch.name,
                'total_policies': total_policies,
                'total_premiums': total_premiums,
            })

        return branch_data

    def get_sales_agent_reports(self):
        """Fetch data for all or branch-specific sales agents."""
        agents_query = SalesAgent.objects.all()
        
        if not self.user.is_superuser and self.user_branch:
            agents_query = agents_query.filter(branch=self.user_branch)

        agent_data = []
        for agent in agents_query:
            policies_query = PolicyHolder.objects.filter(agent=agent)
            total_policies_sold = policies_query.count()
            total_premium_collected = policies_query.aggregate(
                total=Sum('sum_assured')
            )['total'] or 0

            agent_data.append({
                'agent_name': agent.get_full_name(),
                'policies_sold': total_policies_sold,
                'premium_collected': total_premium_collected,
            })

        return agent_data


