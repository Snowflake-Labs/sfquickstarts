"""
Persona-based Q&A Generator using Vine Copula
Generates questions across domains with persona-specific response evaluation
"""
import numpy as np
from scipy import stats
from typing import List, Dict, Optional
import re
import requests
from dataclasses import dataclass
import textstat  # For Flesch reading ease

@dataclass
class PersonaQAPair:
    domain: str
    article: str
    question: str
    expected_answer: str
    category: str
    difficulty: str
    copula_sample: List[float]

# Persona definitions with prompts
PERSONAS = {
    "5th_grade": {
        "name": "Plain English (5th Grade)",
        "description": "Simple language, Flesch score 80-90",
        "prompt": """Respond using simple words a 10-year-old would understand.
Use short sentences (under 15 words each). Avoid jargon and big words.
Use everyday examples. Target Flesch Reading Ease: 80-90.""",
        "target_flesch": (80, 90)
    },
    "scholar": {
        "name": "Plain English Scholar",
        "description": "Academic prose with sophisticated vocabulary",
        "prompt": """Respond in academic prose with sophisticated vocabulary.
Use complex sentence structures with subordinate clauses.
Include qualifications, nuanced analysis, and scholarly context.
Reference relevant theoretical frameworks where appropriate.""",
        "target_flesch": (20, 50)
    },
    "compute": {
        "name": "Compute English (SQL)",
        "description": "SQL code and technical implementations",
        "prompt": """Respond with SQL code or technical implementations.
Prioritize executable, copy-paste ready Snowflake SQL.
Include schema context. Use CTEs for complex queries.
Add brief comments explaining the logic.""",
        "requires_code": True
    },
    "business": {
        "name": "Business English",
        "description": "Professional corporate/financial language",
        "prompt": """Respond in professional business language.
Focus on metrics, KPIs, ROI, and strategic implications.
Use executive summary format: Key Point → Supporting Data → Recommendation.
Consider compliance, risk factors, and stakeholder impact.""",
        "business_terms": ["ROI", "KPI", "stakeholder", "leverage", "synergy", 
                          "strategic", "metrics", "revenue", "margin", "compliance"]
    }
}

# Domain configurations
DOMAINS = {
    "shakespeare": {
        "name": "Shakespeare's Plays",
        "articles": [
            "Hamlet",
            "Macbeth", 
            "Romeo_and_Juliet",
            "A_Midsummer_Night%27s_Dream",
            "Othello"
        ],
        "context": "Shakespearean drama and literature"
    },
    "worldcup": {
        "name": "FIFA World Cup",
        "articles": [
            "FIFA_World_Cup",
            "2022_FIFA_World_Cup",
            "List_of_FIFA_World_Cup_finals"
        ],
        "context": "International football/soccer competition"
    },
    "finance": {
        "name": "Fortune 50 & 10-K Filings",
        "articles": [
            "Form_10-K",
            "Apple_Inc.",
            "Microsoft",
            "Amazon_(company)"
        ],
        "context": "Corporate finance and SEC filings"
    }
}


class PersonaVineCopula:
    """Vine Copula for persona and category dependencies."""
    
    def __init__(self, seed=42):
        np.random.seed(seed)
        self.personas = list(PERSONAS.keys())
        self.categories = ['factual', 'numerical', 'comparison', 'causal', 'list']
        
        # Persona correlations
        self.persona_tau = {
            ('5th_grade', 'scholar'): 0.7,  # Same content, different complexity
            ('scholar', 'compute'): 0.3,     # Different modality
            ('compute', 'business'): 0.5     # Both professional
        }
        
        # Category correlations
        self.category_tau = {
            ('factual', 'numerical'): 0.6,
            ('numerical', 'comparison'): 0.4,
            ('comparison', 'causal'): 0.5,
            ('causal', 'list'): 0.3
        }
    
    def _tau_to_rho(self, tau: float) -> float:
        return np.sin(np.pi * tau / 2)
    
    def sample_vine(self, n: int, items: List[str], tau_dict: Dict) -> np.ndarray:
        """Sample from D-vine copula."""
        d = len(items)
        samples = np.zeros((n, d))
        samples[:, 0] = np.random.uniform(0, 1, n)
        
        for j in range(1, d):
            pair = (items[j-1], items[j])
            tau = tau_dict.get(pair, 0.3)
            rho = self._tau_to_rho(tau)
            
            z_prev = stats.norm.ppf(np.clip(samples[:, j-1], 0.001, 0.999))
            z_cond_mean = rho * z_prev
            z_cond_std = np.sqrt(1 - rho**2)
            z_j = z_cond_mean + z_cond_std * np.random.randn(n)
            samples[:, j] = stats.norm.cdf(z_j)
        
        return samples
    
    def sample(self, n: int) -> Dict:
        """Sample both persona and category distributions."""
        persona_samples = self.sample_vine(n, self.personas, self.persona_tau)
        category_samples = self.sample_vine(n, self.categories, self.category_tau)
        
        return {
            "persona_samples": persona_samples,
            "category_samples": category_samples
        }
    
    def select_category(self, sample: np.ndarray) -> str:
        """Select category from copula sample."""
        probs = sample / sample.sum()
        idx = np.random.choice(len(self.categories), p=probs)
        return self.categories[idx]


class WikiFetcher:
    """Fetch Wikipedia articles."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'PersonaCompareBot/1.0 (Educational Research)'
        })
        self.cache = {}
    
    def fetch(self, title: str) -> Optional[Dict]:
        """Fetch article content."""
        if title in self.cache:
            return self.cache[title]
        
        api_url = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "titles": title,
            "prop": "extracts",
            "explaintext": "true",
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
                    result = {
                        "title": page_data.get("title", title),
                        "content": page_data.get("extract", "")
                    }
                    self.cache[title] = result
                    return result
            return None
        except Exception as e:
            print(f"  Error fetching {title}: {e}")
            return None


class FactExtractor:
    """Extract facts for Q&A generation."""
    
    def __init__(self):
        self.number_pattern = re.compile(r'\b(\d{1,4}(?:,\d{3})*(?:\.\d+)?|\d+(?:st|nd|rd|th)?)\b')
        self.year_pattern = re.compile(r'\b(1[0-9]{3}|20[0-2][0-9])\b')
        self.name_pattern = re.compile(r'\b([A-Z][a-z]+ [A-Z][a-z]+)\b')
    
    def extract(self, text: str, title: str) -> Dict:
        """Extract structured facts."""
        sentences = [s.strip() for s in re.split(r'[.!?]', text) if len(s.strip()) > 20]
        
        facts = {
            "title": title,
            "sentences": sentences[:30],
            "numbers": list(set(self.number_pattern.findall(text)))[:20],
            "years": list(set(self.year_pattern.findall(text)))[:10],
            "names": list(set(self.name_pattern.findall(text)))[:15],
            "summary": text[:400],
            "key_facts": []
        }
        
        # Extract key facts
        keywords = ['is', 'was', 'were', 'are', 'won', 'became', 'wrote', 'scored', 'reported']
        for sent in sentences[:20]:
            for kw in keywords:
                if f' {kw} ' in sent.lower():
                    parts = re.split(rf'\b{kw}\b', sent, maxsplit=1, flags=re.IGNORECASE)
                    if len(parts) == 2 and len(parts[0].strip()) > 5:
                        facts["key_facts"].append({
                            "sentence": sent,
                            "subject": parts[0].strip()[-60:],
                            "predicate": kw,
                            "object": parts[1].strip()[:120]
                        })
                        break
        
        return facts


class PersonaQAGenerator:
    """Generate Q&A with persona support."""
    
    def __init__(self, seed=42):
        self.copula = PersonaVineCopula(seed)
        self.fetcher = WikiFetcher()
        self.extractor = FactExtractor()
        self.domain_data = {}
        np.random.seed(seed)
    
    def load_domain(self, domain_key: str) -> int:
        """Load articles for a domain."""
        if domain_key not in DOMAINS:
            raise ValueError(f"Unknown domain: {domain_key}")
        
        domain = DOMAINS[domain_key]
        loaded = 0
        
        print(f"\nLoading domain: {domain['name']}")
        
        for article in domain["articles"]:
            print(f"  Fetching: {article}...")
            data = self.fetcher.fetch(article)
            
            if data and data.get("content"):
                facts = self.extractor.extract(data["content"], data["title"])
                
                if domain_key not in self.domain_data:
                    self.domain_data[domain_key] = {"articles": {}, "context": domain["context"]}
                
                self.domain_data[domain_key]["articles"][article] = facts
                loaded += 1
                print(f"    ✓ {len(facts['sentences'])} sentences, {len(facts['key_facts'])} facts")
            else:
                print(f"    ✗ Failed")
        
        return loaded
    
    def load_all_domains(self) -> Dict[str, int]:
        """Load all configured domains."""
        results = {}
        for domain_key in DOMAINS.keys():
            results[domain_key] = self.load_domain(domain_key)
        return results
    
    def generate_qa(self, n_questions: int = 20, domains: List[str] = None) -> List[PersonaQAPair]:
        """Generate Q&A pairs using Vine Copula."""
        if not self.domain_data:
            raise ValueError("No domains loaded. Call load_domain() first.")
        
        domains = domains or list(self.domain_data.keys())
        
        # Sample from copula
        samples = self.copula.sample(n_questions)
        
        qa_pairs = []
        
        for i in range(n_questions):
            # Select domain
            domain_idx = int(samples["persona_samples"][i, 0] * len(domains)) % len(domains)
            domain_key = domains[domain_idx]
            domain_data = self.domain_data[domain_key]
            
            # Select article
            articles = list(domain_data["articles"].keys())
            article_idx = int(samples["category_samples"][i, 0] * len(articles)) % len(articles)
            article = articles[article_idx]
            article_data = domain_data["articles"][article]
            
            # Select category
            category = self.copula.select_category(samples["category_samples"][i])
            
            # Generate question
            qa = self._generate_question(
                domain_key, article, article_data, category,
                samples["category_samples"][i]
            )
            
            if qa:
                qa_pairs.append(qa)
        
        return qa_pairs
    
    def _generate_question(self, domain: str, article: str, data: Dict, 
                          category: str, copula_sample: np.ndarray) -> Optional[PersonaQAPair]:
        """Generate a question based on domain and category."""
        
        question = ""
        answer = ""
        
        try:
            if category == "factual":
                if data["key_facts"]:
                    fact = data["key_facts"][np.random.randint(len(data["key_facts"]))]
                    question = f"What is {fact['subject']}?"
                    answer = fact["object"]
                else:
                    question = f"What is {data['title']}?"
                    answer = data["summary"][:200]
                    
            elif category == "numerical":
                if data["numbers"]:
                    num = data["numbers"][np.random.randint(len(data["numbers"]))]
                    for sent in data["sentences"]:
                        if num in sent:
                            question = f"What does the number {num} represent in {data['title']}?"
                            answer = sent
                            break
                    else:
                        question = f"What are important numbers related to {data['title']}?"
                        answer = ", ".join(data["numbers"][:5])
                else:
                    question = f"What dates or quantities are associated with {data['title']}?"
                    answer = data["summary"][:150]
                    
            elif category == "comparison":
                if len(data["names"]) >= 2:
                    idx1, idx2 = np.random.choice(len(data["names"]), size=2, replace=False)
                    n1, n2 = data["names"][idx1], data["names"][idx2]
                    question = f"How do {n1} and {n2} compare in the context of {data['title']}?"
                    answer = f"Both relate to {data['title']} in different ways."
                else:
                    question = f"What distinguishes {data['title']} from similar topics?"
                    answer = data["summary"][:200]
                    
            elif category == "causal":
                if data["key_facts"]:
                    fact = data["key_facts"][np.random.randint(len(data["key_facts"]))]
                    question = f"Why did {fact['subject']} {fact['predicate']} {fact['object'][:30]}?"
                    answer = fact["sentence"]
                else:
                    question = f"What factors led to {data['title']}'s significance?"
                    answer = data["summary"][:200]
                    
            elif category == "list":
                if data["names"]:
                    question = f"Who are the key figures associated with {data['title']}?"
                    answer = ", ".join(data["names"][:5])
                else:
                    question = f"What are the main components of {data['title']}?"
                    answer = data["summary"][:200]
            else:
                question = f"Describe {data['title']}."
                answer = data["summary"][:200]
            
            if not question:
                question = f"What is {data['title']}?"
                answer = data["summary"][:200]
            
            std = float(np.std(copula_sample))
            difficulty = "easy" if std < 0.2 else "medium" if std < 0.35 else "hard"
            
            return PersonaQAPair(
                domain=domain,
                article=article,
                question=question,
                expected_answer=answer[:300] if answer else "N/A",
                category=category,
                difficulty=difficulty,
                copula_sample=copula_sample.tolist()
            )
        except Exception as e:
            print(f"Error generating question: {e}")
            return None


def compute_flesch_score(text: str) -> float:
    """Compute Flesch Reading Ease score."""
    try:
        return textstat.flesch_reading_ease(text)
    except:
        return 50.0  # Default mid-range score


def check_sql_presence(text: str) -> bool:
    """Check if response contains SQL code."""
    sql_keywords = ['SELECT', 'FROM', 'WHERE', 'JOIN', 'GROUP BY', 'ORDER BY', 
                    'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'WITH']
    text_upper = text.upper()
    return any(kw in text_upper for kw in sql_keywords)


def count_business_terms(text: str) -> int:
    """Count business terminology in text."""
    terms = PERSONAS["business"]["business_terms"]
    text_lower = text.lower()
    return sum(1 for term in terms if term.lower() in text_lower)


def evaluate_persona_compliance(response: str, persona_key: str) -> Dict:
    """Evaluate how well response matches persona requirements."""
    result = {"persona": persona_key, "compliant": False}
    
    if persona_key == "5th_grade":
        flesch = compute_flesch_score(response)
        target_min, target_max = PERSONAS[persona_key]["target_flesch"]
        result["flesch_score"] = flesch
        result["compliant"] = flesch >= target_min
        result["score"] = min(100, max(0, flesch))
        
    elif persona_key == "scholar":
        flesch = compute_flesch_score(response)
        target_min, target_max = PERSONAS[persona_key]["target_flesch"]
        result["flesch_score"] = flesch
        result["compliant"] = flesch <= target_max
        result["score"] = min(100, max(0, 100 - flesch))  # Lower flesch = more complex
        
    elif persona_key == "compute":
        has_sql = check_sql_presence(response)
        result["has_sql"] = has_sql
        result["compliant"] = has_sql
        result["score"] = 100 if has_sql else 0
        
    elif persona_key == "business":
        biz_count = count_business_terms(response)
        result["business_terms"] = biz_count
        result["compliant"] = biz_count >= 2
        result["score"] = min(100, biz_count * 20)
    
    return result


# Convenience function for Streamlit
def generate_persona_qa(domains: List[str] = None, n_questions: int = 15, seed: int = 42) -> List[Dict]:
    """Generate Q&A pairs across domains."""
    generator = PersonaQAGenerator(seed)
    
    domains = domains or list(DOMAINS.keys())
    for domain in domains:
        if domain in DOMAINS:
            generator.load_domain(domain)
    
    if not generator.domain_data:
        raise ValueError("No domains loaded successfully")
    
    qa_pairs = generator.generate_qa(n_questions, domains)
    
    return [
        {
            "domain": qa.domain,
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
    print("Testing Persona Q&A Generator")
    print("=" * 60)
    
    try:
        qa_pairs = generate_persona_qa(n_questions=6)
        
        print(f"\nGenerated {len(qa_pairs)} Q&A Pairs:")
        print("-" * 60)
        for i, qa in enumerate(qa_pairs, 1):
            print(f"\n{i}. [{qa['domain']}] [{qa['category']}] {qa['article']}")
            print(f"   Q: {qa['question']}")
            print(f"   A: {qa['expected_answer'][:80]}...")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
