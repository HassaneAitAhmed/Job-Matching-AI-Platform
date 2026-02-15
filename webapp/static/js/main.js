// Main JavaScript for Job Matching AI Platform

// Global state
let currentSection = null;

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Job Matching AI Platform initialized');
    
    // Load statistics
    loadStats();
    
    // Load form options
    loadCities();
    loadSectors();
    
    // Set up form handlers
    setupFormHandlers();
    
    // Set up navigation
    setupNavigation();
});

// Load statistics from API
async function loadStats() {
    try {
        const response = await fetch('/api/stats');
        const stats = await response.json();
        
        document.getElementById('total-jobs').textContent = stats.total_jobs.toLocaleString();
        document.getElementById('total-seekers').textContent = stats.total_seekers.toLocaleString();
        document.getElementById('total-sectors').textContent = stats.sectors;
        document.getElementById('total-cities').textContent = stats.cities;
    } catch (error) {
        console.error('Error loading stats:', error);
        document.getElementById('total-jobs').textContent = 'N/A';
        document.getElementById('total-seekers').textContent = 'N/A';
        document.getElementById('total-sectors').textContent = 'N/A';
        document.getElementById('total-cities').textContent = 'N/A';
    }
}

// Load cities for dropdowns
async function loadCities() {
    try {
        const response = await fetch('/api/cities');
        const cities = await response.json();
        
        const seekerCity = document.getElementById('seeker-city');
        const jobCity = document.getElementById('job-city');
        
        cities.forEach(city => {
            const option1 = document.createElement('option');
            option1.value = city;
            option1.textContent = city;
            seekerCity.appendChild(option1);
            
            const option2 = document.createElement('option');
            option2.value = city;
            option2.textContent = city;
            jobCity.appendChild(option2);
        });
    } catch (error) {
        console.error('Error loading cities:', error);
    }
}

// Load sectors for dropdowns
async function loadSectors() {
    try {
        const response = await fetch('/api/sectors');
        const sectors = await response.json();
        
        const seekerSector = document.getElementById('seeker-sector');
        const jobSector = document.getElementById('job-sector');
        
        sectors.forEach(sector => {
            const option1 = document.createElement('option');
            option1.value = sector;
            option1.textContent = sector;
            seekerSector.appendChild(option1);
            
            const option2 = document.createElement('option');
            option2.value = sector;
            option2.textContent = sector;
            jobSector.appendChild(option2);
        });
    } catch (error) {
        console.error('Error loading sectors:', error);
    }
}

// Set up form submission handlers
function setupFormHandlers() {
    // Job Seeker Form
    document.getElementById('seekerForm').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = {
            skills: document.getElementById('seeker-skills').value,
            experience: parseInt(document.getElementById('seeker-experience').value),
            education: parseInt(document.getElementById('seeker-education').value),
            city: document.getElementById('seeker-city').value,
            sector: document.getElementById('seeker-sector').value,
            contract_type: document.getElementById('seeker-contract').value,
            salary: parseInt(document.getElementById('seeker-salary').value)
        };
        
        await searchJobs(formData);
    });
    
    // Employer Form
    document.getElementById('employerForm').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = {
            skills: document.getElementById('job-skills').value,
            experience_min: parseInt(document.getElementById('job-experience-min').value),
            experience_max: parseInt(document.getElementById('job-experience-max').value),
            education: parseInt(document.getElementById('job-education').value),
            city: document.getElementById('job-city').value,
            sector: document.getElementById('job-sector').value,
            contract_type: document.getElementById('job-contract').value,
            salary: parseInt(document.getElementById('job-salary').value)
        };
        
        await searchCandidates(formData);
    });
}

// Search for jobs matching a seeker
async function searchJobs(seekerData) {
    showLoading();
    
    try {
        const response = await fetch('/api/match/seeker-to-jobs', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(seekerData)
        });
        
        const data = await response.json();
        
        if (data.matches && data.matches.length > 0) {
            displayJobResults(data);
        } else {
            displayNoResults('jobs');
        }
    } catch (error) {
        console.error('Error searching jobs:', error);
        alert('Error searching for jobs. Please try again.');
    } finally {
        hideLoading();
    }
}

// Search for candidates matching a job
async function searchCandidates(jobData) {
    showLoading();
    
    try {
        const response = await fetch('/api/match/job-to-seekers', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(jobData)
        });
        
        const data = await response.json();
        
        if (data.matches && data.matches.length > 0) {
            displayCandidateResults(data);
        } else {
            displayNoResults('candidates');
        }
    } catch (error) {
        console.error('Error searching candidates:', error);
        alert('Error searching for candidates. Please try again.');
    } finally {
        hideLoading();
    }
}

// Display job results
function displayJobResults(data) {
    const resultsTitle = document.getElementById('results-title');
    const resultsSummary = document.getElementById('results-summary');
    const resultsList = document.getElementById('results-list');
    
    resultsTitle.innerHTML = '<i class="fas fa-briefcase"></i> Top Job Matches';
    resultsSummary.textContent = `Found ${data.total_found} matches. Showing top ${data.matches.length} results using ${data.algorithm}.`;
    
    resultsList.innerHTML = '';
    
    data.matches.forEach((job, index) => {
        const card = document.createElement('div');
        card.className = 'result-card';
        
        // Format skills - handle both string and array
        let skillsDisplay = job.skills;
        if (typeof skillsDisplay === 'string' && skillsDisplay.startsWith('[')) {
            try {
                skillsDisplay = JSON.parse(skillsDisplay.replace(/'/g, '"')).join(', ');
            } catch (e) {
                // Keep as is if parsing fails
            }
        }
        
        card.innerHTML = `
            <div class="result-header">
                <div class="result-title">
                    <h3>${index + 1}. ${job.title}</h3>
                    <p>${job.company}</p>
                </div>
                <div class="match-score">${job.match_score}%</div>
            </div>
            <div class="result-details">
                <div class="detail-item">
                    <i class="fas fa-industry"></i>
                    <span><strong>Sector:</strong> ${job.sector}</span>
                </div>
                <div class="detail-item">
                    <i class="fas fa-map-marker-alt"></i>
                    <span><strong>Location:</strong> ${job.location}</span>
                </div>
                <div class="detail-item">
                    <i class="fas fa-file-contract"></i>
                    <span><strong>Contract:</strong> ${job.contract_type}</span>
                </div>
                <div class="detail-item">
                    <i class="fas fa-money-bill-wave"></i>
                    <span><strong>Salary:</strong> ${job.salary.toLocaleString()} DZD</span>
                </div>
                <div class="detail-item">
                    <i class="fas fa-briefcase"></i>
                    <span><strong>Experience:</strong> ${job.experience_required}</span>
                </div>
                <div class="detail-item" style="grid-column: 1 / -1;">
                    <i class="fas fa-code"></i>
                    <span><strong>Skills:</strong> ${skillsDisplay}</span>
                </div>
            </div>
        `;
        
        resultsList.appendChild(card);
    });
    
    showResults();
}

// Display candidate results
function displayCandidateResults(data) {
    const resultsTitle = document.getElementById('results-title');
    const resultsSummary = document.getElementById('results-summary');
    const resultsList = document.getElementById('results-list');
    
    resultsTitle.innerHTML = '<i class="fas fa-users"></i> Top Candidate Matches';
    resultsSummary.textContent = `Found ${data.total_found} matches. Showing top ${data.matches.length} results using ${data.algorithm}.`;
    
    resultsList.innerHTML = '';
    
    data.matches.forEach((candidate, index) => {
        const card = document.createElement('div');
        card.className = 'result-card';
        
        // Format skills - handle both string and array
        let skillsDisplay = candidate.skills;
        if (typeof skillsDisplay === 'string' && skillsDisplay.startsWith('[')) {
            try {
                skillsDisplay = JSON.parse(skillsDisplay.replace(/'/g, '"')).join(', ');
            } catch (e) {
                // Keep as is if parsing fails
            }
        }
        
        card.innerHTML = `
            <div class="result-header">
                <div class="result-title">
                    <h3>${index + 1}. ${candidate.name}</h3>
                    <p>Candidate ID: ${candidate.employee_id}</p>
                </div>
                <div class="match-score">${candidate.match_score}%</div>
            </div>
            <div class="result-details">
                <div class="detail-item">
                    <i class="fas fa-industry"></i>
                    <span><strong>Sector:</strong> ${candidate.sector}</span>
                </div>
                <div class="detail-item">
                    <i class="fas fa-map-marker-alt"></i>
                    <span><strong>Location:</strong> ${candidate.location}</span>
                </div>
                <div class="detail-item">
                    <i class="fas fa-briefcase"></i>
                    <span><strong>Experience:</strong> ${candidate.experience} years</span>
                </div>
                <div class="detail-item">
                    <i class="fas fa-graduation-cap"></i>
                    <span><strong>Education:</strong> Level ${candidate.education}</span>
                </div>
                <div class="detail-item">
                    <i class="fas fa-money-bill-wave"></i>
                    <span><strong>Salary Expectation:</strong> ${candidate.salary_expectation.toLocaleString()} DZD</span>
                </div>
                <div class="detail-item" style="grid-column: 1 / -1;">
                    <i class="fas fa-code"></i>
                    <span><strong>Skills:</strong> ${skillsDisplay}</span>
                </div>
            </div>
        `;
        
        resultsList.appendChild(card);
    });
    
    showResults();
}

// Display no results message
function displayNoResults(type) {
    const resultsTitle = document.getElementById('results-title');
    const resultsSummary = document.getElementById('results-summary');
    const resultsList = document.getElementById('results-list');
    
    resultsTitle.innerHTML = '<i class="fas fa-exclamation-circle"></i> No Matches Found';
    resultsSummary.textContent = `Sorry, we couldn't find any matching ${type} based on your criteria. Try adjusting your search parameters.`;
    
    resultsList.innerHTML = `
        <div class="result-card" style="text-align: center; padding: 3rem;">
            <i class="fas fa-search" style="font-size: 3rem; color: #94a3b8; margin-bottom: 1rem;"></i>
            <h3>No matches found</h3>
            <p style="color: #64748b; margin-top: 1rem;">Try modifying your search criteria or expanding your preferences.</p>
        </div>
    `;
    
    showResults();
}

// Show/hide sections
function showSection(section) {
    // Hide all form containers
    document.getElementById('seeker-form').classList.add('hidden');
    document.getElementById('employer-form').classList.add('hidden');
    document.getElementById('results').classList.add('hidden');
    
    // Show the selected section
    if (section === 'seeker') {
        document.getElementById('seeker-form').classList.remove('hidden');
        currentSection = 'seeker';
        
        // Scroll to the form
        document.getElementById('match').scrollIntoView({ behavior: 'smooth' });
    } else if (section === 'employer') {
        document.getElementById('employer-form').classList.remove('hidden');
        currentSection = 'employer';
        
        // Scroll to the form
        document.getElementById('match').scrollIntoView({ behavior: 'smooth' });
    }
}

function showResults() {
    document.getElementById('seeker-form').classList.add('hidden');
    document.getElementById('employer-form').classList.add('hidden');
    document.getElementById('results').classList.remove('hidden');
    
    // Scroll to results
    document.getElementById('results').scrollIntoView({ behavior: 'smooth' });
}

function hideResults() {
    document.getElementById('results').classList.add('hidden');
    
    // Show the previous form
    if (currentSection === 'seeker') {
        document.getElementById('seeker-form').classList.remove('hidden');
    } else if (currentSection === 'employer') {
        document.getElementById('employer-form').classList.remove('hidden');
    }
    
    // Scroll to the form
    document.getElementById('match').scrollIntoView({ behavior: 'smooth' });
}

// Reset form
function resetForm(formId) {
    document.getElementById(formId).reset();
}

// Loading overlay
function showLoading() {
    document.getElementById('loading').classList.remove('hidden');
}

function hideLoading() {
    document.getElementById('loading').classList.add('hidden');
}

// Navigation
function setupNavigation() {
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Remove active class from all links
            navLinks.forEach(l => l.classList.remove('active'));
            
            // Add active class to clicked link
            this.classList.add('active');
            
            // Get the target section
            const target = this.getAttribute('href');
            
            // Scroll to the section
            document.querySelector(target).scrollIntoView({ behavior: 'smooth' });
        });
    });
    
    // Update active nav on scroll
    window.addEventListener('scroll', function() {
        let current = '';
        const sections = document.querySelectorAll('section');
        
        sections.forEach(section => {
            const sectionTop = section.offsetTop;
            const sectionHeight = section.clientHeight;
            
            if (pageYOffset >= sectionTop - 100) {
                current = section.getAttribute('id');
            }
        });
        
        navLinks.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href') === '#' + current) {
                link.classList.add('active');
            }
        });
    });
}
