// KNAPS Onboarding JavaScript
// Mobile-first, premium UX

(function() {
    'use strict';

    let currentStep = 1;
    let isVerified = false;
    const totalSteps = 6;

    let data = {
        pan: '',
        fullName: '',
        dob: '',
        gender: '',
        phone: '',
        whatsapp: '',
        email: ''
    };

    // Initialize
    if (typeof frappe !== 'undefined') {
        frappe.ready(init);
    } else {
        window.addEventListener('DOMContentLoaded', init);
    }

    function init() {
        setupEventListeners();
        updateUI();
    }

    function setupEventListeners() {
        // PAN: uppercase, alphanumeric only
        const panInput = document.getElementById('pan-input');
        if (panInput) {
            panInput.addEventListener('input', function() {
                this.value = this.value.toUpperCase().replace(/[^A-Z0-9]/g, '');
                hideError('pan-error');
            });
            panInput.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') verifyPAN();
            });
        }

        // OTP: numbers only
        const otpInput = document.getElementById('otp-input');
        if (otpInput) {
            otpInput.addEventListener('input', function() {
                this.value = this.value.replace(/\D/g, '');
                hideError('otp-error');
            });
            otpInput.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') verifyOTP();
            });
        }

        // Enter key support for other inputs
        const fields = ['full-name', 'phone', 'whatsapp', 'email'];
        fields.forEach(function(id) {
            const el = document.getElementById(id);
            if (el) {
                el.addEventListener('keypress', function(e) {
                    if (e.key === 'Enter') {
                        const nextStep = currentStep + 1;
                        if (nextStep <= 6) goToStep(nextStep);
                    }
                });
            }
        });
    }

    function goToStep(step) {
        // Prevent going back to welcome or PAN/OTP after verification
        if (isVerified && step < 4) return;

        if (!validateCurrentStep()) return;
        saveData();

        // Prevent going back before verification
        if (isVerified && step < currentStep && step < 4) {
            return;
        }

        currentStep = step;
        updateUI();
        if (step === 6) updateReview();
    }

    function validateCurrentStep() {
        if (currentStep === 1) return true;
        if (currentStep === 2) {
            const pan = document.getElementById('pan-input').value.trim();
            if (pan.length !== 10) {
                showError('pan-error', 'Please enter a valid 10-character PAN');
                return false;
            }
        }
        if (currentStep === 3) {
            const otp = document.getElementById('otp-input').value.trim();
            if (otp.length !== 6) {
                showError('otp-error', 'Please enter a valid 6-digit OTP');
                return false;
            }
        }
        return true;
    }

    function saveData() {
        if (currentStep === 2) data.pan = document.getElementById('pan-input').value.trim().toUpperCase();
        if (currentStep === 4) {
            data.fullName = document.getElementById('full-name').value.trim();
            data.dob = document.getElementById('dob').value;
            data.gender = document.getElementById('gender').value;
        }
        if (currentStep === 5) {
            data.phone = document.getElementById('phone').value.trim();
            data.whatsapp = document.getElementById('whatsapp').value.trim();
            data.email = document.getElementById('email').value.trim();
        }
    }

    function updateUI() {
        // Hide all steps
        document.querySelectorAll('.step').forEach(function(el) {
            el.classList.remove('active');
        });

        // Show current step
        const stepEl = document.getElementById('step-' + currentStep);
        if (stepEl) stepEl.classList.add('active');

        // Update stepper
        updateStepper();

        // Show/hide welcome header and stepper
        const welcomeHeader = document.getElementById('welcome-header');
        const stepper = document.getElementById('stepper');

        if (welcomeHeader) {
            welcomeHeader.style.display = currentStep === 1 ? 'block' : 'none';
        }
        if (stepper) {
            // Show stepper from step 2 onwards
            stepper.style.display = currentStep >= 2 ? 'block' : 'none';
        }
    }

    function updateStepper() {
        const dots = document.querySelectorAll('.dot');
        const progress = document.getElementById('stepper-progress');

        dots.forEach(function(dot, index) {
            dot.classList.remove('active', 'completed');
            if (index + 1 < currentStep) {
                dot.classList.add('completed');
                dot.innerHTML = '✓';
            } else if (index + 1 === currentStep) {
                dot.classList.add('active');
                dot.textContent = index + 1;
            } else {
                dot.textContent = index + 1;
            }
        });

        if (progress) {
            const pct = ((currentStep - 1) / (totalSteps - 1)) * 100;
            progress.style.width = 'calc(' + pct + '% - 0px)';
        }
    }

    function updateReview() {
        setText('review-pan', data.pan);
        setText('review-name', data.fullName);
        setText('review-dob', data.dob || '-');
        setText('review-phone', data.phone);
        setText('review-email', data.email);
    }

    function setText(id, value) {
        const el = document.getElementById(id);
        if (el) el.textContent = value || '-';
    }

    function showError(id, msg) {
        const el = document.getElementById(id);
        if (el) {
            el.textContent = msg;
            el.classList.add('show');
        }
    }

    function hideError(id) {
        const el = document.getElementById(id);
        if (el) el.classList.remove('show');
    }

    // API Functions
    window.verifyPAN = function() {
        const pan = document.getElementById('pan-input').value.trim().toUpperCase();
        if (pan.length !== 10) {
            showError('pan-error', 'Please enter a valid 10-character PAN');
            return;
        }

        data.pan = pan;
        hideError('pan-error');

        callAPI('knaps.templates.pages.onboarding.verify_pan', { pan: pan }, function(r) {
            if (r.message.success) {
                if (r.message.exists && r.message.data) {
                    document.getElementById('full-name').value = r.message.data.full_name || '';
                    document.getElementById('phone').value = r.message.data.phone || '';
                    document.getElementById('email').value = r.message.data.email || '';
                    data.fullName = r.message.data.full_name || '';
                    data.phone = r.message.data.phone || '';
                    data.email = r.message.data.email || '';
                }
                goToStep(3);
            } else {
                showError('pan-error', 'Something went wrong. Please try again.');
            }
        });
    };

    window.verifyOTP = function() {
        const otp = document.getElementById('otp-input').value.trim();
        if (otp.length !== 6) {
            showError('otp-error', 'Please enter a valid 6-digit OTP');
            return;
        }

        callAPI('knaps.templates.pages.onboarding.verify_otp', { otp: otp }, function(r) {
            if (r.message.success) {
                hideError('otp-error');
                isVerified = true;
                goToStep(4);
            } else {
                showError('otp-error', r.message.message || 'Invalid OTP. Please try again.');
            }
        });
    };

    window.submitOnboarding = function() {
        callAPI('knaps.templates.pages.onboarding.save_onboarding', { data: JSON.stringify(data) }, function(r) {
            if (r.message.success) {
                document.querySelectorAll('.step').forEach(function(el) {
                    el.classList.remove('active');
                });
                document.getElementById('step-success').classList.add('active');
                document.getElementById('stepper').classList.add('hidden');
            }
        });
    };

    window.goToStep = goToStep;

    function callAPI(method, args, callback) {
        if (typeof frappe !== 'undefined') {
            frappe.call({
                method: method,
                args: args,
                callback: callback,
                error: function() {
                    alert('Network error. Please try again.');
                }
            });
        }
    }

})();