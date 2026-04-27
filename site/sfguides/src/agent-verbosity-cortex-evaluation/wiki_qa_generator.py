"""
Wikipedia Q&A Generator using Vine Copula
Generates synthetic questions from Wikipedia articles with dependency modeling
"""
import numpy as np
from scipy import stats
from typing import List, Dict, Tuple, Optional
import re
import requests
from dataclasses import dataclass

@dataclass
class QAPair:
    article: str
    question: str
    expected_answer: str
    category: str
    difficulty: str
    copula_sample: List[float]

class VineCopula:
    """
    D-Vine Copula for modeling question category dependencies.
    Models: factual -> numerical -> comparison -> causal -> list
    """
    
    def __init__(self, seed=42):
        np.random.seed(seed)
        # Copula parameters (Kendall's tau correlations)
        self.tau = {
            ('factual', 'numerical'): 0.6,
            ('numerical', 'comparison'): 0.4,
            ('comparison', 'causal'): 0.5,
            ('causal', 'list'): 0.3
        }
        self.categories = ['factual', 'numerical', 'comparison', 'causal', 'list']
    
    def _tau_to_rho(self, tau: float) -> float:
        """Convert Kendall's tau to Pearson correlation for Gaussian copula."""
        return np.sin(np.pi * tau / 2)
    
    def sample(self, n: int) -> np.ndarray:
        """
        Sample from D-vine copula.
        Returns array of shape (n, 5) with uniform marginals.
        """
        d = len(self.categories)
        samples = np.zeros((n, d))
        
        # First variable: uniform
        samples[:, 0] = np.random.uniform(0, 1, n)
        
        # Sequential sampling using conditional distributions
        for j in range(1, d):
            # Get correlation with previous variable
            pair = (self.categories[j-1], self.categories[j])
            tau = self.tau.get(pair, 0.3)
            rho = self._tau_to_rho(tau)
            
            # Conditional Gaussian copula
            z_prev = stats.norm.ppf(np.clip(samples[:, j-1], 0.001, 0.999))
            z_cond_mean = rho * z_prev
            z_cond_std = np.sqrt(1 - rho**2)
            z_j = z_cond_mean + z_cond_std * np.random.randn(n)
            samples[:, j] = stats.norm.cdf(z_j)
        
        return samples
    
    def sample_category(self, n: int) -> List[str]:
        """Sample question categories based on copula structure."""
        samples = self.sample(n)
        # Use max probability dimension as category
        categories = []
        for row in samples:
            # Weight by copula values
            probs = row / row.sum()
            cat_idx = np.random.choice(len(self.categories), p=probs)
            categories.append(self.categories[cat_idx])
        return categories


class WikipediaFetcher:
    """Fetch and parse Wikipedia articles."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'ModelComparisonBot/1.0 (Educational Research)'
        })
    
    def fetch_article(self, title: str) -> Optional[Dict]:
        """Fetch article using Wikipedia API."""
        # Try the standard MediaWiki API
        api_url = "https://en.wikipedia.org/w/api.php"
        
        params = {
            "action": "query",
            "titles": title,
            "prop": "extracts|info",
            "explaintext": "true",
            "exintro": "false",
            "format": "json",
            "redirects": "1"
        }
        
        try:
            response = self.session.get(api_url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            pages = data.get("query", {}).get("pages", {})
            for page_id, page_data in pages.items():
                if page_id != "-1" and "extract" in page_data:
                    return {
                        "title": page_data.get("title", title),
                        "content": page_data.get("extract", ""),
                        "pageid": page_id
                    }
            
            print(f"  Warning: No content found for {title}")
            return None
            
        except Exception as e:
            print(f"  Error fetching {title}: {e}")
            return None
    
    def fetch_summary(self, title: str) -> Optional[Dict]:
        """Fetch just the summary/intro."""
        api_url = "https://en.wikipedia.org/w/api.php"
        
        params = {
            "action": "query",
            "titles": title,
            "prop": "extracts",
            "exintro": "true",
            "explaintext": "true",
            "format": "json",
            "redirects": "1"
        }
        
        try:
            response = self.session.get(api_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            pages = data.get("query", {}).get("pages", {})
            for page_id, page_data in pages.items():
                if page_id != "-1":
                    return {
                        "title": page_data.get("title", title),
                        "summary": page_data.get("extract", "")[:500]
                    }
            return None
        except:
            return None


class FactExtractor:
    """Extract facts from Wikipedia content."""
    
    def __init__(self):
        self.number_pattern = re.compile(r'\b(\d{1,4}(?:,\d{3})*(?:\.\d+)?|\d+(?:st|nd|rd|th)?)\b')
        self.year_pattern = re.compile(r'\b(1[0-9]{3}|20[0-2][0-9])\b')
        self.name_pattern = re.compile(r'\b([A-Z][a-z]+ [A-Z][a-z]+)\b')
    
    def extract_facts(self, text: str, title: str) -> Dict:
        """Extract structured facts from text."""
        sentences = [s.strip() for s in re.split(r'[.!?]', text) if len(s.strip()) > 20]
        
        facts = {
            "title": title,
            "sentences": sentences[:30],
            "numbers": list(set(self.number_pattern.findall(text)))[:20],
            "years": list(set(self.year_pattern.findall(text)))[:10],
            "names": list(set(self.name_pattern.findall(text)))[:15],
            "key_facts": self._extract_key_facts(sentences)
        }
        return facts
    
    def _extract_key_facts(self, sentences: List[str]) -> List[Dict]:
        """Extract key factual statements."""
        key_facts = []
        keywords = ['is', 'was', 'were', 'are', 'became', 'won', 'created', 'founded', 'launched', 'written', 'directed']
        
        for sent in sentences:
            for kw in keywords:
                if f' {kw} ' in sent.lower():
                    parts = re.split(rf'\b{kw}\b', sent, maxsplit=1, flags=re.IGNORECASE)
                    if len(parts) == 2 and len(parts[0].strip()) > 5:
                        key_facts.append({
                            "sentence": sent,
                            "subject": parts[0].strip()[-60:],
                            "predicate": kw,
                            "object": parts[1].strip()[:120]
                        })
                        break
        return key_facts[:15]


class QuestionTemplates:
    """Question templates for each category."""
    
    TEMPLATES = {
        "factual": [
            "What is {subject}?",
            "Who created {subject}?",
            "What does {subject} refer to?",
            "Describe {subject}.",
            "What is the significance of {subject}?"
        ],
        "numerical": [
            "How many {subject}?",
            "What year did {event} occur?",
            "How long did {subject} last?",
            "What was the count of {subject}?",
            "In what year was {subject}?"
        ],
        "comparison": [
            "How does {subject1} compare to {subject2}?",
            "What is the difference between {subject1} and {subject2}?",
            "Which is more significant: {subject1} or {subject2}?",
            "Compare {subject1} and {subject2}."
        ],
        "causal": [
            "Why did {event} happen?",
            "What caused {event}?",
            "What led to {subject}?",
            "Why is {subject} important?",
            "What was the reason for {event}?"
        ],
        "list": [
            "List the main {subject}.",
            "What are the key {subject}?",
            "Name the {subject}.",
            "What {subject} are there?",
            "Enumerate the {subject}."
        ]
    }
    
    @classmethod
    def get_template(cls, category: str) -> str:
        templates = cls.TEMPLATES.get(category, cls.TEMPLATES["factual"])
        return np.random.choice(templates)


class WikiQAGenerator:
    """Main class for generating Q&A from Wikipedia using Vine Copula."""
    
    def __init__(self, seed=42):
        self.copula = VineCopula(seed)
        self.fetcher = WikipediaFetcher()
        self.extractor = FactExtractor()
        self.articles_data = {}
        np.random.seed(seed)
    
    def load_articles(self, titles: List[str]) -> int:
        """Load and process Wikipedia articles. Returns count of loaded articles."""
        loaded = 0
        for title in titles:
            print(f"Loading: {title}...")
            article = self.fetcher.fetch_article(title)
            
            if article and article.get("content"):
                content = article["content"]
                facts = self.extractor.extract_facts(content, article["title"])
                
                # Get summary too
                summary = self.fetcher.fetch_summary(title)
                facts["summary"] = summary.get("summary", content[:300]) if summary else content[:300]
                facts["description"] = facts["summary"][:150]
                
                self.articles_data[title] = facts
                loaded += 1
                print(f"  ✓ Loaded {len(facts['sentences'])} sentences, {len(facts['key_facts'])} key facts")
            else:
                print(f"  ✗ Failed to load {title}")
        
        return loaded
    
    def generate_qa(self, n_questions: int = 20) -> List[QAPair]:
        """Generate Q&A pairs using Vine Copula sampling."""
        if not self.articles_data:
            raise ValueError("No articles loaded. Call load_articles() first.")
        
        # Sample from copula
        copula_samples = self.copula.sample(n_questions)
        categories = self.copula.sample_category(n_questions)
        
        qa_pairs = []
        articles = list(self.articles_data.keys())
        
        for i in range(n_questions):
            # Select article based on copula sample
            article_idx = int(copula_samples[i, 0] * len(articles)) % len(articles)
            article = articles[article_idx]
            article_data = self.articles_data[article]
            
            category = categories[i]
            
            # Generate question based on category and article data
            qa = self._generate_question(article, article_data, category, copula_samples[i])
            if qa:
                qa_pairs.append(qa)
        
        return qa_pairs
    
    def _generate_question(self, article: str, data: Dict, category: str, 
                          copula_sample: np.ndarray) -> Optional[QAPair]:
        """Generate a single question based on category."""
        
        template = QuestionTemplates.get_template(category)
        question = ""
        answer = ""
        
        try:
            if category == "factual":
                if data["key_facts"]:
                    fact = data["key_facts"][np.random.randint(len(data["key_facts"]))]
                    question = template.format(subject=fact["subject"])
                    answer = fact["object"]
                else:
                    question = f"What is {data['title']}?"
                    answer = data.get("summary", data.get("description", ""))[:200]
                    
            elif category == "numerical":
                if data["numbers"]:
                    num = data["numbers"][np.random.randint(len(data["numbers"]))]
                    # Find sentence containing this number
                    found = False
                    for sent in data["sentences"]:
                        if num in sent:
                            question = f"What is the significance of {num} in {data['title']}?"
                            answer = sent
                            found = True
                            break
                    if not found:
                        question = f"What numbers are significant in {data['title']}?"
                        answer = ", ".join(data["numbers"][:5])
                elif data["years"]:
                    question = f"What year is {data['title']} associated with?"
                    answer = data["years"][0]
                else:
                    question = f"What quantities or dates relate to {data['title']}?"
                    answer = data.get("summary", "")[:150]
                    
            elif category == "comparison":
                if len(data["names"]) >= 2:
                    idx1, idx2 = np.random.choice(len(data["names"]), size=2, replace=False)
                    names = [data["names"][idx1], data["names"][idx2]]
                    question = template.format(subject1=names[0], subject2=names[1])
                    answer = f"Both {names[0]} and {names[1]} relate to {data['title']}"
                else:
                    question = f"What makes {data['title']} unique?"
                    answer = data.get("description", data.get("summary", ""))[:200]
                    
            elif category == "causal":
                if data["key_facts"]:
                    fact = data["key_facts"][np.random.randint(len(data["key_facts"]))]
                    question = f"Why is {fact['subject']} significant to {data['title']}?"
                    answer = fact["sentence"]
                else:
                    question = f"Why is {data['title']} important?"
                    answer = data.get("summary", "")[:200]
                    
            elif category == "list":
                if data["names"]:
                    question = f"Who are the key figures in {data['title']}?"
                    answer = ", ".join(data["names"][:5])
                elif data["numbers"]:
                    question = f"What are the key numbers in {data['title']}?"
                    answer = ", ".join(str(n) for n in data["numbers"][:5])
                else:
                    question = f"What are the main aspects of {data['title']}?"
                    answer = data.get("summary", "")[:200]
            else:
                question = f"Tell me about {data['title']}"
                answer = data.get("summary", "")[:200]
            
            # Ensure we have valid Q&A
            if not question or not answer:
                question = f"What is {data['title']}?"
                answer = data.get("summary", data.get("description", "Information not available"))[:200]
            
            # Determine difficulty based on copula sample variance
            std = float(np.std(copula_sample))
            difficulty = "easy" if std < 0.2 else "medium" if std < 0.35 else "hard"
            
            return QAPair(
                article=article,
                question=question,
                expected_answer=answer[:300] if answer else "N/A",
                category=category,
                difficulty=difficulty,
                copula_sample=copula_sample.tolist()
            )
        except Exception as e:
            print(f"Error generating question for {article}/{category}: {e}")
            return None


# Convenience function for Streamlit
def generate_wiki_qa(articles: List[str], n_questions: int = 20, seed: int = 42) -> List[Dict]:
    """Generate Q&A pairs from Wikipedia articles."""
    generator = WikiQAGenerator(seed)
    loaded = generator.load_articles(articles)
    
    if loaded == 0:
        raise ValueError(f"Failed to load any articles. Tried: {articles}")
    
    qa_pairs = generator.generate_qa(n_questions)
    
    if not qa_pairs:
        raise ValueError("No Q&A pairs generated")
    
    return [
        {
            "article": qa.article,
            "question": qa.question,
            "expected_answer": qa.expected_answer,
            "category": qa.category,
            "difficulty": qa.difficulty,
            "copula_sample": qa.copula_sample
        }
        for qa in qa_pairs
    ]


if __name__ == "__main__":
    # Test with specified articles
    articles = [
        "The_Lord_of_the_Rings",
        "New_England_Patriots",
        "Apollo_program"
    ]
    
    print("Testing Wikipedia Q&A Generator")
    print("=" * 60)
    
    try:
        qa_pairs = generate_wiki_qa(articles, n_questions=10)
        
        print(f"\nGenerated {len(qa_pairs)} Q&A Pairs:")
        print("-" * 60)
        for i, qa in enumerate(qa_pairs, 1):
            print(f"\n{i}. [{qa['category']}] {qa['article']}")
            print(f"   Q: {qa['question']}")
            print(f"   A: {qa['expected_answer'][:100]}...")
    except Exception as e:
        print(f"Error: {e}")
