import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import matplotlib
matplotlib.use('Agg') # Required for headless server environments
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
import re

class AnalyticsService:
    def __init__(self):
        # A benchmark Job Description for scoring. 
        # Configured for modern backend/full-stack enterprise development.
        self.benchmark_jd = """
        We are seeking a Software Developer with experience in backend and full-stack development. 
        The ideal candidate has strong proficiency in Java, Spring Boot, Python, and modern web frameworks 
        like React or Next.js. Experience integrating Artificial Intelligence, machine learning, 
        or Azure AI services into enterprise software is highly desirable. Strong system architecture, 
        API design, and database management skills are required.
        """

    def calculate_ats_score(self, resume_text: str) -> int:
        """Calculates ATS match percentage using TF-IDF and Cosine Similarity."""
        if not resume_text:
            return 0
            
        documents = [self.benchmark_jd, resume_text]
        vectorizer = TfidfVectorizer(stop_words='english')
        
        try:
            tfidf_matrix = vectorizer.fit_transform(documents)
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            # Convert to a percentage and scale slightly for realistic ATS behavior
            score = int(min(similarity * 150, 1.0) * 100) 
            return max(score, 10) # Minimum 10% for having a readable document
        except Exception as e:
            print(f"ATS Scoring Error: {e}")
            return 0

    def extract_top_skills(self, resume_text: str) -> dict:
        """Uses Pandas to count keyword frequency to estimate skill proficiency."""
        text = resume_text.lower()
        
        # Define enterprise tech keywords to look for
        skill_keywords = [
            'java', 'python', 'spring boot', 'react', 'next.js', 'javascript', 
            'sql', 'azure', 'ai', 'machine learning', 'c++', 'fastapi', 'backend'
        ]
        
        # Count frequencies
        frequencies = {skill: len(re.findall(r'\b' + re.escape(skill) + r'\b', text)) for skill in skill_keywords}
        
        # Convert to Pandas DataFrame for easy sorting
        df = pd.DataFrame(list(frequencies.items()), columns=['Skill', 'Frequency'])
        df = df[df['Frequency'] > 0].sort_values(by='Frequency', ascending=False).head(6)
        
        # Normalize scores to a 1-10 scale for the radar chart
        if not df.empty:
            max_freq = df['Frequency'].max()
            df['Score'] = (df['Frequency'] / max_freq) * 10
            # Ensure minimum visual score
            df['Score'] = df['Score'].apply(lambda x: max(x, 3.0))
            return dict(zip(df['Skill'], df['Score']))
        return {"General": 5}

    def generate_skill_radar_chart(self, resume_text: str) -> str:
        """Generates a Seaborn/Matplotlib radar chart and returns it as a Base64 string."""
        skills_data = self.extract_top_skills(resume_text)
        
        labels = [skill.title() for skill in skills_data.keys()]
        values = list(skills_data.values())
        
        # Close the plot for a circular radar chart
        values += values[:1]
        
        angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
        angles += angles[:1]

        plt.figure(figsize=(5, 5), facecolor='white')
        ax = plt.subplot(111, polar=True)
        
        # Plot styling
        ax.plot(angles, values, color='#4F46E5', linewidth=2, linestyle='solid')
        ax.fill(angles, values, color='#4F46E5', alpha=0.25)
        
        ax.set_theta_offset(np.pi / 2)
        ax.set_theta_direction(-1)
        ax.set_thetagrids(np.degrees(angles[:-1]), labels, fontsize=10, weight='bold')
        ax.set_ylim(0, 10)
        ax.set_yticks([]) # Hide radial grid values
        ax.spines['polar'].set_visible(False)
        
        # Convert plot to Base64 image
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', transparent=True)
        plt.close()
        buf.seek(0)
        
        return base64.b64encode(buf.read()).decode('utf-8')