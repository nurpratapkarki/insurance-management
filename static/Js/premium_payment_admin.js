document.addEventListener('DOMContentLoaded', function () {
    // Get relevant fields
    const policyHolderSelect = document.querySelector('#id_policy_holder'); // The dropdown
    const annualPremiumField = document.querySelector('#id_annual_premium'); // The annual premium field
    const amountField = document.querySelector('#id_amount'); // The interval payment field

    annualPremiumField.disabled = true; // Disable the annual premium field
    amountField.disabled = true; // Disable the amount field

    /**
     * Updates premium fields based on the selected policy holder.
     * @param {string} policyHolderId - The selected policy holder's ID.
     */
    function updatePremiumFields(policyHolderId) {
        if (!policyHolderId) {
            // Reset fields if no policy holder is selected
            annualPremiumField.value = '0.00';
            amountField.value = '0.00';
            return;
        }

        // Fetch policy holder data from the server
        fetch(`/api/policyholders/${policyHolderId}`) // Adjust API endpoint if needed
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Failed to fetch data: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log(data);
                
                if (data.error) {
                    console.error(data.error);
                    annualPremiumField.value = '0.00';
                    amountField.value = '0.00';
                } else {
                    // Update fields with calculated values
                    annualPremiumField.value = data.loaded_annual_premium;
                    amountField.value = data.interval_payment;
                }
            })
            .catch(error => {
                console.error('Error fetching policyholder data:', error);
                annualPremiumField.value = '0.00';
                amountField.value = '0.00';
            });
    }

    /**
     * Event listener for the policy holder select field.
     */
    $(policyHolderSelect).on('change.select2', function () {
        const selectedPolicyHolderId = this.value; // Get the selected policy holder ID
        console.log('PolicyHolder selected:', selectedPolicyHolderId); // Debugging log
        updatePremiumFields(selectedPolicyHolderId);
    });
});
