# Ai-project
job matching Ai project
# Heuristic
- Start with two datasets: job offers and job seekers
- For each pair, assign a matching score based on:
  - Skills required by the offer
  - Skills existing in the seeker
- Store results in a matrix where:
  - Columns = Jobs
  - Rows = Seekers
- State representation: Pair from matrix
- Initial state: Pair with highest score
- Each depth represents a job
- Goal state: All jobs assigned to best available seeker
- Child nodes: New job with all unassigned seekers
- Path selection: Choose node with highest cumulative score
- Final result: Path from root to leaf containing all matches