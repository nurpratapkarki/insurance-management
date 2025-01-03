from rest_framework import serializers
from .models import (
    InsurancePolicy,
    SalesAgent,
    Branch,
    PolicyHolder,
    ClaimRequest,
    ClaimProcessing,
    PremiumPayment,
    EmployeePosition,
    Employee,
    PaymentProcessing,
    Underwriting,
    Company
)
class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = '__all__'

class InsurancePolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = InsurancePolicy
        fields = '__all__'


class SalesAgentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesAgent
        fields = '__all__'


class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = '__all__'

class PolicyHolderSerializer(serializers.ModelSerializer):
    class Meta:
        model = PolicyHolder
        fields = '__all__'
    def validate_sum_assured(self, value):
        policy = self.instance.policy if self.instance else self.initial_data.get('policy')
        if policy and (value < policy.min_sum_assured or value > policy.max_sum_assured):
            raise serializers.ValidationError(
                f"Sum assured must be between {policy.min_sum_assured} and {policy.max_sum_assured}."
            )
        return value
    

    def create(self, validated_data):
        branch = validated_data['branch']
        company = validated_data['company']
        last_policy = PolicyHolder.objects.filter(branch=branch, company=company).order_by('id').last()
        last_number = int(last_policy.policy_number[-6:]) if last_policy else 0
        validated_data['policy_number'] = f"{company.company_code}{branch.branch_code}{str(last_number + 1).zfill(6)}"
        return super().create(validated_data)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['agent'] = SalesAgentSerializer(instance.agent).data
        ret['company'] = CompanySerializer(instance.company).data
        ret['policy'] = InsurancePolicySerializer(instance.policy).data if instance.policy else None
        ret['branch'] = BranchSerializer(instance.branch).data if instance.branch else None
        return ret

    def create(self, validated_data):
        agent_data = validated_data.pop('agent')
        company_data = validated_data.pop('company')
        policy_data = validated_data.pop('policy', None)
        branch_data = validated_data.pop('branch', None)

        agent = SalesAgent.objects.get(**agent_data)
        company = Company.objects.get(**company_data)
        policy = InsurancePolicy.objects.get(**policy_data) if policy_data else None
        branch = Branch.objects.get(**branch_data) if branch_data else None

        policy_holder = PolicyHolder.objects.create(
            agent=agent,
            company=company,
            policy=policy,
            branch=branch,
            **validated_data
        )
        return policy_holder
class ClaimRequestSerializer(serializers.ModelSerializer):
    policy_holder = PolicyHolderSerializer(read_only=True)  
    policy_holder_id = serializers.PrimaryKeyRelatedField(
        queryset=PolicyHolder.objects.all(), source='policy_holder', write_only=True
    )
    policy = InsurancePolicySerializer(read_only=True)
    branch = BranchSerializer(read_only=True)
    class Meta:
        model = ClaimRequest
        fields = '__all__'


class ClaimProcessingSerializer(serializers.ModelSerializer):
    claim_request = ClaimRequestSerializer(read_only=True)
    claim_request_id = serializers.PrimaryKeyRelatedField(
        queryset=ClaimRequest.objects.all(), source='claim_request', write_only=True
    )

    class Meta:
        model = ClaimProcessing
        fields = '__all__'


class PremiumPaymentSerializer(serializers.ModelSerializer):
    policy_holder = PolicyHolderSerializer(read_only=True)
    policy_holder_id = serializers.PrimaryKeyRelatedField(
        queryset=PolicyHolder.objects.all(), source='policy_holder', write_only=True
    )

    class Meta:
        model = PremiumPayment
        fields = '__all__'

    def create(self, validated_data):
        payment = PremiumPayment(**validated_data)
        payment.calculate_premium()
        payment.save()
        return payment

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.calculate_premium()
        instance.save()
        return instance

class EmployeePositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeePosition
        fields = '__all__'



class EmployeeSerializer(serializers.ModelSerializer):
    employee_position = EmployeePositionSerializer(read_only=True)
    employee_position_id = serializers.PrimaryKeyRelatedField(
        queryset=EmployeePosition.objects.all(), source='employee_position', write_only=True
    )

    class Meta:
        model = Employee
        fields = '__all__'


class PaymentProcessingSerializer(serializers.ModelSerializer):
    claim_request = ClaimRequestSerializer(read_only=True)
    claim_request_id = serializers.PrimaryKeyRelatedField(
        queryset=ClaimRequest.objects.all(), source='claim_request', write_only=True
    )

    class Meta:
        model = PaymentProcessing
        fields = '__all__'


class UnderwritingSerializer(serializers.ModelSerializer):
    policy_holder = PolicyHolderSerializer(read_only=True)
    policy_holder_id = serializers.PrimaryKeyRelatedField(
        queryset=PolicyHolder.objects.all(), source='policy_holder', write_only=True
    )
    policy = InsurancePolicySerializer(read_only=True)
    policy_id = serializers.PrimaryKeyRelatedField(
        queryset=InsurancePolicy.objects.all(), source='policy', write_only=True
    )
    evaluated_by = EmployeeSerializer(read_only=True)
    evaluated_by_id = serializers.PrimaryKeyRelatedField(
        queryset=Employee.objects.all(), source='evaluated_by', write_only=True
    )

    class Meta:
        model = Underwriting
        fields = '__all__'
