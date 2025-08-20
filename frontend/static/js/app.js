/**
 * SEC Filings QA Agent - Frontend JavaScript
 * Handles all user interactions, API calls, and UI updates
 */

// Configuration
const CONFIG = {
    API_BASE_URL: window.location.origin + '/api/v1',
    MAX_RETRIES: 3,
    RETRY_DELAY: 1000,
    TYPING_DELAY: 50
};

// Global state
let isLoading = false;
let currentRequestId = null;

/**
 * Initialize the application when DOM is loaded
 */
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

/**
 * Main initialization function
 */
function initializeApp() {
    console.log('🚀 Initializing SEC Filings QA Agent');
    
    // Initialize theme
    initializeTheme();
    
    // Setup event listeners
    setupEventListeners();
    
    // Load initial data
    loadSystemStats();
    
    // Setup auto-refresh for stats
    setInterval(loadSystemStats, 60000); // Refresh every minute
    
    console.log('✅ App initialized successfully');
}

/**
 * Initialize theme management
 */
function initializeTheme() {
    const themeToggle = document.getElementById('theme-toggle');
    const body = document.body;
    
    // Load saved theme or default to light
    const savedTheme = localStorage.getItem('theme') || 'light';
    setTheme(savedTheme);
    
    // Theme toggle event listener
    themeToggle.addEventListener('click', function() {
        const currentTheme = body.classList.contains('dark-theme') ? 'dark' : 'light';
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        setTheme(newTheme);
        localStorage.setItem('theme', newTheme);
        
        // Add animation effect
        themeToggle.style.transform = 'rotate(180deg)';
        setTimeout(() => {
            themeToggle.style.transform = '';
        }, 300);
    });
}

/**
 * Set theme and update UI
 */
function setTheme(theme) {
    const body = document.body;
    const themeToggle = document.getElementById('theme-toggle');
    const icon = themeToggle.querySelector('i');
    
    if (theme === 'dark') {
        body.classList.add('dark-theme');
        body.classList.remove('light-theme');
        icon.className = 'fas fa-sun';
        themeToggle.title = 'Switch to Light Theme';
    } else {
        body.classList.add('light-theme');
        body.classList.remove('dark-theme');
        icon.className = 'fas fa-moon';
        themeToggle.title = 'Switch to Dark Theme';
    }
}

/**
 * Setup all event listeners
 */
function setupEventListeners() {
    // Question form
    const questionForm = document.getElementById('question-form');
    const questionTextarea = document.getElementById('question');
    const charCount = document.getElementById('char-count');
    
    // Character counter
    questionTextarea.addEventListener('input', function() {
        const count = this.value.length;
        charCount.textContent = count;
        
        // Color coding for character count
        if (count > 900) {
            charCount.style.color = 'var(--danger-color)';
        } else if (count > 750) {
            charCount.style.color = 'var(--warning-color)';
        } else {
            charCount.style.color = 'var(--text-muted)';
        }
    });
    
    // Question form submission
    questionForm.addEventListener('submit', handleQuestionSubmit);
    
    // Process form
    const processForm = document.getElementById('process-form');
    processForm.addEventListener('submit', handleProcessSubmit);
    
    // Example cards
    const exampleCards = document.querySelectorAll('.example-card');
    exampleCards.forEach(card => {
        card.addEventListener('click', function() {
            const question = this.dataset.question;
            const ticker = this.dataset.ticker;
            const filing = this.dataset.filing;
            
            // Fill form with example data
            document.getElementById('question').value = question;
            document.getElementById('ticker').value = ticker;
            document.getElementById('filing-type').value = filing;
            
            // Update character count
            const event = new Event('input');
            document.getElementById('question').dispatchEvent(event);
            
            // Scroll to form and focus
            document.getElementById('question').scrollIntoView({ behavior: 'smooth' });
            setTimeout(() => {
                document.getElementById('question').focus();
            }, 500);
            
            // Add visual feedback
            this.style.transform = 'scale(0.95)';
            setTimeout(() => {
                this.style.transform = '';
            }, 150);
        });
    });
    
    // Retry button
    const retryBtn = document.getElementById('retry-btn');
    retryBtn.addEventListener('click', function() {
        hideError();
        // Re-submit the last form if available
        const lastForm = document.querySelector('form:last-submitted');
        if (lastForm) {
            lastForm.dispatchEvent(new Event('submit'));
        }
    });
    
    // Footer links
    document.getElementById('health-check').addEventListener('click', function(e) {
        e.preventDefault();
        performHealthCheck();
    });
    
    document.getElementById('system-status').addEventListener('click', function(e) {
        e.preventDefault();
        showSystemStatus();
    });
}

/**
 * Handle question form submission
 */
async function handleQuestionSubmit(e) {
    e.preventDefault();
    
    if (isLoading) return;
    
    const formData = new FormData(e.target);
    const question = formData.get('question').trim();
    const ticker = formData.get('ticker').trim().toUpperCase();
    const filingType = formData.get('filing_type');
    const k = parseInt(formData.get('k'));
    
    // Validation
    if (!question) {
        showError('Please enter a question');
        return;
    }
    
    if (question.length > 1000) {
        showError('Question is too long (maximum 1000 characters)');
        return;
    }
    
    if (ticker && ticker.length > 10) {
        showError('Invalid ticker symbol');
        return;
    }
    
    // Mark form as last submitted
    e.target.classList.add('last-submitted');
    document.querySelectorAll('form').forEach(f => {
        if (f !== e.target) f.classList.remove('last-submitted');
    });
    
    // Prepare request data
    const requestData = {
        question: question,
        k: k
    };
    
    if (ticker) requestData.ticker = ticker;
    if (filingType) requestData.filing_type = filingType;
    
    // Submit question
    await submitQuestion(requestData);
}

/**
 * Handle process filings form submission
 */
async function handleProcessSubmit(e) {
    e.preventDefault();
    
    if (isLoading) return;
    
    const formData = new FormData(e.target);
    const ticker = formData.get('ticker').trim().toUpperCase();
    const filingType = formData.get('filing_type');
    const limit = parseInt(formData.get('limit'));
    
    // Validation
    if (!ticker) {
        showError('Please enter a ticker symbol');
        return;
    }
    
    if (ticker.length > 10) {
        showError('Invalid ticker symbol');
        return;
    }
    
    // Prepare request data
    const requestData = {
        filing_type: filingType,
        limit: limit
    };
    
    // Submit processing request
    await processFilings(ticker, requestData);
}

/**
 * Submit question to API
 */
async function submitQuestion(requestData) {
    showLoading('Analyzing SEC filings...');
    hideResults();
    hideError();
    
    currentRequestId = generateRequestId();
    const requestId = currentRequestId;
    
    try {
        console.log('📤 Submitting question:', requestData.question.substring(0, 100) + '...');
        
        const response = await fetchWithRetry('/questions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        });
        
        // Check if this is still the current request
        if (requestId !== currentRequestId) {
            console.log('🚫 Request cancelled (newer request in progress)');
            return;
        }
        
        if (response.success) {
            console.log('✅ Question answered successfully');
            showResults(response.data);
        } else {
            throw new Error(response.error || 'Failed to get answer');
        }
        
    } catch (error) {
        console.error('❌ Error submitting question:', error);
        if (requestId === currentRequestId) {
            showError(`Failed to get answer: ${error.message}`);
        }
    } finally {
        if (requestId === currentRequestId) {
            hideLoading();
        }
    }
}

/**
 * Process filings for a company
 */
async function processFilings(ticker, requestData) {
    showLoading(`Processing ${requestData.filing_type} filings for ${ticker}...`, 'This may take several minutes');
    hideError();
    
    const resultsContainer = document.getElementById('process-results');
    resultsContainer.style.display = 'none';
    
    try {
        console.log(`📤 Processing filings for ${ticker}:`, requestData);
        
        const response = await fetchWithRetry(`/companies/${ticker}/process`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        });
        
        if (response.success) {
            console.log('✅ Filings processed successfully');
            showProcessResults(response.data);
            
            // Refresh system stats
            setTimeout(() => {
                loadSystemStats();
            }, 1000);
        } else {
            throw new Error(response.error || 'Failed to process filings');
        }
        
    } catch (error) {
        console.error('❌ Error processing filings:', error);
        showError(`Failed to process filings: ${error.message}`);
    } finally {
        hideLoading();
    }
}

/**
 * Load system statistics
 */
async function loadSystemStats() {
    try {
        const response = await fetchWithRetry('/status');
        
        if (response.success) {
            updateStatsDisplay(response.data);
        } else {
            console.warn('Failed to load system stats:', response.error);
        }
        
    } catch (error) {
        console.warn('Error loading system stats:', error);
    }
}

/**
 * Update statistics display
 */
function updateStatsDisplay(data) {
    const database = data.database || {};
    const vectorDb = data.vector_database || {};
    
    // Update stat cards
    updateStatCard('companies-count', database.companies || 0);
    updateStatCard('filings-count', database.filings || 0);
    updateStatCard('vectors-count', formatNumber(vectorDb.total_vectors || 0));
    updateStatCard('last-updated', formatTimestamp(data.timestamp));
}

/**
 * Update individual stat card
 */
function updateStatCard(elementId, value) {
    const element = document.getElementById(elementId);
    if (element && element.textContent !== value.toString()) {
        element.style.transform = 'scale(1.1)';
        element.textContent = value;
        setTimeout(() => {
            element.style.transform = '';
        }, 200);
    }
}

/**
 * Show loading state
 */
function showLoading(message = 'Loading...', subtext = 'Please wait') {
    isLoading = true;
    hideResults();
    hideError();
    
    const loadingSection = document.getElementById('loading-section');
    const loadingText = document.querySelector('.loading-text');
    const loadingSubtext = document.querySelector('.loading-subtext');
    
    loadingText.textContent = message;
    loadingSubtext.textContent = subtext;
    loadingSection.style.display = 'block';
    loadingSection.classList.add('fade-in');
    
    // Disable form buttons
    document.querySelectorAll('button[type="submit"]').forEach(btn => {
        btn.disabled = true;
        const span = btn.querySelector('span');
        if (span) {
            span.textContent = 'Processing...';
        }
    });
}

/**
 * Hide loading state
 */
function hideLoading() {
    isLoading = false;
    
    const loadingSection = document.getElementById('loading-section');
    loadingSection.style.display = 'none';
    
    // Re-enable form buttons
    document.querySelectorAll('button[type="submit"]').forEach(btn => {
        btn.disabled = false;
        const span = btn.querySelector('span');
        if (span) {
            if (btn.id === 'submit-btn') {
                span.textContent = 'Ask Question';
            } else if (btn.id === 'process-btn') {
                span.textContent = 'Process Filings';
            }
        }
    });
}

/**
 * Show results
 */
/**
 * Convert markdown to HTML for better display
 */
function formatMarkdownToHTML(text) {
    if (!text) return 'No answer available';
    
    let formatted = text;
    
    // Convert headers
    formatted = formatted.replace(/^## (.+)$/gm, '<h2 class="answer-heading">$1</h2>');
    formatted = formatted.replace(/^### (.+)$/gm, '<h3 class="answer-subheading">$1</h3>');
    
    // Convert bold text
    formatted = formatted.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    
    // Convert bullet points
    formatted = formatted.replace(/^- (.+)$/gm, '<li>$1</li>');
    
    // Wrap consecutive list items in ul tags
    formatted = formatted.replace(/(<li>.*<\/li>)/gs, function(match) {
        return '<ul class="answer-list">' + match + '</ul>';
    });
    
    // Convert line breaks to paragraphs
    const paragraphs = formatted.split('\n\n').filter(p => p.trim());
    formatted = paragraphs.map(p => {
        if (p.includes('<h2>') || p.includes('<h3>') || p.includes('<ul>')) {
            return p;
        }
        return `<p class="answer-paragraph">${p.trim()}</p>`;
    }).join('');
    
    // Fix any double ul tags
    formatted = formatted.replace(/<\/ul>\s*<ul[^>]*>/g, '');
    
    return formatted;
}

function showResults(data) {
    const resultsSection = document.getElementById('results-section');
    const answerContent = document.getElementById('answer-content');
    const sourcesList = document.getElementById('sources-list');
    const resultsMeta = document.getElementById('results-meta');
    
    // Update metadata
    const filters = data.filters_applied || {};
    let metaText = `Retrieved ${filters.chunks_retrieved || 0} relevant documents`;
    if (filters.ticker) metaText += ` for ${filters.ticker}`;
    if (filters.filing_type) metaText += ` (${filters.filing_type})`;
    resultsMeta.textContent = metaText;
    
    // Format and show answer
    answerContent.innerHTML = '';
    const formattedAnswer = formatMarkdownToHTML(data.answer || 'No answer available');
    
    // Show formatted answer with typing effect for the first paragraph only
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = formattedAnswer;
    const firstElement = tempDiv.firstElementChild;
    
    if (firstElement) {
        // Type the first paragraph/heading
        typeText(answerContent, firstElement.textContent || firstElement.innerText);
        
        // Then show the rest formatted
        setTimeout(() => {
            answerContent.innerHTML = formattedAnswer;
        }, Math.min(2000, (firstElement.textContent || firstElement.innerText).length * 30));
    } else {
        answerContent.innerHTML = formattedAnswer;
    }
    
    // Show sources
    sourcesList.innerHTML = '';
    if (data.sources && data.sources.length > 0) {
        data.sources.forEach((source, index) => {
            setTimeout(() => {
                const sourceElement = createSourceElement(source, index);
                sourcesList.appendChild(sourceElement);
                sourceElement.classList.add('slide-up');
            }, 1000 + (index * 200));
        });
    } else {
        sourcesList.innerHTML = '<p style="color: var(--text-muted); font-style: italic;">No sources available</p>';
    }
    
    // Show results section
    resultsSection.style.display = 'block';
    resultsSection.classList.add('fade-in');
    
    // Scroll to results
    setTimeout(() => {
        resultsSection.scrollIntoView({ behavior: 'smooth' });
    }, 500);
}

/**
 * Create source element
 */
function createSourceElement(source, index) {
    const sourceDiv = document.createElement('div');
    sourceDiv.className = 'source-item';
    
    const confidence = source.confidence || source.score || 0;
    const confidencePercent = Math.round(confidence * 100);
    
    sourceDiv.innerHTML = `
        <div class="source-header">
            <div class="source-title">
                ${source.ticker || 'Unknown'} - ${source.filing_type || 'Unknown'} 
                (${source.filing_date ? new Date(source.filing_date).toLocaleDateString() : 'Unknown Date'})
                ${source.section_name ? ' - ' + source.section_name : ''}
            </div>
            <div class="source-score">${confidencePercent}% match</div>
        </div>
        <div class="source-excerpt">${source.text ? source.text.substring(0, 300) + '...' : 'No excerpt available'}</div>
    `;
    
    return sourceDiv;
}

/**
 * Show process results
 */
function showProcessResults(data) {
    const resultsContainer = document.getElementById('process-results');
    
    const successCount = data.filings_processed || 0;
    const totalCount = data.filings_found || 0;
    const chunksCount = data.total_chunks_created || 0;
    
    resultsContainer.innerHTML = `
        <div style="margin-bottom: 1rem;">
            <h4 style="color: var(--success-color); margin-bottom: 0.5rem;">
                <i class="fas fa-check-circle"></i> Processing Complete
            </h4>
            <p style="color: var(--text-secondary); margin-bottom: 1rem;">
                Successfully processed ${successCount} of ${totalCount} filings for ${data.ticker},
                creating ${chunksCount} searchable document chunks.
            </p>
        </div>
        
        ${data.processed_filings && data.processed_filings.length > 0 ? `
            <div>
                <h5 style="margin-bottom: 0.5rem;">Processed Filings:</h5>
                <ul style="margin: 0; padding-left: 1.5rem;">
                    ${data.processed_filings.map(filing => `
                        <li style="margin-bottom: 0.25rem; color: var(--text-secondary);">
                            ${filing.accession_number} - ${filing.num_chunks} chunks
                        </li>
                    `).join('')}
                </ul>
            </div>
        ` : ''}
    `;
    
    resultsContainer.style.display = 'block';
    resultsContainer.classList.add('slide-up');
}

/**
 * Hide results
 */
function hideResults() {
    const resultsSection = document.getElementById('results-section');
    resultsSection.style.display = 'none';
}

/**
 * Show error message
 */
function showError(message) {
    hideLoading();
    hideResults();
    
    const errorSection = document.getElementById('error-section');
    const errorMessage = document.getElementById('error-message');
    
    errorMessage.textContent = message;
    errorSection.style.display = 'block';
    errorSection.classList.add('fade-in');
}

/**
 * Hide error message
 */
function hideError() {
    const errorSection = document.getElementById('error-section');
    errorSection.style.display = 'none';
}

/**
 * Perform health check
 */
async function performHealthCheck() {
    try {
        showLoading('Checking system health...');
        
        const response = await fetchWithRetry('/health');
        
        if (response.success) {
            const data = response.data;
            alert(`✅ System Health Check Passed\\n\\nDatabase: ${data.database?.status || 'Unknown'}\\nVector DB: ${data.vector_database?.status || 'Unknown'}\\nServices: All operational`);
        } else {
            throw new Error(response.error || 'Health check failed');
        }
        
    } catch (error) {
        alert(`❌ Health Check Failed\\n\\n${error.message}`);
    } finally {
        hideLoading();
    }
}

/**
 * Show system status in modal-like display
 */
async function showSystemStatus() {
    try {
        showLoading('Loading system status...');
        
        const response = await fetchWithRetry('/status');
        
        if (response.success) {
            const data = response.data;
            const statusText = `
🖥️ SYSTEM STATUS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Database Statistics:
  • Companies: ${data.database?.companies || 0}
  • Filings: ${data.database?.filings || 0}
  • Document Chunks: ${data.database?.chunks || 0}

🔍 Vector Database:
  • Total Vectors: ${formatNumber(data.vector_database?.total_vectors || 0)}
  • Index Size: ${data.vector_database?.index_size || 'Unknown'}
  • Embedding Model: ${data.vector_database?.model || 'Unknown'}

⚙️ Services:
  • Status: ${data.services_initialized ? '✅ Operational' : '❌ Error'}
  • Last Updated: ${formatTimestamp(data.timestamp)}

🔧 Document Processor:
  • Total Processed: ${data.document_processor?.total_processed || 0}
  • Success Rate: ${data.document_processor?.success_rate || 'Unknown'}
            `.trim();
            
            alert(statusText);
        } else {
            throw new Error(response.error || 'Failed to get system status');
        }
        
    } catch (error) {
        alert(`❌ Failed to Load System Status\\n\\n${error.message}`);
    } finally {
        hideLoading();
    }
}

/**
 * Fetch with retry logic
 */
async function fetchWithRetry(endpoint, options = {}, retries = CONFIG.MAX_RETRIES) {
    const url = CONFIG.API_BASE_URL + endpoint;
    
    for (let i = 0; i <= retries; i++) {
        try {
            const response = await fetch(url, {
                ...options,
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            return data;
            
        } catch (error) {
            console.warn(`Attempt ${i + 1} failed:`, error.message);
            
            if (i === retries) {
                throw error;
            }
            
            // Wait before retrying
            await new Promise(resolve => setTimeout(resolve, CONFIG.RETRY_DELAY * (i + 1)));
        }
    }
}

/**
 * Type text with animation effect
 */
function typeText(element, text, delay = CONFIG.TYPING_DELAY) {
    element.innerHTML = '';
    let index = 0;
    
    function type() {
        if (index < text.length) {
            element.innerHTML += text.charAt(index);
            index++;
            setTimeout(type, delay);
        }
    }
    
    type();
}

/**
 * Generate unique request ID
 */
function generateRequestId() {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
}

/**
 * Format large numbers with appropriate units
 */
function formatNumber(num) {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
}

/**
 * Format timestamp for display
 */
function formatTimestamp(timestamp) {
    if (!timestamp) return 'Unknown';
    
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`;
    return date.toLocaleDateString();
}

// Export for testing purposes
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        formatNumber,
        formatTimestamp,
        generateRequestId
    };
}
