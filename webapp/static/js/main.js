// Main JavaScript for Job Matching AI Platform

const ALGORITHM_LABELS = {
    astar: 'A* search (optimal)',
    greedy: 'Greedy best-first (fast, approximate)',
    csp: 'CSP (hard constraints)',
    exhaustive: 'Exhaustive baseline (score everything)',
};

const CRITERION_LABELS = {
    sector: 'Sector',
    contract_type: 'Contract',
    education: 'Education',
    location: 'Location',
    experience: 'Experience',
    salary: 'Salary',
    skills: 'Skills',
};

const PAGE_SIZE = 10;

// State of the current search, used for "Load more".
let currentSection = null;
let lastSearch = null;   // { endpoint, payload, offset, kind }

document.addEventListener('DOMContentLoaded', () => {
    loadStats();
    loadOptions();
    loadSkills();
    setupFormHandlers();
    setupNavigation();
});

// ---------------------------------------------------------------- helpers

function el(tag, attrs = {}, ...children) {
    const node = document.createElement(tag);
    for (const [key, value] of Object.entries(attrs)) {
        if (key === 'class') node.className = value;
        else if (key === 'style') node.style.cssText = value;
        else node.setAttribute(key, value);
    }
    for (const child of children) {
        if (child === null || child === undefined) continue;
        node.append(child instanceof Node ? child : document.createTextNode(String(child)));
    }
    return node;
}

function icon(name) {
    return el('i', { class: `fas ${name}` });
}

function fillSelect(select, options) {
    for (const opt of options) {
        const value = typeof opt === 'object' ? opt.value : opt;
        const label = typeof opt === 'object' ? opt.label : opt;
        select.append(el('option', { value: String(value) }, label));
    }
}

function numberOrNull(id) {
    const raw = document.getElementById(id).value;
    return raw === '' ? null : Number(raw);
}

async function fetchJSON(url, options) {
    const response = await fetch(url, options);
    let data = null;
    try {
        data = await response.json();
    } catch (e) {
        // non-JSON body
    }
    if (!response.ok) {
        throw new Error((data && data.error) || `Request failed (${response.status})`);
    }
    return data;
}

// ---------------------------------------------------------------- bootstrapping

async function loadStats() {
    try {
        const stats = await fetchJSON('/api/stats');
        document.getElementById('total-jobs').textContent = stats.total_jobs.toLocaleString();
        document.getElementById('total-seekers').textContent = stats.total_seekers.toLocaleString();
        document.getElementById('total-sectors').textContent = stats.sectors;
        document.getElementById('total-cities').textContent = stats.cities;
        document.getElementById('about-vocab').textContent = stats.skill_vocabulary;
        const nodes = Object.values(stats.tree_nodes).reduce((a, b) => a + b, 0);
        document.getElementById('about-nodes').textContent = nodes.toLocaleString();
        document.getElementById('about-unlisted').textContent =
            `${stats.jobs_without_skills} / ${stats.total_jobs}`;
    } catch (error) {
        console.error('Error loading stats:', error);
        for (const id of ['total-jobs', 'total-seekers', 'total-sectors', 'total-cities']) {
            document.getElementById(id).textContent = 'N/A';
        }
    }
}

async function loadOptions() {
    try {
        const options = await fetchJSON('/api/options');
        document.querySelectorAll('.sector-select').forEach(s => fillSelect(s, options.sectors));
        document.querySelectorAll('.city-select').forEach(s => fillSelect(s, options.cities));
        document.querySelectorAll('.contract-select').forEach(s => fillSelect(s, options.contract_types));
        document.querySelectorAll('.edu-select').forEach(s => fillSelect(s, options.education_levels));
        document.querySelectorAll('.algorithm-select').forEach(s => {
            fillSelect(s, options.algorithms.map(a => ({ value: a, label: ALGORITHM_LABELS[a] || a })));
            s.addEventListener('change', () => toggleCspHint(s));
            toggleCspHint(s);
        });
    } catch (error) {
        console.error('Error loading options:', error);
    }
}

async function loadSkills() {
    try {
        const skills = await fetchJSON('/api/skills');
        const list = document.getElementById('skill-list');
        skills.forEach(s => list.append(el('option', { value: s })));
    } catch (error) {
        console.error('Error loading skills:', error);
    }
}

function toggleCspHint(select) {
    const hint = select.parentElement.querySelector('.csp-hint');
    if (hint) hint.classList.toggle('hidden', select.value !== 'csp');
}

// ---------------------------------------------------------------- forms

function setupFormHandlers() {
    document.getElementById('seekerForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const payload = {
            skills: document.getElementById('seeker-skills').value,
            experience: numberOrNull('seeker-experience'),
            education: numberOrNull('seeker-education'),
            city: document.getElementById('seeker-city').value,
            sector: document.getElementById('seeker-sector').value,
            contract_type: document.getElementById('seeker-contract').value,
            salary: numberOrNull('seeker-salary'),
            algorithm: document.getElementById('seeker-algorithm').value,
            max_distance_km: numberOrNull('seeker-max-km'),
        };
        await runSearch('/api/match/seeker-to-jobs', payload, 'jobs');
    });

    document.getElementById('employerForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const payload = {
            skills: document.getElementById('job-skills').value,
            experience_min: numberOrNull('job-experience-min'),
            experience_max: numberOrNull('job-experience-max'),
            education: numberOrNull('job-education'),
            city: document.getElementById('job-city').value,
            sector: document.getElementById('job-sector').value,
            contract_type: document.getElementById('job-contract').value,
            salary: numberOrNull('job-salary'),
            algorithm: document.getElementById('job-algorithm').value,
            max_distance_km: numberOrNull('job-max-km'),
        };
        await runSearch('/api/match/job-to-seekers', payload, 'candidates');
    });

    document.getElementById('assignForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        await runAssignment();
    });
}

async function runSearch(endpoint, payload, kind) {
    lastSearch = { endpoint, payload, offset: 0, kind };
    document.getElementById('results-list').replaceChildren();
    await fetchPage();
}

async function loadMore() {
    if (!lastSearch) return;
    lastSearch.offset += PAGE_SIZE;
    await fetchPage();
}

async function fetchPage() {
    showLoading();
    try {
        const body = { ...lastSearch.payload, limit: PAGE_SIZE, offset: lastSearch.offset };
        const data = await fetchJSON(lastSearch.endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });
        if (lastSearch.offset === 0 && data.matches.length === 0) {
            displayNoResults(lastSearch.kind);
        } else {
            displayResults(data, lastSearch.kind);
        }
    } catch (error) {
        console.error('Search failed:', error);
        alert(`Search failed: ${error.message}`);
    } finally {
        hideLoading();
    }
}

// ---------------------------------------------------------------- results

function displayResults(data, kind) {
    const title = document.getElementById('results-title');
    title.replaceChildren(
        icon(kind === 'jobs' ? 'fa-briefcase' : 'fa-users'),
        kind === 'jobs' ? ' Top Job Matches' : ' Top Candidate Matches',
    );

    const shown = lastSearch.offset + data.matches.length;
    document.getElementById('results-summary').textContent =
        `Showing ${shown} results ranked by ${ALGORITHM_LABELS[data.algorithm] || data.algorithm}.`;
    document.getElementById('results-stats').textContent = formatStats(data.stats);

    const list = document.getElementById('results-list');
    data.matches.forEach((match, i) => {
        const rank = lastSearch.offset + i + 1;
        list.append(kind === 'jobs' ? jobCard(match, rank) : candidateCard(match, rank));
    });

    document.getElementById('load-more').classList.toggle('hidden', !data.has_more);
    showResults();
}

function formatStats(stats) {
    const parts = [`${stats.elapsed_ms} ms`];
    if (stats.nodes_expanded) parts.push(`${stats.nodes_expanded} tree nodes expanded`);
    parts.push(`${stats.items_scored} items scored`);
    if (stats.solutions !== undefined) parts.push(`${stats.solutions} items satisfy the constraints`);
    if (stats.relaxed_constraints && stats.relaxed_constraints.length) {
        parts.push(`relaxed: ${stats.relaxed_constraints.join(', ')}`);
    }
    return parts.join(' · ');
}

function detail(iconName, label, value, wide = false) {
    return el('div', { class: 'detail-item', style: wide ? 'grid-column: 1 / -1;' : '' },
        icon(iconName),
        el('span', {}, el('strong', {}, `${label}: `), value));
}

function breakdownBars(breakdown) {
    const wrap = el('div', { class: 'breakdown' });
    for (const [criterion, { score, weight }] of Object.entries(breakdown)) {
        const level = score >= 75 ? 'good' : score >= 40 ? 'mid' : 'low';
        wrap.append(el('div', { class: 'breakdown-row', title: `weight ${weight}%` },
            el('span', { class: 'breakdown-label' }, CRITERION_LABELS[criterion] || criterion),
            el('span', { class: 'breakdown-track' },
                el('span', { class: `breakdown-fill ${level}`, style: `width: ${Math.max(0, Math.min(100, score))}%` })),
            el('span', { class: 'breakdown-value' }, `${Math.round(score)}%`),
            el('span', { class: 'breakdown-weight' }, `×${weight}%`)));
    }
    return wrap;
}

function skillsLine(match) {
    if (!match.skills_listed) {
        return el('em', { class: 'muted' }, 'No skills listed (scored as a weak skills match)');
    }
    return match.skills.join(', ');
}

function cardShell(rank, heading, subheading, score) {
    const card = el('div', { class: 'result-card' });
    card.append(el('div', { class: 'result-header' },
        el('div', { class: 'result-title' }, el('h3', {}, `${rank}. ${heading}`), el('p', {}, subheading)),
        el('div', { class: 'match-score' }, `${score}%`)));
    return card;
}

function jobCard(job, rank) {
    const card = cardShell(rank, job.title, `Job #${job.id} · ${job.department}`, job.match_score);
    card.append(el('div', { class: 'result-details' },
        detail('fa-industry', 'Sector', job.sector),
        detail('fa-map-marker-alt', 'Location', job.city),
        detail('fa-file-contract', 'Contract', job.contract_type),
        detail('fa-money-bill-wave', 'Salary', `${job.salary.toLocaleString()} DZD`),
        detail('fa-briefcase', 'Experience', `${job.experience_required[0]}-${job.experience_required[1]} years`),
        detail('fa-graduation-cap', 'Education', job.education_required),
        detail('fa-code', 'Skills', skillsLine(job), true)));
    card.append(breakdownBars(job.breakdown));
    return card;
}

function candidateCard(c, rank) {
    const card = cardShell(rank, `Candidate #${c.id}`, c.department, c.match_score);
    card.append(el('div', { class: 'result-details' },
        detail('fa-industry', 'Sector', c.sector),
        detail('fa-map-marker-alt', 'Location', c.city),
        detail('fa-file-contract', 'Seeking', c.contract_type),
        detail('fa-briefcase', 'Experience', `${c.experience_years} years`),
        detail('fa-graduation-cap', 'Education', c.education),
        detail('fa-money-bill-wave', 'Expects', `${c.salary_expectation.toLocaleString()} DZD`),
        detail('fa-code', 'Skills', skillsLine(c), true)));
    card.append(breakdownBars(c.breakdown));
    return card;
}

function displayNoResults(type) {
    document.getElementById('results-title').replaceChildren(icon('fa-exclamation-circle'), ' No Matches Found');
    document.getElementById('results-summary').textContent =
        `We couldn't find any matching ${type}. Try adjusting your search parameters.`;
    document.getElementById('results-stats').textContent = '';
    document.getElementById('results-list').replaceChildren(
        el('div', { class: 'result-card', style: 'text-align: center; padding: 3rem;' },
            el('h3', {}, 'No matches found')));
    document.getElementById('load-more').classList.add('hidden');
    showResults();
}

// ---------------------------------------------------------------- batch assignment

async function runAssignment() {
    const out = document.getElementById('assign-results');
    out.replaceChildren(el('p', {}, 'Running...'));
    try {
        const data = await fetchJSON('/api/assign', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                n_seekers: numberOrNull('assign-seekers'),
                n_jobs: numberOrNull('assign-jobs'),
                sector: document.getElementById('assign-sector').value,
                seed: numberOrNull('assign-seed'),
            }),
        });
        const table = el('table', { class: 'assign-table' },
            el('thead', {}, el('tr', {},
                el('th', {}, 'Method'), el('th', {}, 'Total score'), el('th', {}, '% of optimal'),
                el('th', {}, 'Assigned'), el('th', {}, 'Time'))));
        const tbody = el('tbody');
        for (const r of data.results) {
            tbody.append(el('tr', {},
                el('td', {}, r.method), el('td', {}, r.total_score.toFixed(3)),
                el('td', {}, `${r.pct_of_optimal}%`), el('td', {}, r.assigned),
                el('td', {}, `${r.elapsed_ms} ms`)));
        }
        table.append(tbody);
        out.replaceChildren(
            el('p', {}, `${data.n_seekers} seekers, ${data.n_jobs} postings with ${data.total_posts} open posts.`),
            table,
            el('p', { class: 'muted' },
                'Optimal = Hungarian algorithm (exact). Pair score = mean of the seeker and employer perspectives.'));
    } catch (error) {
        out.replaceChildren(el('p', { class: 'error' }, `Assignment failed: ${error.message}`));
    }
}

// ---------------------------------------------------------------- sections & navigation

function showSection(section) {
    document.getElementById('seeker-form').classList.add('hidden');
    document.getElementById('employer-form').classList.add('hidden');
    document.getElementById('results').classList.add('hidden');
    if (section === 'seeker' || section === 'employer') {
        document.getElementById(`${section}-form`).classList.remove('hidden');
        currentSection = section;
        document.getElementById('match').scrollIntoView({ behavior: 'smooth' });
    }
}

function showResults() {
    document.getElementById('seeker-form').classList.add('hidden');
    document.getElementById('employer-form').classList.add('hidden');
    document.getElementById('results').classList.remove('hidden');
    if (lastSearch && lastSearch.offset === 0) {
        document.getElementById('results').scrollIntoView({ behavior: 'smooth' });
    }
}

function hideResults() {
    document.getElementById('results').classList.add('hidden');
    if (currentSection) {
        document.getElementById(`${currentSection}-form`).classList.remove('hidden');
    }
    document.getElementById('match').scrollIntoView({ behavior: 'smooth' });
}

function resetForm(formId) {
    document.getElementById(formId).reset();
    document.querySelectorAll(`#${formId} .algorithm-select`).forEach(toggleCspHint);
}

function showLoading() {
    document.getElementById('loading').classList.remove('hidden');
}

function hideLoading() {
    document.getElementById('loading').classList.add('hidden');
}

function setupNavigation() {
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        link.addEventListener('click', function (e) {
            e.preventDefault();
            navLinks.forEach(l => l.classList.remove('active'));
            this.classList.add('active');
            document.querySelector(this.getAttribute('href')).scrollIntoView({ behavior: 'smooth' });
        });
    });

    window.addEventListener('scroll', () => {
        let current = '';
        document.querySelectorAll('section').forEach(section => {
            if (window.scrollY >= section.offsetTop - 100) current = section.getAttribute('id');
        });
        navLinks.forEach(link => {
            link.classList.toggle('active', link.getAttribute('href') === '#' + current);
        });
    });
}
