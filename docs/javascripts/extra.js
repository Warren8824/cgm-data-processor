document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.source-link').forEach(link => {
        const methodId = link.getAttribute('data-content');
        console.log('Looking for method:', methodId);

        // Find the method's documentation section
        const methodElement = document.querySelector(`#${methodId}`);
        if (methodElement) {
            const docSection = methodElement.closest('.doc');
            console.log('Found documentation:', docSection);
            if (docSection) {
                link.setAttribute('data-doc', docSection.innerHTML);
            }
        }
    });
});