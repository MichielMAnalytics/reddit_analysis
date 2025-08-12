import openai
from typing import List, Dict
import json
from tqdm import tqdm
import os
from dotenv import load_dotenv

load_dotenv()


class OpenAIAnalyzer:
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
    def analyze_recruitment_problems(self, posts: List[Dict], batch_size: int = 10) -> Dict:
        """
        Analyze posts and comments to identify top recruitment problems.
        
        Args:
            posts: List of post dictionaries with comments
            batch_size: Number of posts to analyze in each batch
        
        Returns:
            Dictionary with analysis results
        """
        print(f"Analyzing {len(posts)} posts for recruitment problems...")
        
        # Process posts in batches to manage token limits
        all_problems = []
        
        for i in tqdm(range(0, len(posts), batch_size), desc="Analyzing batches"):
            batch = posts[i:i + batch_size]
            batch_analysis = self._analyze_batch(batch)
            if batch_analysis:
                all_problems.extend(batch_analysis)
        
        # Get final summary of all problems
        final_analysis = self._summarize_problems(all_problems)
        
        return final_analysis
    
    def _prepare_content_for_analysis(self, posts: List[Dict]) -> str:
        """Prepare post content for GPT analysis."""
        content_parts = []
        
        for post in posts:
            post_content = f"POST: {post['title']}\n"
            if post['selftext']:
                post_content += f"BODY: {post['selftext']}\n"
            
            # Add top comments
            if post['comments']:
                post_content += "TOP COMMENTS:\n"
                for comment in post['comments'][:5]:  # Top 5 comments
                    post_content += f"- {comment['body'][:200]}...\n"
            
            content_parts.append(post_content)
        
        return "\n---\n".join(content_parts)
    
    def _analyze_batch(self, posts: List[Dict]) -> List[Dict]:
        """Analyze a batch of posts."""
        content = self._prepare_content_for_analysis(posts)
        
        prompt = """Analyze these Reddit posts from r/recruitinghell and identify the main recruitment problems people are complaining about.

For each problem identified, provide:
1. Problem title (short, descriptive)
2. Description (2-3 sentences)
3. Frequency (how often it appears)
4. Example quotes or situations

Focus on concrete, specific problems rather than general complaints.

Content to analyze:
{content}

Return your analysis as a JSON array of problems.""".format(content=content[:8000])  # Limit content length
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert at analyzing recruitment and hiring practices. Extract specific, actionable problems from Reddit posts."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            return result.get('problems', [])
            
        except Exception as e:
            print(f"Error analyzing batch: {e}")
            return []
    
    def _summarize_problems(self, all_problems: List[Dict]) -> Dict:
        """Create final summary of all identified problems."""
        if not all_problems:
            return {"error": "No problems identified"}
        
        problems_text = json.dumps(all_problems, indent=2)
        
        prompt = """Given this list of recruitment problems identified from Reddit posts, create a comprehensive summary.

Group similar problems together and rank them by frequency/severity.

Provide:
1. Top 10 most common recruitment problems (ranked)
2. Key themes and patterns
3. Specific examples for each problem
4. Brief recommendations for job seekers

Problems list:
{problems}

Format as a structured JSON response with clear categories.""".format(problems=problems_text[:10000])
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert at synthesizing and summarizing recruitment industry problems."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            print(f"Error creating final summary: {e}")
            return {"error": str(e)}
    
    def generate_report(self, analysis: Dict, output_file: str = "recruitment_problems_report.json"):
        """Save analysis results to a JSON file."""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
        
        print(f"Report saved to {output_file}")