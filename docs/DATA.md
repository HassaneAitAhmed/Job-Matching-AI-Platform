# Data quality report

- Jobs: 754 rows; seekers: 8124 rows; distance matrix: 48 cities.
- Jobs with no technical skills: 435 (58%). They cover whole sectors (Aerospace & Defense, Construction, E-Commerce, Healthcare, Mining, Pharmaceuticals, Public Sector, Renewable Energy, Telecommunications, Tourism & Hospitality, Transport & Logistics), so skills cannot be imputed from similar postings. The engine scores them as a weak skills match and the UI flags them.
- Distinct skill names: jobs 347, seekers 324, shared exactly: 45.
- Sector labels only in jobs: ['Finance']; only in seekers: ['Banking & Finance'].
- Contract labels jobs: ['Alternance', 'CDD', 'CDI', 'Freelance', 'Internship']; seekers: ['Alternance', 'CDD', 'CDI', 'Freelance', 'Stage'].
- Education labels jobs: ['Baccalaureate', 'Doctorat', "Ingénieur d'État", 'Licence', 'Master', 'No Formal Education']; seekers: ['Baccalaureate', 'Doctorat', "Ingénieur d'État", 'License', 'Master'].
- City spellings not literally in the distance matrix: ['Aïn Témouchent', 'Bejaïa', 'Béchar', 'Béjaïa', 'Djanet', 'Ghardaïa', 'In Salah', "M'sila", 'M’sila', 'Saïda', 'Sétif', 'Timimoun', 'Tébessa'].
- Seekers looking for an internship (Stage) with >10 years of experience: 1529.
- Internship seekers (Stage) holding a Doctorat: 440.
- Jobs whose department differs from their title: 73% (e.g. row 2: 'Cybersecurity Analyst' in department 'DevOps Engineer').

These patterns (random-looking title/department/skill combinations, implausible experience/contract pairs) suggest the datasets were synthetically generated or heavily augmented. Scores produced on them demonstrate the algorithms; they are not evidence of real-world matching quality.
