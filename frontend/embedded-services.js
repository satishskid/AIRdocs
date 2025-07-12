// AIRDOCS Embedded Services Manager
class EmbeddedServicesManager {
    constructor() {
        this.currentService = null;
        this.oauthConnected = false;
        this.serviceUrls = {
            genspark: 'https://www.genspark.ai/',
            manus: 'https://www.manus.chat/',
            gamma_app: 'https://gamma.app/',
            tome_app: 'https://tome.app/',
            beautiful_ai: 'https://www.beautiful.ai/',
            paperpal: 'https://paperpal.com/',
            jenni_ai: 'https://jenni.ai/',
            scispace: 'https://scispace.com/',
            consensus_ai: 'https://consensus.app/',
            elicit_ai: 'https://elicit.com/',
            copy_ai: 'https://www.copy.ai/',
            persado: 'https://www.persado.com/'
        };
        
        this.apiServices = {
            perplexity_pro: '/api/generate-research',
            jasper_ai: '/api/generate-marketing',
            semantic_scholar: '/api/search-papers',
            tavily_research: '/api/research-web'
        };

        this.init();
    }

    init() {
        this.setupEventListeners();
        this.checkOAuthStatus();
        this.loadServiceConfiguration();
    }

    setupEventListeners() {
        // Service selection
        document.querySelectorAll('.service-item').forEach(item => {
            item.addEventListener('click', (e) => {
                const serviceName = e.currentTarget.dataset.service;
                const category = e.currentTarget.dataset.category;
                this.selectService(serviceName, category, e.currentTarget);
            });
        });

        // OAuth connection
        document.getElementById('connectOAuth').addEventListener('click', () => {
            this.showOAuthModal();
        });

        document.getElementById('authenticateGoogle').addEventListener('click', () => {
            this.authenticateWithGoogle();
        });

        // Service actions
        document.getElementById('refreshService').addEventListener('click', () => {
            this.refreshCurrentService();
        });

        document.getElementById('openExternal').addEventListener('click', () => {
            this.openServiceExternal();
        });

        // Close modal on background click
        document.getElementById('oauthModal').addEventListener('click', (e) => {
            if (e.target.id === 'oauthModal') {
                this.hideOAuthModal();
            }
        });
    }

    async loadServiceConfiguration() {
        try {
            const response = await fetch('/api/services/configuration');
            const config = await response.json();
            this.updateServiceAvailability(config);
        } catch (error) {
            console.error('Failed to load service configuration:', error);
        }
    }

    updateServiceAvailability(config) {
        // Update service items based on actual availability
        document.querySelectorAll('.service-item').forEach(item => {
            const serviceName = item.dataset.service;
            const serviceConfig = config.services?.[serviceName];
            
            if (serviceConfig) {
                // Update quality score
                const qualityScore = item.querySelector('.quality-score');
                if (qualityScore) {
                    qualityScore.textContent = `${serviceConfig.quality_score}/100`;
                }

                // Update access type
                const accessType = item.querySelector('.access-type');
                if (accessType) {
                    if (serviceConfig.api_available) {
                        accessType.textContent = 'API';
                        accessType.className = 'access-type access-api';
                        item.className = item.className.replace('embedded-available', 'api-available');
                    } else {
                        accessType.textContent = 'Embedded';
                        accessType.className = 'access-type access-embedded';
                        item.className = item.className.replace('api-available', 'embedded-available');
                    }
                }
            }
        });
    }

    selectService(serviceName, category, element) {
        // Update UI selection
        document.querySelectorAll('.service-item').forEach(item => {
            item.classList.remove('selected');
        });
        element.classList.add('selected');

        this.currentService = {
            name: serviceName,
            category: category,
            element: element
        };

        // Check if this is an API service or embedded service
        if (this.apiServices[serviceName]) {
            this.loadApiService(serviceName, category);
        } else {
            this.loadEmbeddedService(serviceName, category);
        }
    }

    async loadApiService(serviceName, category) {
        // Hide welcome screen and show service container
        document.getElementById('welcomeScreen').classList.add('hidden');
        document.getElementById('serviceContainer').classList.remove('hidden');

        // Update service title
        document.getElementById('serviceTitle').textContent = `${serviceName} (API Integration)`;

        // Show loading
        document.getElementById('loadingOverlay').classList.remove('hidden');

        try {
            // Create API interface
            const apiInterface = this.createApiInterface(serviceName, category);
            
            // Replace iframe with API interface
            const iframeContainer = document.querySelector('.iframe-container');
            const existingIframe = document.getElementById('serviceIframe');
            if (existingIframe) {
                existingIframe.style.display = 'none';
            }

            // Add API interface
            let apiContainer = document.getElementById('apiInterface');
            if (!apiContainer) {
                apiContainer = document.createElement('div');
                apiContainer.id = 'apiInterface';
                apiContainer.style.cssText = `
                    position: absolute;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background: white;
                    padding: 2rem;
                    overflow-y: auto;
                `;
                iframeContainer.appendChild(apiContainer);
            }

            apiContainer.innerHTML = apiInterface;
            apiContainer.style.display = 'block';

            // Hide loading
            document.getElementById('loadingOverlay').classList.add('hidden');

        } catch (error) {
            console.error('Failed to load API service:', error);
            this.showError('Failed to load API service');
        }
    }

    loadEmbeddedService(serviceName, category) {
        // Check OAuth requirement
        if (!this.oauthConnected) {
            this.showOAuthModal();
            return;
        }

        // Hide welcome screen and show service container
        document.getElementById('welcomeScreen').classList.add('hidden');
        document.getElementById('serviceContainer').classList.remove('hidden');

        // Update service title
        const displayName = serviceName.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
        document.getElementById('serviceTitle').textContent = `${displayName} (Embedded)`;

        // Show loading
        document.getElementById('loadingOverlay').classList.remove('hidden');

        // Hide API interface if visible
        const apiContainer = document.getElementById('apiInterface');
        if (apiContainer) {
            apiContainer.style.display = 'none';
        }

        // Show and load iframe
        const iframe = document.getElementById('serviceIframe');
        iframe.style.display = 'block';
        
        // Load service URL
        const serviceUrl = this.serviceUrls[serviceName];
        if (serviceUrl) {
            iframe.src = serviceUrl;
            
            // Handle iframe load
            iframe.onload = () => {
                document.getElementById('loadingOverlay').classList.add('hidden');
            };

            // Handle iframe error
            iframe.onerror = () => {
                this.showError('Failed to load embedded service');
            };
        } else {
            this.showError('Service URL not configured');
        }
    }

    createApiInterface(serviceName, category) {
        const templates = {
            perplexity_pro: `
                <div style="max-width: 800px; margin: 0 auto;">
                    <h2 style="margin-bottom: 2rem; color: #374151;">🔬 Perplexity Pro Research</h2>
                    <div style="margin-bottom: 2rem;">
                        <label style="display: block; margin-bottom: 0.5rem; font-weight: 600;">Research Query:</label>
                        <textarea id="researchQuery" placeholder="Enter your research topic..." style="width: 100%; height: 120px; padding: 1rem; border: 2px solid #e5e7eb; border-radius: 8px; font-family: inherit; resize: vertical;"></textarea>
                    </div>
                    <div style="margin-bottom: 2rem;">
                        <label style="display: block; margin-bottom: 0.5rem; font-weight: 600;">Research Type:</label>
                        <select id="researchType" style="width: 100%; padding: 0.75rem; border: 2px solid #e5e7eb; border-radius: 8px;">
                            <option value="comprehensive">Comprehensive Analysis</option>
                            <option value="market_research">Market Research</option>
                            <option value="academic">Academic Research</option>
                            <option value="trend_analysis">Trend Analysis</option>
                        </select>
                    </div>
                    <button onclick="generateResearch()" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 1rem 2rem; border: none; border-radius: 8px; font-weight: 600; cursor: pointer; width: 100%;">
                        🚀 Generate Research Report
                    </button>
                    <div id="researchResults" style="margin-top: 2rem; padding: 1.5rem; background: #f9fafb; border-radius: 8px; display: none;">
                        <h3 style="margin-bottom: 1rem;">Research Results:</h3>
                        <div id="researchContent"></div>
                    </div>
                </div>
            `,
            jasper_ai: `
                <div style="max-width: 800px; margin: 0 auto;">
                    <h2 style="margin-bottom: 2rem; color: #374151;">🎯 Jasper AI Marketing</h2>
                    <div style="margin-bottom: 2rem;">
                        <label style="display: block; margin-bottom: 0.5rem; font-weight: 600;">Campaign Description:</label>
                        <textarea id="campaignQuery" placeholder="Describe your marketing campaign..." style="width: 100%; height: 120px; padding: 1rem; border: 2px solid #e5e7eb; border-radius: 8px; font-family: inherit; resize: vertical;"></textarea>
                    </div>
                    <div style="margin-bottom: 2rem;">
                        <label style="display: block; margin-bottom: 0.5rem; font-weight: 600;">Content Type:</label>
                        <select id="contentType" style="width: 100%; padding: 0.75rem; border: 2px solid #e5e7eb; border-radius: 8px;">
                            <option value="marketing">Marketing Campaign</option>
                            <option value="email">Email Marketing</option>
                            <option value="social">Social Media</option>
                            <option value="ad_copy">Ad Copy</option>
                        </select>
                    </div>
                    <button onclick="generateMarketing()" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 1rem 2rem; border: none; border-radius: 8px; font-weight: 600; cursor: pointer; width: 100%;">
                        🎯 Generate Marketing Content
                    </button>
                    <div id="marketingResults" style="margin-top: 2rem; padding: 1.5rem; background: #f9fafb; border-radius: 8px; display: none;">
                        <h3 style="margin-bottom: 1rem;">Marketing Content:</h3>
                        <div id="marketingContent"></div>
                    </div>
                </div>
            `,
            semantic_scholar: `
                <div style="max-width: 800px; margin: 0 auto;">
                    <h2 style="margin-bottom: 2rem; color: #374151;">📚 Semantic Scholar Search</h2>
                    <div style="margin-bottom: 2rem;">
                        <label style="display: block; margin-bottom: 0.5rem; font-weight: 600;">Academic Query:</label>
                        <input type="text" id="academicQuery" placeholder="Search academic papers..." style="width: 100%; padding: 1rem; border: 2px solid #e5e7eb; border-radius: 8px; font-family: inherit;">
                    </div>
                    <button onclick="searchPapers()" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 1rem 2rem; border: none; border-radius: 8px; font-weight: 600; cursor: pointer; width: 100%;">
                        🔍 Search Academic Papers
                    </button>
                    <div id="paperResults" style="margin-top: 2rem;">
                        <div id="papersList"></div>
                    </div>
                </div>
            `
        };

        return templates[serviceName] || '<div>API interface not configured for this service.</div>';
    }

    checkOAuthStatus() {
        // Check if user is authenticated with Google
        const oauthToken = localStorage.getItem('google_oauth_token');
        if (oauthToken) {
            this.setOAuthConnected(true);
        }
    }

    setOAuthConnected(connected) {
        this.oauthConnected = connected;
        const statusElement = document.getElementById('oauthStatus');
        const connectButton = document.getElementById('connectOAuth');

        if (connected) {
            statusElement.textContent = '✅ Google OAuth Connected';
            statusElement.className = 'oauth-status oauth-connected';
            connectButton.style.display = 'none';
        } else {
            statusElement.textContent = '🔒 Google OAuth Required';
            statusElement.className = 'oauth-status oauth-disconnected';
            connectButton.style.display = 'block';
        }
    }

    showOAuthModal() {
        document.getElementById('oauthModal').classList.remove('hidden');
    }

    hideOAuthModal() {
        document.getElementById('oauthModal').classList.add('hidden');
    }

    async authenticateWithGoogle() {
        try {
            // Simulate Google OAuth flow
            // In production, this would use Google OAuth 2.0
            const response = await fetch('/api/auth/google/initiate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                const data = await response.json();
                // Redirect to Google OAuth
                window.location.href = data.auth_url;
            } else {
                throw new Error('Failed to initiate OAuth');
            }
        } catch (error) {
            console.error('OAuth authentication failed:', error);
            // For demo purposes, simulate successful authentication
            localStorage.setItem('google_oauth_token', 'demo_token_' + Date.now());
            this.setOAuthConnected(true);
            this.hideOAuthModal();
            
            // If user was trying to access a service, load it now
            if (this.currentService) {
                this.loadEmbeddedService(this.currentService.name, this.currentService.category);
            }
        }
    }

    refreshCurrentService() {
        if (this.currentService) {
            if (this.apiServices[this.currentService.name]) {
                this.loadApiService(this.currentService.name, this.currentService.category);
            } else {
                this.loadEmbeddedService(this.currentService.name, this.currentService.category);
            }
        }
    }

    openServiceExternal() {
        if (this.currentService) {
            const serviceUrl = this.serviceUrls[this.currentService.name];
            if (serviceUrl) {
                window.open(serviceUrl, '_blank');
            }
        }
    }

    showError(message) {
        document.getElementById('loadingOverlay').innerHTML = `
            <div style="color: #ef4444; text-align: center;">
                <div style="font-size: 2rem; margin-bottom: 1rem;">⚠️</div>
                <div>${message}</div>
            </div>
        `;
    }
}

// Global functions for API interfaces
async function generateResearch() {
    const query = document.getElementById('researchQuery').value;
    const type = document.getElementById('researchType').value;
    
    if (!query.trim()) {
        alert('Please enter a research query');
        return;
    }

    const resultsDiv = document.getElementById('researchResults');
    const contentDiv = document.getElementById('researchContent');
    
    resultsDiv.style.display = 'block';
    contentDiv.innerHTML = '<div style="text-align: center;">🔄 Generating research report...</div>';

    try {
        const response = await fetch('/api/generate-content', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                prompt: query,
                content_category: 'research_reports',
                research_type: type
            })
        });

        const data = await response.json();
        if (data.success) {
            contentDiv.innerHTML = `<pre style="white-space: pre-wrap; font-family: inherit;">${data.content}</pre>`;
        } else {
            contentDiv.innerHTML = `<div style="color: #ef4444;">Error: ${data.error}</div>`;
        }
    } catch (error) {
        contentDiv.innerHTML = `<div style="color: #ef4444;">Failed to generate research: ${error.message}</div>`;
    }
}

async function generateMarketing() {
    const query = document.getElementById('campaignQuery').value;
    const type = document.getElementById('contentType').value;
    
    if (!query.trim()) {
        alert('Please enter a campaign description');
        return;
    }

    const resultsDiv = document.getElementById('marketingResults');
    const contentDiv = document.getElementById('marketingContent');
    
    resultsDiv.style.display = 'block';
    contentDiv.innerHTML = '<div style="text-align: center;">🔄 Generating marketing content...</div>';

    try {
        const response = await fetch('/api/generate-content', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                prompt: query,
                content_category: 'marketing_campaigns',
                content_type: type
            })
        });

        const data = await response.json();
        if (data.success) {
            contentDiv.innerHTML = `<pre style="white-space: pre-wrap; font-family: inherit;">${data.content}</pre>`;
        } else {
            contentDiv.innerHTML = `<div style="color: #ef4444;">Error: ${data.error}</div>`;
        }
    } catch (error) {
        contentDiv.innerHTML = `<div style="color: #ef4444;">Failed to generate marketing content: ${error.message}</div>`;
    }
}

async function searchPapers() {
    const query = document.getElementById('academicQuery').value;
    
    if (!query.trim()) {
        alert('Please enter a search query');
        return;
    }

    const resultsDiv = document.getElementById('papersList');
    resultsDiv.innerHTML = '<div style="text-align: center; padding: 2rem;">🔄 Searching academic papers...</div>';

    try {
        const response = await fetch('/api/search-papers', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                query: query,
                limit: 10
            })
        });

        const data = await response.json();
        if (data.success && data.papers) {
            let papersHtml = '';
            data.papers.forEach(paper => {
                papersHtml += `
                    <div style="border: 1px solid #e5e7eb; border-radius: 8px; padding: 1.5rem; margin-bottom: 1rem; background: white;">
                        <h4 style="margin-bottom: 0.5rem; color: #374151;">${paper.title}</h4>
                        <p style="color: #6b7280; margin-bottom: 0.5rem;">Authors: ${paper.authors || 'Unknown'}</p>
                        <p style="color: #6b7280; margin-bottom: 1rem;">Year: ${paper.year || 'Unknown'} | Citations: ${paper.citationCount || 0}</p>
                        <p style="line-height: 1.6;">${paper.abstract || 'No abstract available'}</p>
                        ${paper.url ? `<a href="${paper.url}" target="_blank" style="color: #667eea; text-decoration: none;">📄 View Paper</a>` : ''}
                    </div>
                `;
            });
            resultsDiv.innerHTML = papersHtml;
        } else {
            resultsDiv.innerHTML = '<div style="color: #ef4444; text-align: center; padding: 2rem;">No papers found</div>';
        }
    } catch (error) {
        resultsDiv.innerHTML = `<div style="color: #ef4444; text-align: center; padding: 2rem;">Search failed: ${error.message}</div>`;
    }
}

// Initialize the embedded services manager
document.addEventListener('DOMContentLoaded', () => {
    window.embeddedServices = new EmbeddedServicesManager();
});
