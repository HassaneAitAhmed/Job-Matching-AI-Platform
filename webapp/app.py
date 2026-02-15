"""
Job Matching AI Platform - Flask Web Application
Backend API for matching job seekers with jobs using multiple AI algorithms
"""

from flask import Flask, render_template, request, jsonify
import pandas as pd
import json
import sys
import os
from ast import literal_eval

# Add parent directory to path to import from extracted code
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = Flask(__name__)

# Global variables to store loaded data
jobs_df = None
employees_df = None
city_distances = None
job_model = None
employee_model = None

def load_data():
    """Load all necessary data files"""
    global jobs_df, employees_df, city_distances, job_model, employee_model
    
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Load CSV data
    jobs_df = pd.read_csv(os.path.join(base_path, 'data', 'jobs.csv'))
    employees_df = pd.read_csv(os.path.join(base_path, 'data', 'emplo.csv'))
    
    # Load distance data
    with open(os.path.join(base_path, 'data', 'algeria_distances.json'), 'r') as f:
        city_distances = json.load(f)
    
    # Load pre-built models
    with open(os.path.join(base_path, 'job_transition_model.json'), 'r') as f:
        job_model = json.load(f)
    
    with open(os.path.join(base_path, 'employee_transition_model.json'), 'r') as f:
        employee_model = json.load(f)
    
    print("✅ Data loaded successfully!")

def calculate_skill_similarity(skills1, skills2):
    """Calculate similarity between two skill sets"""
    if not skills1 or not skills2:
        return 0.0
    
    # Convert to sets for comparison
    if isinstance(skills1, str):
        skills1 = [s.strip() for s in skills1.split(',')]
    if isinstance(skills2, str):
        skills2 = [s.strip() for s in skills2.split(',')]
    
    set1 = set(str(s).lower() for s in skills1)
    set2 = set(str(s).lower() for s in skills2)
    
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    
    return intersection / union if union > 0 else 0.0

def calculate_match_score(seeker, job):
    """Calculate a match score between a job seeker and a job"""
    score = 0.0
    max_score = 100.0
    
    # Skill matching (30 points)
    skill_sim = calculate_skill_similarity(
        seeker.get('technical_skills', ''),
        job.get('technical_skills', '')
    )
    score += skill_sim * 30
    
    # Education matching (15 points)
    seeker_edu = float(seeker.get('edu_value', 0) or 0)
    job_edu = float(job.get('edu_value', 0) or 0)
    if seeker_edu >= job_edu:
        score += 15
    elif seeker_edu >= job_edu - 3:
        score += 10
    
    # Experience matching (20 points)
    seeker_exp = float(seeker.get('years_experience', 0) or 0)
    job_exp_min = float(job.get('experience_min_req', 0) or 0)
    job_exp_max = float(job.get('experience_max_req', job_exp_min) or job_exp_min)
    
    if job_exp_min <= seeker_exp <= job_exp_max + 2:
        score += 20
    elif seeker_exp >= job_exp_min - 1:
        score += 15
    
    # Salary matching (15 points)
    seeker_salary = float(seeker.get('salary', 0) or 0)
    job_salary = float(job.get('salary', 0) or 0)
    
    if job_salary >= seeker_salary * 0.9:
        score += 15
    elif job_salary >= seeker_salary * 0.7:
        score += 10
    
    # Location matching (20 points)
    if seeker.get('city', '').lower() == job.get('job location', '').lower():
        score += 20
    else:
        # Check if cities are in the distance matrix
        seeker_city = seeker.get('city', '')
        job_city = job.get('job location', '')
        if seeker_city in city_distances and job_city in city_distances.get(seeker_city, {}):
            distance = city_distances[seeker_city].get(job_city, 1000)
            if distance < 50:
                score += 15
            elif distance < 150:
                score += 10
            elif distance < 300:
                score += 5
    
    return min(score, max_score)

@app.route('/')
def index():
    """Render the home page"""
    return render_template('index.html')

@app.route('/api/stats')
def get_stats():
    """Get statistics about the dataset"""
    return jsonify({
        'total_jobs': len(jobs_df),
        'total_seekers': len(employees_df),
        'sectors': jobs_df['sector'].nunique(),
        'cities': jobs_df['job location'].nunique()
    })

@app.route('/api/sectors')
def get_sectors():
    """Get list of unique sectors"""
    sectors = sorted(jobs_df['sector'].dropna().unique().tolist())
    return jsonify(sectors)

@app.route('/api/cities')
def get_cities():
    """Get list of unique cities"""
    cities = sorted(jobs_df['job location'].dropna().unique().tolist())
    return jsonify(cities)

@app.route('/api/skills')
def get_skills():
    """Get list of unique technical skills"""
    skills = set()
    for skill_list in jobs_df['technical_skills'].dropna():
        try:
            if isinstance(skill_list, str):
                parsed = literal_eval(skill_list)
                if isinstance(parsed, list):
                    skills.update(parsed)
        except (ValueError, SyntaxError):
            pass
    return jsonify(sorted(list(skills)))

@app.route('/api/match/seeker-to-jobs', methods=['POST'])
def match_seeker_to_jobs():
    """Find best jobs for a job seeker"""
    data = request.json
    
    # Extract seeker information
    seeker = {
        'technical_skills': data.get('skills', ''),
        'years_experience': data.get('experience', 0),
        'edu_value': data.get('education', 12),
        'city': data.get('city', ''),
        'salary': data.get('salary', 0),
        'sector': data.get('sector', ''),
        'contract_type': data.get('contract_type', '')
    }
    
    # Filter jobs based on basic criteria
    filtered_jobs = jobs_df.copy()
    
    if seeker['sector']:
        filtered_jobs = filtered_jobs[filtered_jobs['sector'] == seeker['sector']]
    
    if seeker['contract_type']:
        filtered_jobs = filtered_jobs[filtered_jobs['type of contract'] == seeker['contract_type']]
    
    # Calculate match scores for all filtered jobs
    matches = []
    for idx, job in filtered_jobs.head(100).iterrows():  # Limit to 100 for performance
        score = calculate_match_score(seeker, job.to_dict())
        if score > 30:  # Only include jobs with >30% match
            matches.append({
                'job_id': str(job.get('job_Id', idx)),
                'title': job.get('job title', 'N/A'),
                'company': job.get('company name', 'N/A'),
                'sector': job.get('sector', 'N/A'),
                'location': job.get('job location', 'N/A'),
                'contract_type': job.get('type of contract', 'N/A'),
                'salary': float(job.get('salary', 0) or 0),
                'experience_required': f"{job.get('experience_min_req', 0)}-{job.get('experience_max_req', 0)} years",
                'skills': str(job.get('technical_skills', 'N/A')),
                'match_score': round(score, 2)
            })
    
    # Sort by match score
    matches.sort(key=lambda x: x['match_score'], reverse=True)
    
    # Return top 10 matches
    return jsonify({
        'matches': matches[:10],
        'total_found': len(matches),
        'algorithm': 'Greedy Best-First Search'
    })

@app.route('/api/match/job-to-seekers', methods=['POST'])
def match_job_to_seekers():
    """Find best candidates for a job"""
    data = request.json
    
    # Extract job information
    job = {
        'technical_skills': data.get('skills', ''),
        'experience_min_req': data.get('experience_min', 0),
        'experience_max_req': data.get('experience_max', 10),
        'edu_value': data.get('education', 12),
        'job location': data.get('city', ''),
        'salary': data.get('salary', 0),
        'sector': data.get('sector', ''),
        'type of contract': data.get('contract_type', '')
    }
    
    # Filter employees based on basic criteria
    filtered_employees = employees_df.copy()
    
    if job['sector']:
        filtered_employees = filtered_employees[filtered_employees['sector'] == job['sector']]
    
    # Calculate match scores for all filtered employees
    matches = []
    for idx, employee in filtered_employees.head(100).iterrows():  # Limit to 100 for performance
        # Reverse the match calculation
        employee_dict = employee.to_dict()
        employee_dict['city'] = employee_dict.get('city', '')
        
        score = calculate_match_score(employee_dict, job)
        if score > 30:  # Only include candidates with >30% match
            matches.append({
                'employee_id': str(employee.get('employee_Id', idx)),
                'name': f"Candidate {idx}",  # Anonymous
                'sector': employee.get('sector', 'N/A'),
                'location': employee.get('city', 'N/A'),
                'experience': float(employee.get('years_experience', 0) or 0),
                'education': str(employee.get('edu_value', 'N/A')),
                'salary_expectation': float(employee.get('salary', 0) or 0),
                'skills': str(employee.get('technical_skills', 'N/A')),
                'match_score': round(score, 2)
            })
    
    # Sort by match score
    matches.sort(key=lambda x: x['match_score'], reverse=True)
    
    # Return top 10 matches
    return jsonify({
        'matches': matches[:10],
        'total_found': len(matches),
        'algorithm': 'Greedy Best-First Search'
    })

if __name__ == '__main__':
    print("🚀 Starting Job Matching AI Platform...")
    load_data()
    # Note: Set debug=False in production. Debug mode is only for development.
    import os
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(debug=debug_mode, host='0.0.0.0', port=5000)
