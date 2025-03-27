from import_export import resources
from .models import *

class OccupationResource(resources.ModelResource):
    class Meta:
        model = Occupation
        fields = ('id', 'name', 'risk_category')

class BonusRateResource(resources.ModelResource):
    class Meta:
        model = BonusRate
        fields = ('id', 'year', 'policy_type', 'min_year', 'max_year', 'bonus_per_thousand')

class MortalityRateResource(resources.ModelResource):
    class Meta:
        model = MortalityRate
        fields = ('id', 'age_group_start', 'age_group_end', 'rate')

class InsurancePolicyResource(resources.ModelResource):
    class Meta:
        model = InsurancePolicy
        exclude = ('created_at',)

class DurationFactorResource(resources.ModelResource):
    class Meta:
        model = DurationFactor
        fields = ('id', 'min_duration', 'max_duration', 'factor', 'policy_type') 