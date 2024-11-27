// Allowed UTM content identifiers
const allowedUTMValues = ["referral", "partner"];

// Function to validate the UTM content parameter
function isValidUTMContent(value) {
    return allowedUTMValues.includes(value);
}

// Function to get query parameters
function getQueryParam(param) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(param);
}

// Main function to check and sanitize UTM content
function checkUTMContent() {
    const utmContent = getQueryParam('utm_content');
    
    // Log warning if UTM content is invalid
    if (!utmContent || !isValidUTMContent(utmContent)) {
        console.warn('Invalid UTM content detected, ignoring parameter.');
        return;
    }

    // Proceed with validated UTM content
    console.log('Valid UTM content:', utmContent);
}

// Run the check on page load
document.addEventListener("DOMContentLoaded", checkUTMContent);
