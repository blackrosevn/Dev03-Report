// Vinatex Report Portal - Internationalization

// Current language
let currentLanguage = 'vi';

// Translations storage
let translations = {};

// Load language file
async function loadLanguage(lang) {
    try {
        currentLanguage = lang || 'vi';
        
        // Fetch the language file
        const response = await fetch(`/static/translations/${currentLanguage}.json`);
        if (!response.ok) {
            throw new Error(`Failed to load language file: ${response.status}`);
        }
        
        translations = await response.json();
        
        // Apply translations to the page
        applyTranslations();
        
        // Store the language preference
        localStorage.setItem('language', currentLanguage);
        
        return true;
    } catch (error) {
        console.error('Error loading language:', error);
        return false;
    }
}

// Apply translations to the current page
function applyTranslations() {
    // Get all elements with data-i18n attribute
    const elements = document.querySelectorAll('[data-i18n]');
    
    elements.forEach(element => {
        const key = element.getAttribute('data-i18n');
        const translation = getTranslation(key);
        
        if (translation) {
            // Check if the element is an input with placeholder
            if (element.hasAttribute('placeholder')) {
                element.setAttribute('placeholder', translation);
            }
            // For normal elements, set the text content
            else {
                element.textContent = translation;
            }
            
            // Store the translation as a hidden element for reference by JavaScript
            if (!document.getElementById(key)) {
                const hiddenElement = document.createElement('span');
                hiddenElement.id = key;
                hiddenElement.style.display = 'none';
                hiddenElement.textContent = translation;
                document.body.appendChild(hiddenElement);
            } else {
                document.getElementById(key).textContent = translation;
            }
        }
    });
    
    // Handle elements with placeholder translations
    const placeholderElements = document.querySelectorAll('[data-i18n-placeholder]');
    placeholderElements.forEach(element => {
        const key = element.getAttribute('data-i18n-placeholder');
        const translation = getTranslation(key);
        
        if (translation) {
            element.setAttribute('placeholder', translation);
        }
    });
}

// Get a translation by key
function getTranslation(key) {
    // Split the key by dots to traverse the nested structure
    const keys = key.split('.');
    let value = translations;
    
    for (const k of keys) {
        if (value && typeof value === 'object' && k in value) {
            value = value[k];
        } else {
            return null;
        }
    }
    
    return value;
}

// Translate a specific text
function translate(key, defaultText) {
    const translation = getTranslation(key);
    return translation || defaultText || key;
}

// Switch language
function switchLanguage(lang) {
    if (lang && lang !== currentLanguage) {
        loadLanguage(lang);
    }
}

// Initialize on document load
document.addEventListener('DOMContentLoaded', function() {
    // Try to load language from local storage or use default
    const savedLanguage = localStorage.getItem('language') || document.documentElement.lang || 'vi';
    loadLanguage(savedLanguage);
    
    // Set up language selector if present
    const languageSelector = document.querySelector('select[name="language"]');
    if (languageSelector) {
        languageSelector.value = savedLanguage;
        languageSelector.addEventListener('change', function() {
            switchLanguage(this.value);
        });
    }
});
