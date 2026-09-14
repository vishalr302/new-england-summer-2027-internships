import re

CATEGORY_RULES = {
    'AI / Machine Learning': r'machine learning|\bAI\b|artificial intelligence|deep learning|\bNLP\b',
    'Data Science': r'data scien',
    'Statistics / Analytics': r'statistic|analytic|data analyst|quantitative|business intelligence|business insights|data management|data solutions|trading analyst',
    'Software Engineering': r'software|developer|full.stack|front.end|back.end|compiler|data engineer|\bSWE\b',
    'Scientific Computing / Research': r'research|scientific|computational|simulation|bioinformatics',
    'Product Management': r'product (?:management|manager)|technical product',
    'Cybersecurity': r'cyber|security',
    'Hardware / Engineering': r'hardware|electrical|mechanical|robotic|firmware|semiconductor|engineer|\bFPGA\b|\bGPU\b|physical design|analog design|design verification|functional validation|design for test|packaging|device modell',
    'General Technology': r'technology|technical|\bIT\b|systems|cloud|devops|computing',
}


def categorize(title):
    tags = [name for name, pattern in CATEGORY_RULES.items() if re.search(pattern, title, re.I)]
    return (tags or ['Other'])[0], tags


def categorize_job(job):
    category, tags = categorize(job['title'])
    if category != 'Other':
        return category, tags
    if re.search(r'human resources|\bHR\b|accounting|finance|marketing|sales|legal|sustainability|logistics', job['title'], re.I):
        return 'Other', []
    description = job.get('description', '')
    if re.search(r'software|machine learning|data scien|data analy|cybersecurity|computer science|robotics|semiconductor|\bFPGA\b|computational', description, re.I):
        return categorize(description)
    return 'Other', []
