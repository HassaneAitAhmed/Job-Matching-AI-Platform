# Job Matching AI Platform - Web Application

This is the web interface for the Job Matching AI Platform, providing an intuitive way to interact with the AI matching algorithms.

## Features

- **Job Seeker Matching**: Find the best jobs based on your skills, experience, and preferences
- **Employer Matching**: Find the best candidates for your job openings
- **Real-time Results**: Get instant matching results with percentage scores
- **Multiple Criteria**: Matches based on skills, location, experience, education, and salary
- **Beautiful UI**: Modern, responsive design that works on all devices

## Quick Start

### Prerequisites

- Python 3.9 or higher
- pip (Python package manager)

### Installation

1. Navigate to the webapp directory:
```bash
cd webapp
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python app.py
```

**For development with debug mode:**
```bash
export FLASK_DEBUG=true  # On Linux/Mac
set FLASK_DEBUG=true     # On Windows
python app.py
```

4. Open your web browser and navigate to:
```
http://localhost:5000
```

> **Security Note**: Debug mode is disabled by default for security. Only enable it during development, never in production.

## Usage

### For Job Seekers

1. Click "I'm a Job Seeker" on the home page
2. Fill in your details:
   - Technical skills (comma-separated)
   - Years of experience
   - Education level
   - Preferred city
   - Sector preference (optional)
   - Contract type preference (optional)
   - Expected salary
3. Click "Find Jobs"
4. View your top 10 job matches with match scores

### For Employers

1. Click "I'm an Employer" on the home page
2. Fill in the job details:
   - Required technical skills (comma-separated)
   - Minimum and maximum experience required
   - Required education level
   - Job location
   - Sector (optional)
   - Contract type (optional)
   - Offered salary
3. Click "Find Candidates"
4. View your top 10 candidate matches with match scores

## Project Structure

```
webapp/
├── app.py                 # Flask backend server
├── requirements.txt       # Python dependencies
├── static/
│   ├── css/
│   │   └── style.css     # Styling
│   └── js/
│       └── main.js       # Frontend JavaScript
└── templates/
    └── index.html        # Main HTML template
```

## API Endpoints

- `GET /` - Main web interface
- `GET /api/stats` - Get dataset statistics
- `GET /api/sectors` - Get list of sectors
- `GET /api/cities` - Get list of cities
- `GET /api/skills` - Get list of technical skills
- `POST /api/match/seeker-to-jobs` - Match a job seeker to jobs
- `POST /api/match/job-to-seekers` - Match a job to candidates

## Matching Algorithm

The platform uses a weighted scoring system:

| Criterion | Weight |
|-----------|--------|
| Technical Skills | 30% |
| Experience | 20% |
| Location | 20% |
| Education | 15% |
| Salary | 15% |

## Technologies Used

- **Backend**: Flask (Python)
- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **Data Processing**: Pandas, NumPy
- **Styling**: Custom CSS with modern design
- **Icons**: Font Awesome 6

## Deployment

### Quick Deployment Options

This application can be easily deployed to various hosting platforms:

**🚀 One-Click Deployment:**
- **Heroku**: `git push heroku main`
- **Railway**: Connect GitHub repo in dashboard
- **Render**: Connect GitHub repo and auto-deploy

**🐳 Docker Deployment:**
```bash
# From project root
docker-compose up -d
# App available at http://localhost:8080
```

**📚 Detailed Instructions:**

See the comprehensive [DEPLOYMENT.md](../DEPLOYMENT.md) guide for:
- Docker deployment
- Heroku deployment
- Railway deployment
- Render deployment
- Google Cloud Run
- PythonAnywhere
- VPS deployment
- Environment configuration
- Monitoring and troubleshooting

### Production Configuration

For production deployment, the application uses:
- **Gunicorn** as WSGI server (2 workers, 4 threads)
- **Port** from environment variable (default: 5000)
- **Debug mode** disabled by default
- **Health check** endpoint at `/health`

Example with gunicorn:
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## Troubleshooting

### Port Already in Use

If port 5000 is already in use, you can change it in `app.py`:
```python
app.run(debug=True, host='0.0.0.0', port=8000)  # Change to any available port
```

### Data Files Not Found

Make sure you're running the application from the correct directory and that the data files exist in the parent directory:
- `data/jobs.csv`
- `data/emplo.csv`
- `data/algeria_distances.json`
- `job_transition_model.json`
- `employee_transition_model.json`

## Future Enhancements

- [ ] User authentication and profiles
- [ ] Save search history
- [ ] Advanced filtering options
- [ ] Export results to PDF/CSV
- [ ] Integration with other algorithms (A*, GA, CSP)
- [ ] Real-time updates
- [ ] Mobile app

## License

This project was developed for academic purposes at **The National Higher School of Artificial Intelligence (ENSIA), Algeria**.

## Support

For issues or questions, please refer to the main project README or contact the development team.
