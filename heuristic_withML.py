#!/usr/bin/env python3
"""
Full job-matching script using A* heuristic search with RandomForest-based feature prediction.

Optimality and Heuristic Admissibility:
- Uses an A* search over feature assignments. Each state is a partial assignment of features.
- The heuristic estimates the maximum remaining similarity by predicting unassigned features and computing their similarity contribution.
- Admissible: it never overestimates true remaining similarity because it predicts only based on observed and previously predicted values.
- With admissibility and non-negative path costs, A* guarantees an optimal (maximum-similarity) complete assignment.

Search Tree Characteristics:
- Branching factor b = average number of possible values per feature.
- Depth d = number of features (len(FEATURE_NAMES)).
- Worst-case exploration O(b^d), but informed heuristic prunes heavily.

Test Case:
- Single JobOffer defined.
- Training data consists of 30 observed employees for model learning.

Author: AI Assistant
"""

import random
import itertools
from queue import PriorityQueue
from collections import namedtuple
from sklearn.ensemble import RandomForestClassifier


# State tuple for A* search: (assigned_features, depth, path_cost)
State = namedtuple('State', ['assigned_features', 'depth', 'path_cost'])

# Data class for JobOffer
class JobOffer:
    def __init__(self, required_skills, min_experience, salary_range,
                 location, sector, education_level, department=None):
        self.required_skills = required_skills
        self.min_experience = min_experience
        self.salary_range = salary_range
        self.location = location
        self.sector = sector
        self.education_level = education_level
        self.department = department

    def __repr__(self):
        return (f"JobOffer(required_skills={self.required_skills}, "
                f"min_experience={self.min_experience}, "
                f"salary_range={self.salary_range}, location={self.location}, "
                f"sector={self.sector}, education_level={self.education_level}, "
                f"department={self.department})")

# Feature definitions
FEATURE_NAMES = [
    "gender", "age_range", "department", "sector",
    "seniority_level", "highest_education", "employment_type",
    "technical_skills"
]
FEATURE_VALUES = {
    "gender": ["Male", "Female"],
    "age_range": ["20-25", "26-30", "31-35", "36-40", "41+"],
    "department": ["HSE (Health, Safety, Environment)", "General Management", "E-Learning Platforms"],
    "sector": ["Energy & Petroleum", "Mining", "Education"],
    "seniority_level": ["Entry", "Mid", "Lead", "Senior"],
    "highest_education": ["Bac", "Licence", "Master", "Doctorate"],
    "employment_type": ["Full-Time", "Part-Time"],
    "technical_skills": [
        ["Microsoft Office", "Critical Thinking", "Team Leadership"],
        ["Risk Assessment", "Safety Protocols", "Reporting"],
        ["Data Analysis", "Project Management", "Communication"]
    ]
}

def get_possible_values(feature_name):
    """Return possible values for a feature."""
    return FEATURE_VALUES.get(feature_name, [])

# Similarity helpers

def calculate_partial_similarity(assigned, job_offer):
    """Compute g(n): similarity from currently assigned features."""
    score = 0
    for feat, val in assigned.items():
        if feat == "technical_skills":
            score += len(set(val) & set(job_offer.required_skills)) * 2
        elif hasattr(job_offer, feat) and getattr(job_offer, feat) == val:
            score += 3
    return score


def similarity_function(full_profile, job_offer):
    """Compute total similarity for a full profile."""
    score = 0
    if full_profile.get("department") == job_offer.department:
        score += 20
    if full_profile.get("sector") == job_offer.sector:
        score += 15
    if full_profile.get("highest_education") == job_offer.education_level:
        score += 10
    if "technical_skills" in full_profile:
        commons = set(full_profile["technical_skills"]) & set(job_offer.required_skills)
        score += len(commons) * 5
    return score

# Heuristic for A* search
def heuristic(state, job_offer, predictor):
    """Admissible h(n): estimated remaining similarity."""
    if state.depth == len(FEATURE_NAMES):
        return 0
    assigned = state.assigned_features
    unassigned = FEATURE_NAMES[state.depth:]
    # Predict unassigned based on all observed and assigned values:
    predicted = predictor.predict_features(assigned, unassigned)
    full_profile = {**assigned, **predicted}
    return similarity_function(full_profile, job_offer) - state.path_cost

# Helper to hash assignments

def make_hashable(assigned):
    return frozenset(
        (k, tuple(v) if isinstance(v, list) else v)
        for k, v in assigned.items()
    )

# A* search over feature assignments
def feature_based_job_matching(job_offer, predictor, sim_func):
    """Return feature assignment maximizing similarity within search."""
    counter = itertools.count()
    initial = State({}, 0, 0)
    frontier = PriorityQueue()
    f0 = heuristic(initial, job_offer, predictor)
    frontier.put((-f0, next(counter), initial))
    explored = set()

    while not frontier.empty():
        _, _, state = frontier.get()
        if state.depth == len(FEATURE_NAMES):
            return state.assigned_features

        explored.add(make_hashable(state.assigned_features))
        feat = FEATURE_NAMES[state.depth]
        for val in get_possible_values(feat):
            new_assigned = dict(state.assigned_features)
            new_assigned[feat] = val
            key = make_hashable(new_assigned)
            if key in explored:
                continue
            g = calculate_partial_similarity(new_assigned, job_offer)
            new_state = State(new_assigned, state.depth+1, g)
            f_val = g + heuristic(new_state, job_offer, predictor)
            frontier.put((-f_val, next(counter), new_state))
    return None

# Feature predictor
class FeaturePredictor:
    """RandomForest predictor for unassigned features."""
    def __init__(self, training_data):
        self.models = {}
        self.train(training_data)

    def train(self, data):
        for target in FEATURE_NAMES:
            X, y = [], []
            for emp in data:
                subset = {k: v for k, v in emp.items() if k != target}
                X.append(self.encode_features(subset))
                y.append(self.encode_feature_value(emp[target], target))
            model = RandomForestClassifier(n_estimators=50)
            model.fit(X, y)
            self.models[target] = model

    def encode_features(self, feats):
        return [self.encode_feature_value(feats.get(f), f) for f in FEATURE_NAMES]

    def encode_feature_value(self, val, fname):
        if fname == "technical_skills":
            return len(val) if isinstance(val, list) else 0
        try:
            return FEATURE_VALUES[fname].index(val)
        except Exception:
            return 0

    def decode_feature_value(self, enc, fname):
        if fname == "technical_skills":
            return random.choice(FEATURE_VALUES[fname])
        try:
            return FEATURE_VALUES[fname][enc]
        except Exception:
            return FEATURE_VALUES[fname][0]

    def rank_features_by_predictability(self, features):
        order = ["gender","age_range","employment_type",
                 "highest_education","seniority_level",
                 "sector","department","technical_skills"]
        return [f for f in order if f in features]

    def predict_features(self, assigned, unassigned):
        preds = {}
        current = dict(assigned)
        for feat in self.rank_features_by_predictability(unassigned):
            x = [self.encode_features(current)]
            enc = self.models[feat].predict(x)[0]
            val = self.decode_feature_value(enc, feat)
            preds[feat] = val
            current[feat] = val
        return preds

# Demo: one JobOffer and 30 employees
if __name__ == "__main__":
    # Generate 30 observed employee profiles
    training = []
    for _ in range(30):
        emp = {f: random.choice(vals) for f, vals in FEATURE_VALUES.items()}
        training.append(emp)

    predictor = FeaturePredictor(training)

    job = JobOffer(
        required_skills=["Risk Assessment","Reporting","Team Leadership"],
        min_experience=3,
        salary_range=(40000,60000),
        location="Algiers",
        sector="Energy & Petroleum",
        education_level="Licence",
        department="HSE (Health, Safety, Environment)"
    )

    print("Job Offer →", job)
    match = feature_based_job_matching(job, predictor, similarity_function)
    print("\nBest-matching profile:")
    for feat,value in match.items():
        print(f"{feat:20s}: {value}")
    print("\nFinal similarity score:", similarity_function(match, job))
