class JobSeeker:
    def __init__(self, skills, experience, salary, location, job_interest, sector, education_level, job_id):
        self.skills = set(skills)
        self.experience = experience
        self.salary = salary
        self.location = location
        self.job_interest = job_interest
        self.sector = sector
        self.education_level = education_level
        self.id = job_id

class JobOffer:
    def __init__(self, required_skills, min_experience, salary_range, location, sector, education_level):
        self.required_skills = set(required_skills)
        self.min_experience = min_experience
        self.salary_range = salary_range
        self.location = location
        self.sector = sector
        self.education_level = education_level

def build_domains(job_seekers, job_offers):
    domains = {}
    for seeker in job_seekers:
        eligible_offers = []
        for offer in job_offers:
            # Check all constraints
            skills_match = offer.required_skills.issubset(seeker.skills)
            experience_met = seeker.experience >= offer.min_experience
            salary_ok = offer.salary_range[0] <= seeker.salary <= offer.salary_range[1]
            location_match = seeker.location == offer.location
            sector_match = seeker.job_interest == offer.sector
            education_ok = seeker.education_level >= offer.education_level
            
            if all([skills_match, experience_met, salary_ok, location_match, sector_match, education_ok]): 
                eligible_offers.append(offer)
        domains[seeker] = eligible_offers
    return domains

def select_unassigned_variable(assignment, domains):
    unassigned = [s for s in domains if s not in assignment]
    
    # MRV: Sort by remaining offers
    unassigned.sort(key=lambda x: len(domains[x]))
    if not unassigned:
        return None
    
    # Degree Heuristic: Break ties by most constrained neighbors
    mrv_candidates = [u for u in unassigned if len(domains[u]) == len(domains[unassigned[0]])]
    
    max_degree = -1
    selected = mrv_candidates[0]
    for candidate in mrv_candidates:
        degree = sum(1 for other in unassigned if other != candidate and set(domains[candidate]).intersection(domains[other]))
        if degree > max_degree:
            max_degree = degree
            selected = candidate
    return selected

def order_domain_values(seeker, domains, assignment):
    offer_scores = []
    for offer in domains[seeker]:
        # LCV: Score based on how many other seekers can still use this offer
        dependent_seekers = sum(1 for s in domains if s not in assignment and offer in domains[s] and s != seeker)
        score = 1 / (dependent_seekers + 1)  # Higher score = less constraining
        offer_scores.append((offer, score))
    
    # Sort by descending score
    offer_scores.sort(key=lambda x: -x[1])
    return [offer for offer, _ in offer_scores]

def backtrack(assignment, domains):
    if len(assignment) == len(domains):
        return assignment
    
    seeker = select_unassigned_variable(assignment, domains)
    if not seeker:
        return None
    
    for offer in order_domain_values(seeker, domains, assignment):
        # Create new assignment
        assignment[seeker] = offer
        result = backtrack(assignment, domains)
        if result:
            return result
        del assignment[seeker]
    
    return None

def score_job(seeker, offer):
    # Scoring weights
    salary_score = (seeker.salary - offer.salary_range[0]) / (offer.salary_range[1] - offer.salary_range[0] + 1)
    skill_score = len(offer.required_skills & seeker.skills) / len(offer.required_skills)
    experience_score = min(seeker.experience / offer.min_experience, 1.5)
    education_score = 1.0 if seeker.education_level >= offer.education_level else 0.0
    
    # Weighted sum (tweak these as needed)
    total_score = (
        0.4 * salary_score +
        0.3 * skill_score +
        0.2 * experience_score +
        0.1 * education_score
    )
    return total_score

def build_top_k_domains(job_seekers, job_offers, k=3):
    domains = {}
    for seeker in job_seekers:
        scored_offers = []
        for offer in job_offers:
            skills_match = offer.required_skills.issubset(seeker.skills)
            experience_met = seeker.experience >= offer.min_experience
            salary_ok = offer.salary_range[0] <= seeker.salary <= offer.salary_range[1]
            location_match = seeker.location == offer.location
            sector_match = seeker.job_interest == offer.sector
            education_ok = seeker.education_level >= offer.education_level
            
            if all([skills_match, experience_met, salary_ok, location_match, sector_match, education_ok]): 
                score = score_job(seeker, offer)
                scored_offers.append((offer, score))
        
        # Sort and take top k offers
        top_offers = sorted(scored_offers, key=lambda x: -x[1])[:k]
        domains[seeker] = [offer for offer, _ in top_offers]
    return domains


# Example usage
seekers = [
    JobSeeker(
        skills=["Python", "ML"],
        experience=5,
        salary=65000,
        location="Algiers",
        job_interest="AI",
        sector="Tech",
        education_level=3,  # Assuming 3=Bachelor's
        job_id=1
    )
]

offers = [
    JobOffer(
        required_skills=["Python", "ML"],
        min_experience=3,
        salary_range=(60000, 70000),
        location="Algiers",
        sector="AI",
        education_level=3
    )
]

domains = build_domains(seekers, offers)
solution = backtrack({}, domains)

if solution:
    for seeker, offer in solution.items():
        print(f"JobSeeker {seeker.id} matched to offer in {offer.sector}")
else:
    print("No solution found")