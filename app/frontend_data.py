from .models import *
from django.db.models import Sum
from datetime import date

class Dashboard:
    """
    A model-like structure to fetch and display dashboard data.
    """
    @staticmethod
    def get_company_report():
        """Fetch company-wide aggregated data."""
        

        today = date.today()
        return {
            'total_policy_holders': PolicyHolder.objects.count(),
            'active_policy_holders': PolicyHolder.objects.filter(status='Active').count(),
            'total_premiums': PremiumPayment.objects.aggregate(total=Sum('total_paid'))['total'] or 0,
            'outstanding_premiums': PremiumPayment.objects.filter(payment_status='Unpaid').aggregate(
                outstanding=Sum('remaining_premium')
            )['outstanding'] or 0,
            'total_agents': SalesAgent.objects.count(),
        }

    @staticmethod
    def get_branch_reports():
        """Fetch data for each branch."""
        

        branches = Branch.objects.all()
        branch_data = []

        for branch in branches:
            total_policies = PolicyHolder.objects.filter(branch=branch).count()
            total_premiums = PremiumPayment.objects.filter(policy_holder__branch=branch).aggregate(
                total=Sum('total_paid')
            )['total'] or 0
            branch_data.append({
                'branch_name': branch.name,
                'total_policies': total_policies,
                'total_premiums': total_premiums,
            })

        return branch_data

    @staticmethod
    def get_sales_agent_reports():
        """Fetch data for all sales agents."""
        # from myapp.models import SalesAgent, PolicyHolder

        agents = SalesAgent.objects.all()
        agent_data = []

        for agent in agents:
            total_policies_sold = PolicyHolder.objects.filter(agent=agent).count()
            total_premium_collected = PolicyHolder.objects.filter(agent=agent).aggregate(
                total=Sum('sum_assured')
            )['total'] or 0

            agent_data.append({
                'agent_name': agent.get_full_name(),
                'policies_sold': total_policies_sold,
                'premium_collected': total_premium_collected,
            })

        return agent_data