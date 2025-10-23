// =============================================
// Medical AI - Frontend JavaScript
// =============================================

// === WIZARD FORM NAVIGATION ===
let currentStep = 1;
const totalSteps = 3;

function updateProgress() {
    const progress = (currentStep / totalSteps) * 100;
    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');
    const progressPercent = document.getElementById('progressPercent');

    if (progressFill) progressFill.style.width = progress + '%';
    if (progressText) progressText.textContent = `Bước ${currentStep}/${totalSteps}`;
    if (progressPercent) progressPercent.textContent = `${Math.round(progress)}%`;
}

function showStep(stepNumber) {
    // Hide all steps
    document.querySelectorAll('.wizard-step').forEach(step => {
        step.classList.remove('active');
    });

    // Show target step
    const targetStep = document.querySelector(`.wizard-step[data-step="${stepNumber}"]`);
    if (targetStep) {
        targetStep.classList.add('active');
        currentStep = stepNumber;
        updateProgress();

        // Scroll to top
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
}

function nextStep() {
    // Validate current step
    const currentStepEl = document.querySelector(`.wizard-step[data-step="${currentStep}"]`);
    const inputs = currentStepEl.querySelectorAll('input[required], select[required]');

    let isValid = true;
    inputs.forEach(input => {
        if (!input.value) {
            isValid = false;
            input.classList.add('border-red-500');

            // Reset border color after 2 seconds
            setTimeout(() => {
                input.classList.remove('border-red-500');
            }, 2000);
        }
    });

    if (!isValid) {
        alert('Vui lòng điền đầy đủ thông tin bắt buộc!');
        return;
    }

    if (currentStep < totalSteps) {
        showStep(currentStep + 1);
    }
}

function prevStep() {
    if (currentStep > 1) {
        showStep(currentStep - 1);
    }
}

// === TEMPERATURE STATUS ===
function updateTemperatureStatus() {
    const tempInput = document.getElementById('nhiet_do');
    const statusDiv = document.getElementById('nhiet_do_status');

    if (!tempInput || !statusDiv) return;

    const temp = parseFloat(tempInput.value);

    if (isNaN(temp)) {
        statusDiv.textContent = '';
        statusDiv.className = '';
        return;
    }

    statusDiv.className = 'px-3 py-2 rounded-lg text-sm font-semibold inline-block';

    if (temp < 36) {
        statusDiv.textContent = '❄️ Hạ nhiệt độ';
        statusDiv.classList.add('bg-blue-100', 'text-blue-800');
    } else if (temp >= 36 && temp <= 37) {
        statusDiv.textContent = '✅ Bình thường';
        statusDiv.classList.add('bg-green-100', 'text-green-800');
    } else if (temp > 37 && temp <= 38) {
        statusDiv.textContent = '⚠️ Sốt nhẹ';
        statusDiv.classList.add('bg-yellow-100', 'text-yellow-800');
    } else if (temp > 38) {
        statusDiv.textContent = '🔥 Sốt cao';
        statusDiv.classList.add('bg-red-100', 'text-red-800');
    }
}

// === COUGH TYPE TOGGLE ===
function toggleCoughType() {
    const hoCheckbox = document.getElementById('ho');
    const loaiHoGroup = document.getElementById('loai_ho_group');

    if (hoCheckbox && loaiHoGroup) {
        if (hoCheckbox.checked) {
            loaiHoGroup.style.display = 'block';
        } else {
            loaiHoGroup.style.display = 'none';
        }
    }
}

// === FORM SUBMISSION ===
function handleFormSubmit(event) {
    event.preventDefault();

    // Show loading overlay
    showLoading();

    // Collect form data
    const formData = new FormData(event.target);
    const data = {};

    formData.forEach((value, key) => {
        // Convert "on" to true for checkboxes
        if (value === "on") {
            data[key] = true;
        } else if (data[key]) {
            // Handle multiple values (checkboxes)
            if (Array.isArray(data[key])) {
                data[key].push(value);
            } else {
                data[key] = [data[key], value];
            }
        } else {
            data[key] = value;
        }
    });

    // Add unchecked checkboxes as false
    const allCheckboxes = document.querySelectorAll('input[type="checkbox"]');
    allCheckboxes.forEach(cb => {
        if (!cb.checked && cb.name && !(cb.name in data)) {
            data[cb.name] = false;
        }
    });

    console.log('[DEBUG] Sending data:', data);

    // Send to API
    fetch('/medical/api/diagnose', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
        .then(response => response.json())
        .then(result => {
            hideLoading();

            console.log('[DEBUG] Response:', result);

            if (result.ok && result.session_id) {
                // Redirect to results page
                window.location.href = `/medical/results/${result.session_id}`;
            } else {
                alert('Có lỗi xảy ra: ' + (result.error || 'Unknown error'));
            }
        })
        .catch(error => {
            hideLoading();
            console.error('Error:', error);
            alert('Không thể kết nối đến server. Vui lòng thử lại.');
        });
}

// === LOADING OVERLAY ===
function showLoading() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.style.display = 'flex';

        // Simulate progress
        setTimeout(() => {
            updateLoadingStep(1);
        }, 1000);

        setTimeout(() => {
            updateLoadingStep(2);
        }, 2500);
    }
}

function hideLoading() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.style.display = 'none';
    }
}

function updateLoadingStep(step) {
    const loadingSteps = document.querySelectorAll('#loadingOverlay .space-y-2 > div');
    loadingSteps.forEach((el, index) => {
        if (index < step) {
            el.innerHTML = el.innerHTML.replace('⏳', '✓');
            el.classList.remove('text-purple-600', 'font-medium');
            el.classList.add('text-green-600');
        } else if (index === step) {
            el.classList.add('text-purple-600', 'font-medium');
        }
    });
}

// === GRAPH TABS ===
function showGraph(graphType) {
    // Update tabs
    document.querySelectorAll('.graph-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    if (event && event.target) {
        event.target.classList.add('active');
    }

    // Update content
    document.querySelectorAll('.graph-content').forEach(content => {
        content.classList.remove('active');
    });

    const targetGraph = document.getElementById(`${graphType}-graph`);
    if (targetGraph) {
        targetGraph.classList.add('active');
    }
}

// === SHARE RESULTS ===
function shareResults() {
    if (navigator.share) {
        navigator.share({
            title: 'Kết quả Chẩn đoán - Medical AI',
            text: 'Xem kết quả chẩn đoán của tôi từ Medical AI',
            url: window.location.href
        }).catch(err => console.log('Share error:', err));
    } else {
        // Fallback: Copy to clipboard
        navigator.clipboard.writeText(window.location.href).then(() => {
            alert('Đã copy link vào clipboard!');
        });
    }
}

// === INITIALIZATION ===
document.addEventListener('DOMContentLoaded', function () {
    // Temperature monitoring
    const tempInput = document.getElementById('nhiet_do');
    if (tempInput) {
        tempInput.addEventListener('input', updateTemperatureStatus);
        updateTemperatureStatus(); // Initial check
    }

    // Cough type toggle
    const hoCheckbox = document.getElementById('ho');
    if (hoCheckbox) {
        hoCheckbox.addEventListener('change', toggleCoughType);
        toggleCoughType(); // Initial state
    }

    // Form submission
    const symptomForm = document.getElementById('symptomForm');
    if (symptomForm) {
        symptomForm.addEventListener('submit', handleFormSubmit);
    }

    // Initialize wizard progress
    if (document.querySelector('.wizard-step')) {
        updateProgress();
    }

    // Animate confidence bar on results page
    const confidenceFill = document.querySelector('.h-full.rounded-full');
    if (confidenceFill) {
        const targetWidth = confidenceFill.style.width;
        confidenceFill.style.width = '0%';
        setTimeout(() => {
            confidenceFill.style.transition = 'width 1s ease-out';
            confidenceFill.style.width = targetWidth;
        }, 500);
    }
});

// === KEYBOARD SHORTCUTS ===
document.addEventListener('keydown', function (event) {
    // Only on wizard page
    if (!document.querySelector('.wizard-step')) return;

    // Don't trigger shortcuts when typing in textarea or input
    if (event.target.matches('textarea, input[type="text"], input[type="number"]')) {
        return;
    }

    if (event.key === 'ArrowRight' || event.key === 'Enter') {
        const activeStep = document.querySelector('.wizard-step.active');
        const submitBtn = activeStep.querySelector('button[type="submit"]');

        if (!submitBtn) {
            event.preventDefault();
            nextStep();
        }
    }

    if (event.key === 'ArrowLeft') {
        event.preventDefault();
        prevStep();
    }
});

// === ERROR HANDLING ===
window.addEventListener('error', function (event) {
    console.error('Global error:', event.error);
});

window.addEventListener('unhandledrejection', function (event) {
    console.error('Unhandled promise rejection:', event.reason);
});

// === UTILITY FUNCTIONS ===
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Export functions for global use
window.nextStep = nextStep;
window.prevStep = prevStep;
window.showGraph = showGraph;
window.shareResults = shareResults;

// === FORM SUBMISSION ===
function handleFormSubmit(event) {
    event.preventDefault();

    // Show loading overlay
    showLoading();

    // Collect form data
    const formData = new FormData(event.target);
    const data = {};

    formData.forEach((value, key) => {
        // Convert "on" to true for checkboxes
        if (value === "on") {
            data[key] = true;
        } else if (data[key]) {
            // Handle multiple values (checkboxes)
            if (Array.isArray(data[key])) {
                data[key].push(value);
            } else {
                data[key] = [data[key], value];
            }
        } else {
            data[key] = value;
        }
    });

    // Add unchecked checkboxes as false
    const allCheckboxes = document.querySelectorAll('input[type="checkbox"]');
    allCheckboxes.forEach(cb => {
        if (!cb.checked && cb.name && !(cb.name in data)) {
            data[cb.name] = false;
        }
    });

    console.log('[DEBUG] Sending data:', data);

    // Send to API
    fetch('/medical/api/diagnose', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
        .then(response => response.json())
        .then(result => {
            hideLoading();

            console.log('[DEBUG] Response:', result);

            if (result.ok && result.session_id) {
                // Redirect to results page
                window.location.href = `/medical/results/${result.session_id}`;
            } else {
                alert('Có lỗi xảy ra: ' + (result.error || 'Unknown error'));
            }
        })
        .catch(error => {
            hideLoading();
            console.error('Error:', error);
            alert('Không thể kết nối đến server. Vui lòng thử lại.');
        });
}

// === LOADING OVERLAY ===
function showLoading() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.style.display = 'flex';

        // Simulate progress
        setTimeout(() => {
            updateLoadingStep(1);
        }, 1000);

        setTimeout(() => {
            updateLoadingStep(2);
        }, 2500);
    }
}

function hideLoading() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.style.display = 'none';
    }
}

function updateLoadingStep(step) {
    const steps = document.querySelectorAll('.loading-step');
    steps.forEach((el, index) => {
        if (index < step) {
            el.innerHTML = el.innerHTML.replace('⏳', '✓');
            el.classList.remove('active');
        } else if (index === step) {
            el.classList.add('active');
        }
    });
}

// === GRAPH TABS ===
function showGraph(graphType) {
    // Update tabs
    document.querySelectorAll('.graph-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    event.target.classList.add('active');

    // Update content
    document.querySelectorAll('.graph-content').forEach(content => {
        content.classList.remove('active');
    });

    const targetGraph = document.getElementById(`${graphType}-graph`);
    if (targetGraph) {
        targetGraph.classList.add('active');
    }
}

// === SHARE RESULTS ===
function shareResults() {
    if (navigator.share) {
        navigator.share({
            title: 'Kết quả Chẩn đoán - Medical AI',
            text: 'Xem kết quả chẩn đoán của tôi từ Medical AI',
            url: window.location.href
        }).catch(err => console.log('Share error:', err));
    } else {
        // Fallback: Copy to clipboard
        navigator.clipboard.writeText(window.location.href).then(() => {
            alert('Đã copy link vào clipboard!');
        });
    }
}

// === INITIALIZATION ===
document.addEventListener('DOMContentLoaded', function () {
    // Temperature monitoring
    const tempInput = document.getElementById('nhiet_do');
    if (tempInput) {
        tempInput.addEventListener('input', updateTemperatureStatus);
        updateTemperatureStatus(); // Initial check
    }

    // Cough type toggle
    const hoCheckbox = document.getElementById('ho');
    if (hoCheckbox) {
        hoCheckbox.addEventListener('change', toggleCoughType);
        toggleCoughType(); // Initial state
    }

    // Form submission
    const symptomForm = document.getElementById('symptomForm');
    if (symptomForm) {
        symptomForm.addEventListener('submit', handleFormSubmit);
    }

    // Initialize wizard progress
    if (document.querySelector('.wizard-step')) {
        updateProgress();
    }

    // Animate landing page elements
    animateLandingPage();

    // Animate result cards on load
    const resultCards = document.querySelectorAll('.result-card');
    resultCards.forEach((card, index) => {
        setTimeout(() => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(20px)';
            card.style.transition = 'all 0.5s ease';

            setTimeout(() => {
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }, 50);
        }, index * 100);
    });

    // Animate confidence bar
    const confidenceFill = document.querySelector('.confidence-fill');
    if (confidenceFill) {
        const targetWidth = confidenceFill.style.width;
        confidenceFill.style.width = '0%';
        setTimeout(() => {
            confidenceFill.style.width = targetWidth;
        }, 500);
    }

    // Add intersection observer for scroll animations
    initScrollAnimations();
});

// === LANDING PAGE ANIMATIONS ===
function animateLandingPage() {
    // Animate hero content
    const hero = document.querySelector('.hero');
    if (hero) {
        hero.style.opacity = '0';
        hero.style.transform = 'translateY(-20px)';
        setTimeout(() => {
            hero.style.transition = 'all 0.8s cubic-bezier(0.4, 0, 0.2, 1)';
            hero.style.opacity = '1';
            hero.style.transform = 'translateY(0)';
        }, 100);
    }

    // Animate feature cards
    const featureCards = document.querySelectorAll('.feature-card');
    featureCards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(30px)';
        setTimeout(() => {
            card.style.transition = 'all 0.6s cubic-bezier(0.4, 0, 0.2, 1)';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, 200 + index * 100);
    });
}

// === SCROLL ANIMATIONS ===
function initScrollAnimations() {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-in');
            }
        });
    }, {
        threshold: 0.1,
        rootMargin: '0px 0px -100px 0px'
    });

    // Observe stat items
    document.querySelectorAll('.stat-item').forEach(item => {
        observer.observe(item);
    });
}

// === KEYBOARD SHORTCUTS ===
document.addEventListener('keydown', function (event) {
    // Only on wizard page
    if (!document.querySelector('.wizard-step')) return;

    // Don't trigger shortcuts when typing in textarea or input
    if (event.target.matches('textarea, input[type="text"], input[type="number"]')) {
        return;
    }

    if (event.key === 'ArrowRight' || event.key === 'Enter') {
        const activeStep = document.querySelector('.wizard-step.active');
        const submitBtn = activeStep.querySelector('button[type="submit"]');

        if (!submitBtn) {
            event.preventDefault();
            nextStep();
        }
    }

    if (event.key === 'ArrowLeft') {
        event.preventDefault();
        prevStep();
    }
});

// === ACCESSIBILITY ENHANCEMENTS ===
// Add focus indicators for keyboard navigation
document.addEventListener('focus', function (event) {
    if (event.target.matches('input, select, textarea, button')) {
        event.target.style.outline = '3px solid var(--primary-color)';
        event.target.style.outlineOffset = '2px';
    }
}, true);

document.addEventListener('blur', function (event) {
    if (event.target.matches('input, select, textarea, button')) {
        event.target.style.outline = '';
        event.target.style.outlineOffset = '';
    }
}, true);

// === ERROR HANDLING ===
window.addEventListener('error', function (event) {
    console.error('Global error:', event.error);
});

window.addEventListener('unhandledrejection', function (event) {
    console.error('Unhandled promise rejection:', event.reason);
});

// === UTILITY FUNCTIONS ===
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// === INITIALIZE ===
document.addEventListener('DOMContentLoaded', function () {
    // Attach form submit handler
    const symptomForm = document.getElementById('symptomForm');
    if (symptomForm) {
        symptomForm.addEventListener('submit', handleFormSubmit);
    }

    // Initialize temperature status listener
    const tempInput = document.getElementById('nhiet_do');
    if (tempInput) {
        tempInput.addEventListener('input', updateTemperatureStatus);
    }

    // Initialize ho checkbox listener
    const hoCheckbox = document.getElementById('ho');
    if (hoCheckbox) {
        hoCheckbox.addEventListener('change', toggleHoType);
    }

    // Initialize progress
    updateProgress();
});

// Export functions for global use
window.nextStep = nextStep;
window.prevStep = prevStep;
window.showGraph = showGraph;
window.shareResults = shareResults;
