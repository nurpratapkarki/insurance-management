document.addEventListener('DOMContentLoaded', function () {
    // Get relevant fields
    const policyHolderSelect = document.querySelector('#id_policy_holder'); // The dropdown
    const annualPremiumField = document.querySelector('#id_annual_premium'); // The annual premium field
    const amountField = document.querySelector('#id_amount'); // The interval payment field
    const form = document.querySelector('form'); // The main form

    // Disable the fields initially
    annualPremiumField.disabled = true;
    amountField.disabled = true;

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
                if (data.error) {
                    console.error(data.error);
                    annualPremiumField.value = '0.00';
                    amountField.value = '0.00';
                } else {
                    // Update fields with calculated values
                    annualPremiumField.value = data.loaded_annual_premium || '0.00';
                    amountField.value = data.interval_payment || '0.00';
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

    /**
     * Prevent form default reset behavior and ensure fields are submitted correctly.
     */
    form.addEventListener('submit', function (event) {
        event.preventDefault(); // Prevent default form submission

        // Enable fields to include them in the submission
        annualPremiumField.disabled = false;
        amountField.disabled = false;

        // Submit the form using JavaScript
        const formData = new FormData(form); // Collect form data
        const actionUrl = form.action; // Get the form's action URL

        fetch(actionUrl, {
            method: 'POST',
            body: formData,
        })
            .then(response => {
                if (response.ok) {
                    console.log('Form submitted successfully!');
                    window.location.reload(); // Reload or redirect as needed
                } else {
                    return response.json().then(data => {
                        console.error('Submission failed:', data);
                        alert('Error submitting form. Please check your inputs.');
                    });
                }
            })
            .catch(error => {
                console.error('Error submitting form:', error);
                alert('An unexpected error occurred while submitting the form.');
            });
    });
});
