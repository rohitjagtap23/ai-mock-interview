import re
SKILLS=['Java','Spring Boot','Spring','Spring Security','Spring Cloud','Microservices','REST APIs','REST','SQL','MySQL','PostgreSQL','Oracle','MongoDB','NoSQL','Docker','Kubernetes','Git','GitHub','Maven','Gradle','Jenkins','CI/CD','AWS','Azure','GCP','Kafka','Redis','React','ReactJS','Angular','JavaScript','TypeScript','HTML','CSS','GraphQL','Hibernate','JPA','JUnit','Mockito','Python','Data Structures','Algorithms','System Design','Agile','Scrum','Machine Learning','Pandas','NumPy','TensorFlow','PyTorch','Linux']
def extract_skills(text):
    if not text:return []
    low=text.lower(); out=[]
    for skill in SKILLS:
        if re.search(r'(?<![a-z0-9])'+re.escape(skill.lower())+r'(?![a-z0-9])',low): out.append(skill)
    return out
def analyze_jobs(jobs):
    freq={}
    for job in jobs or []:
        for skill in set(extract_skills(job.get('description',''))): freq[skill]=freq.get(skill,0)+1
    return [{'skill':s,'job_count':n} for s,n in sorted(freq.items(),key=lambda x:x[1],reverse=True)]
def get_top_skills(skills,limit=5):
    aliases={'Spring':'Spring Boot','REST':'REST APIs','ReactJS':'React'}; f={}
    for x in skills or []:
        s=aliases.get(x.get('skill'),x.get('skill','')); f[s]=f.get(s,0)+int(x.get('job_count',0))
    return [{'skill':s,'job_count':n} for s,n in sorted(f.items(),key=lambda x:x[1],reverse=True)[:limit]]
