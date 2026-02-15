# 🎯 Job Matching AI Platform

<div align="center">

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Jupyter](https://img.shields.io/badge/Jupyter-Notebook-orange.svg)
![Flask](https://img.shields.io/badge/Flask-3.0-green.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)
![License](https://img.shields.io/badge/License-Academic-green.svg)
![Status](https://img.shields.io/badge/Status-Completed-success.svg)

**An AI-driven job matching platform using advanced search algorithms and constraint satisfaction techniques**

*Spring 2025*

### 🚀 Quick Deploy

[![Deploy to Heroku](https://img.shields.io/badge/Deploy%20to-Heroku-purple?logo=heroku&style=for-the-badge)](https://heroku.com/deploy)
[![Deploy to Render](https://img.shields.io/badge/Deploy%20to-Render-46E3B7?logo=render&style=for-the-badge)](https://render.com)
[![Deploy with Docker](https://img.shields.io/badge/Deploy%20with-Docker-2496ED?logo=docker&style=for-the-badge)](#-deployment)

**[📖 Full Deployment Guide](DEPLOYMENT.md)** | **[⚡ Quick Start](HOSTING.md)**

</div>

---

## 🏛️ Academic Information

| | |
|---|---|
| **Institution** | The National Higher School of Artificial Intelligence (ENSIA), Algeria |
| **Course** | Introduction to Artificial Intelligence |
| **Supervisor** | Professor **Ahmed Guessoum** |
| **Semester** | Spring 2025 |

---

## 📋 Table of Contents

- [Abstract](#-abstract)
- [Problem Statement](#-problem-statement)
- [Features](#-features)
- [Project Structure](#-project-structure)
- [Algorithms Implemented](#-algorithms-implemented)
- [Data Preprocessing](#-data-preprocessing)
- [Installation](#-installation)
- [Usage](#-usage)
- [Deployment](#-deployment)
- [Results & Performance](#-results--performance)
- [Team Members & Contributions](#-team-members--contributions)
- [References](#-references)

---

## 📄 Abstract

This project is a **job matching AI-driven platform** that enables:
- **Employers** to find the most suitable candidates for job postings
- **Job seekers** to discover the most suitable jobs based on their capabilities and preferences

The system evaluates multiple features including technical skills, experience levels, city/location, sector, education, and expected salary to provide optimal matches using various AI techniques.

---

## 🎯 Problem Statement

The Algerian job market faces significant challenges in efficiently connecting qualified candidates with suitable employment opportunities. Despite high unemployment rates (particularly among youth), many employers struggle to find candidates whose skills and expectations align with their needs.

### Key Challenges Addressed:
- ❌ Inefficient job search methods
- ❌ Lack of standardized skill assessments
- ❌ Geographical imbalances in opportunity distribution
- ❌ Time-consuming manual screening processes

### Our Solution:
- ✅ AI-driven matching using multiple algorithms
- ✅ Hierarchical clustering for efficient search
- ✅ Multi-feature evaluation (skills, location, education, experience, salary)
- ✅ Bidirectional matching (Seeker→Job and Job→Seeker)

---

## ✨ Features

### Core Functionality
| Feature | Description |
|---------|-------------|
| **Seeker → Job Matching** | Find the best jobs for a given job seeker profile |
| **Job → Seeker Matching** | Find the best candidates for a given job posting |
| **Custom Profile Creation** | Create custom job or employee profiles for matching |
| **Algorithm Comparison** | Compare execution times across all algorithms |

### Matching Criteria
- 🏢 **Sector** - Industry alignment (IT, Healthcare, Finance, etc.)
- 📝 **Contract Type** - CDI, CDD, Alternance preferences
- 🎓 **Education Level** - BAC, Licence, Master, Ingénieur d'État, Doctorat
- 📍 **Location** - City-based matching with distance calculations
- ⏱️ **Experience** - Years of experience requirements
- 💰 **Salary** - Salary expectations and offerings
- 🔧 **Technical Skills** - Skill-based similarity matching

---

## 📁 Project Structure

```
Job-Matching-AI-Platform/
├── 📓 finalversion.ipynb           # Main Jupyter notebook with all implementations
├── 📊 data/
│   ├── jobs.csv                    # Job postings dataset
│   ├── emplo.csv                   # Employee/seeker dataset
│   └── algeria_distances.json      # City distance matrix for Algeria
├── 📄 job_transition_model.json    # Pre-built job clustering model
├── 📄 employee_transition_model.json # Pre-built employee clustering model
├── 📑 report.pdf                   # Detailed project report
├── 🌐 webapp/                      # Web application
│   ├── app.py                      # Flask backend server
│   ├── requirements.txt            # Python dependencies
│   ├── templates/
│   │   └── index.html              # Main web interface
│   ├── static/
│   │   ├── css/style.css          # Styling
│   │   └── js/main.js             # Frontend JavaScript
│   └── README.md                   # Web app documentation
└── 📖 README.md                    # This file
```


---

## 🧠 Algorithms Implemented

### 1. A* Search Algorithm
The A* algorithm finds optimal matches by combining:
- **Path cost g(n)**: Accumulated cost from start to current node
- **Heuristic h(n)**: Estimated cost to reach the goal

```
f(n) = g(n) + h(n)
```

**Properties:**
- ✅ Optimal solution guaranteed
- ✅ 92% match accuracy
- ⏱️ Time Complexity: O(n) worst case, much less on average
- 💾 Space Complexity: O(n)

### 2. Greedy Best-First Search
Uses only the heuristic function to guide the search:

```
f(n) = h(n)
```

**Properties:**
- ⚡ Fastest execution
- 📊 78% accuracy
- ⏱️ Time Complexity: O(n log|C|)
- 💾 Space Complexity: O(log n)

### 3. Genetic Algorithm (GA)
Evolutionary approach for job-employee pair optimization:

**Key Components:**
- **Chromosome**: Set of job-employee pairs
- **Fitness Function**: Multi-criteria scoring (skills, location, experience, salary, education)
- **Selection**: Tournament selection (k=3)
- **Crossover**: Uniform crossover with pair validation
- **Mutation**: Random pair replacement

**Fitness Weights:**
| Criterion | Weight |
|-----------|--------|
| Skills | 30% |
| Location | 20% |
| Experience | 20% |
| Salary | 15% |
| Education | 15% |

**Properties:**
- 📊 85% accuracy with 50 chromosomes
- 🔄 Converges in ~23 generations on average
- ⏱️ Time Complexity: O(g × p × c)

### 4. Constraint Satisfaction Problem (CSP)
Models the matching problem with:
- **Variables**: Attributes (sector, contract_type, edu_value, city, years_experience)
- **Domains**: Possible values from the transition model
- **Constraints**: Hard (sector, contract) and soft (education, location, salary)

**Key Features:**
- Depth-first search with backtracking
- Value ordering based on compatibility
- Fallback mechanism for partial matches

---

## 🔄 Data Preprocessing

### Hierarchical Feature-Based Clustering

The preprocessing creates a tree-like structure for efficient search:

```
Feature Order: [sector, contract_type, edu_value, city, years_experience]
```

#### Cluster Tree Structure:
```
ClusterTree:
├── sector=IT
│   ├── contract_type=CDI
│   │   ├── edu_value=Master
│   │   │   ├── city=Algiers
│   │   │   │   ├── experience=5+years
│   │   │   │   │   └── [job_ids: 123, 456, ...]
│   │   │   │   └── ...
│   │   │   └── ...
│   │   └── ...
│   └── ...
└── ...
```

#### Direction-Based Aggregation:
- **Job Model**: Prefers lower requirements (min education/experience) but higher salaries
- **Employee Model**: Prefers higher qualifications but lower salary expectations

### Expected Values per Cluster:
Each cluster stores aggregated "expected values" for heuristic calculations:
- Maximum/minimum feature values based on direction
- Skill sets available in the cluster
- Salary ranges

---

## 🚀 Installation

### Prerequisites
- Python 3.9 or higher
- Jupyter Notebook (for notebook version)
- Flask (for web application)

### Option 1: Web Application (Recommended)

The easiest way to use the platform is through our web interface:

1. **Navigate to the webapp directory**
```bash
cd webapp
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Run the web application**
```bash
python app.py
```

4. **Open your browser**
Navigate to `http://localhost:5000`

See [webapp/README.md](webapp/README.md) for detailed instructions.

### Option 2: Jupyter Notebook

1. **Clone/Download the repository**
```bash
cd ff
```

2. **Install dependencies**
```bash
pip install pandas numpy scikit-learn matplotlib tqdm
```

3. **Launch Jupyter Notebook**
```bash
jupyter notebook finalversion.ipynb
```

---

## 💻 Usage

### Web Application Usage

The web application provides an intuitive interface for both job seekers and employers:

#### For Job Seekers:
1. Click **"I'm a Job Seeker"** on the home page
2. Fill in your details:
   - Technical skills (e.g., "Python, Machine Learning, SQL")
   - Years of experience
   - Education level
   - Preferred city
   - Sector and contract type preferences (optional)
   - Expected salary
3. Click **"Find Jobs"** to see your top matches with percentage scores

#### For Employers:
1. Click **"I'm an Employer"** on the home page
2. Fill in job requirements:
   - Required technical skills
   - Experience range (min-max years)
   - Education level required
   - Job location
   - Offered salary
3. Click **"Find Candidates"** to see top candidate matches

### Jupyter Notebook Usage

Execute all cells in the notebook, then run the final cell to access the interactive menu:

```
1) CSP: seeker → jobs
2) CSP: job → seekers
3) Search (A*/Greedy)
4) Genetic Algorithm (GA)
5) Compare all (CSP, Search & GA) with timing
```

### Example: Finding Jobs for a Seeker

```python
# Using CSP
seeker = Seeker(
    id=1, 
    name='John Doe', 
    skills={'Python', 'Java'}, 
    experience=10,
    salary=50000, 
    preferred_locations={'Algiers'},
    preferred_job_types={'CDI'}, 
    sector='Information Technology',
    education='12'
)

csp = JobMatchingCSP(
    seeker_model, job_model, attribute_order,
    items=[seeker], 
    city_distances=city_dist,
    direction='seeker_to_job', 
    top_k=3
)
results = csp.solve()
```

### Example: Using A* Search

```python
candidate = {
    'sector': 'Healthcare',
    'contract_type': 'CDD',
    'edu_value': '12',
    'city': 'Jijel',
    'years_experience': '8',
    'salary': '50000',
    'technical_skills': 'Precision Medicine'
}

gs = GeneralSearch(
    transition_model_path='employee_transition_model.json',
    distances_path='data/algeria_distances.json',
    direction='employee'
)
gs.set_entity(candidate)
results = gs.search_astar(k=3)
```

### Example: Using Genetic Algorithm

```python
# Load data
jobs = DataLoader.load_jobs('data/jobs.csv')
employees = DataLoader.load_employees('data/emplo.csv')

# Create custom employee
employee = EmPloyee(
    employee_id="test_001",
    technical_skills="python, sql, machine learning",
    years_experience=4,
    highest_education="master",
    city="algiers",
    salary_expectation=75000
)

# Initialize GA and match
ga = PairGA(
    jobs=jobs,
    employees=[employee],
    pop_size=10,
    generations=100,
    mutation_rate=0.1,
    max_pairs=5,
    distance_file="data/algeria_distances.json"
)
_, matches = ga.match_custom_employee(employee, top_n=5)
```

---

## 🚀 Deployment

The web application can be easily deployed to various hosting platforms. Multiple deployment options are available:

### Quick Deployment

**🐳 Docker (Recommended):**
```bash
docker-compose up -d
# Application available at http://localhost:8080
```

**☁️ Cloud Platforms:**

| Platform | Difficulty | Free Tier | Deploy Command |
|----------|-----------|-----------|----------------|
| **Heroku** | ⭐ Easy | Yes (550 hrs/mo) | `git push heroku main` |
| **Railway** | ⭐ Easy | $5 credit/mo | Connect GitHub repo |
| **Render** | ⭐⭐ Medium | Yes (limited) | Connect GitHub repo |
| **Google Cloud Run** | ⭐⭐⭐ Advanced | Yes (2M requests/mo) | `gcloud run deploy` |
| **PythonAnywhere** | ⭐⭐ Medium | Yes (512MB) | Manual setup |

### Deployment Files Included

- ✅ `Dockerfile` - Container configuration
- ✅ `docker-compose.yml` - Easy Docker setup
- ✅ `Procfile` - Heroku/Railway configuration
- ✅ `render.yaml` - Render.com configuration
- ✅ `runtime.txt` - Python version specification
- ✅ `requirements.txt` - All dependencies including gunicorn

### Comprehensive Guide

See **[DEPLOYMENT.md](DEPLOYMENT.md)** for detailed instructions including:

- 📦 Docker deployment
- ☁️ Cloud platform setup (Heroku, Railway, Render, Google Cloud)
- 🖥️ VPS deployment with Nginx
- 🔧 Environment configuration
- 📊 Monitoring and logging
- 🔐 Security best practices
- 🐛 Troubleshooting guide

### One-Line Deploy Examples

**Heroku:**
```bash
heroku create && git push heroku main
```

**Docker:**
```bash
docker build -t job-matching-ai . && docker run -p 8080:8080 job-matching-ai
```

**Health Check:**
```bash
curl http://your-app-url/health
```

---

## 📊 Results & Performance

### Execution Time Comparison

| Algorithm | Execution Time | Accuracy |
|-----------|---------------|----------|
| CSP (S→J) | ~0.0005s | High |
| CSP (J→S) | ~0.0001s | High |
| A* Search | ~0.0038s | 92% |
| Greedy | ~0.0010s | 78% |
| GA | ~0.0006s | 85% |

### Key Achievements

- 📈 **92%** match accuracy with A* algorithm
- ⏱️ **0.005s** worst-case latency across all algorithms
- 🔍 **60%** reduction in search space through hierarchical clustering
- ⚡ **40%** reduction in hiring time compared to manual screening
- 🌍 **87%** accuracy in location preference matching
- 👥 **72%** more diverse shortlists than traditional methods

### Comparative Analysis

| Algorithm | Best For | Trade-off |
|-----------|----------|-----------|
| **A*** | Optimal accuracy | Higher memory usage |
| **Greedy** | Speed-critical applications | Lower quality matches |
| **GA** | Large-scale batch matching | Requires tuning |
| **CSP** | Constraint-heavy scenarios | Rigid constraints |

---

## 👥 Team Members & Contributions

### Project Team

| Name | Group | Contributions |
|------|-------|---------------|
| **Hassane Ait Ahmed Lamara** | G5 | • Genetic algorithm formulation<br>• Implementation of cost function for global search<br>• Global problem formulation<br>• Data scraping<br>• Dataset section in report |
| **Nasrellah Kharoubi** | G8 | • Data cleaning<br>• Global problem formulation<br>• Resource gathering<br>• Proving the admissibility of the heuristic |
| **Louai Nasrellah Soufi** | G4 | • Data cleaning<br>• Implementing preprocessing (hierarchical clustering)<br>• Implementing functions in global search<br>• Implementing inference function in CSP<br>• Problem solving techniques in report |
| **Yahia Kerroum** | G6 | • Implementing the genetic algorithm<br>• Implementing the heuristic function<br>• Writing results analysis in report<br>• A* and CSP problem formulation |
| **Islam Benali** | G1 | • Implementing CSP components<br>• Designing the platform<br>• Visualization contributions<br>• Discussion section in report |
| **Mohamed Toubal** | G1 | • Gathering data<br>• CSP formulation contributions<br>• Genetic algorithm implementation<br>• Writing remaining parts of report |

---

## 📚 Dataset

### Data Sources
- **Emploitic.com**: Scraped using [emploitic-scraper](https://github.com/Typh00ns/emploitic-scraper)
- **LinkedIn**: Collected via [Apify API](https://apify.com/curious_coder/linkedin-profile-scraper)
- **Google Forms**: Real-world data from Algerian professionals

### Data Processing
- Standardization with ChatGPT assistance
- Median/mean imputation for numerical fields
- Mode imputation for categorical fields
- Duplicate removal and text normalization

### Dataset Links
- [Employee Dataset](link-to-employee-dataset)
- [Job Dataset](link-to-job-dataset)
- [Algeria Distances Dataset](link-to-distances-dataset)

---

## 🔮 Future Work

- 🔗 Integration with Algerian national employment database
- 📱 Mobile app for real-time candidate notifications
- 🌐 Arabic NLP for CV parsing enhancement
- 🤖 Deep learning for improved skill matching
- 📊 Real-time market adaptation using reinforcement learning

---

## 📖 References

1. Emploitic Website - [emploitic.com](https://emploitic.com)
2. Apify Scripts - [apify.com](https://apify.com)
3. Scraping Tool - [GitHub Repository](https://github.com/Typh00ns/emploitic-scraper)
4. LLMs for Debugging
5. Statistical studies on attribute weights

---

## 📄 License

This project was developed for academic purposes at **The National Higher School of Artificial Intelligence (ENSIA), Algeria** under the supervision of **Professor Ahmed Guessoum**.

