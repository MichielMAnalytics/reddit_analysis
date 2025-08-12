import praw
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from tqdm import tqdm
import os
from dotenv import load_dotenv

load_dotenv()


class RedditFetcher:
    def __init__(self):
        self.reddit = praw.Reddit(
            client_id=os.getenv("REDDIT_CLIENT_ID"),
            client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
            user_agent=os.getenv("REDDIT_USER_AGENT", "recruitment_hell_analyzer/1.0")
        )
        self.subreddit = self.reddit.subreddit("recruitinghell")
    
    def fetch_posts(self, lookback_days: int = 30, limit: Optional[int] = None) -> List[Dict]:
        """
        Fetch posts from r/recruitinghell within the specified lookback period.
        
        Args:
            lookback_days: Number of days to look back from current date
            limit: Maximum number of posts to fetch (None for all)
        
        Returns:
            List of post dictionaries with their data
        """
        posts = []
        cutoff_timestamp = (datetime.now() - timedelta(days=lookback_days)).timestamp()
        
        # Fetch posts using the 'new' sorting to get chronological order
        submission_generator = self.subreddit.new(limit=None)
        
        print(f"Fetching posts from the last {lookback_days} days...")
        
        for submission in tqdm(submission_generator, desc="Fetching posts"):
            # Check if post is within our time window
            if submission.created_utc < cutoff_timestamp:
                break
            
            # Skip if we've hit our limit
            if limit and len(posts) >= limit:
                break
            
            posts.append(self._extract_post_data(submission))
        
        print(f"Fetched {len(posts)} posts")
        return posts
    
    def _extract_post_data(self, submission) -> Dict:
        """Extract relevant data from a Reddit submission."""
        return {
            'id': submission.id,
            'title': submission.title,
            'author': str(submission.author) if submission.author else '[deleted]',
            'created_utc': submission.created_utc,
            'created_date': datetime.fromtimestamp(submission.created_utc).isoformat(),
            'score': submission.score,
            'num_comments': submission.num_comments,
            'selftext': submission.selftext,
            'url': submission.url,
            'permalink': f"https://reddit.com{submission.permalink}",
            'is_self': submission.is_self,
            'comments': []
        }
    
    def fetch_comments(self, posts: List[Dict], max_comments_per_post: int = 100) -> List[Dict]:
        """
        Fetch comments for a list of posts.
        
        Args:
            posts: List of post dictionaries
            max_comments_per_post: Maximum number of comments to fetch per post
        
        Returns:
            Updated posts with comments included
        """
        print(f"Fetching comments for {len(posts)} posts...")
        
        for post in tqdm(posts, desc="Fetching comments"):
            submission = self.reddit.submission(id=post['id'])
            submission.comments.replace_more(limit=0)  # Remove MoreComments objects
            
            comments = []
            comment_count = 0
            
            for comment in submission.comments.list():
                if comment_count >= max_comments_per_post:
                    break
                
                if hasattr(comment, 'body') and comment.body != '[deleted]':
                    comments.append({
                        'id': comment.id,
                        'author': str(comment.author) if comment.author else '[deleted]',
                        'body': comment.body,
                        'score': comment.score,
                        'created_utc': comment.created_utc,
                        'created_date': datetime.fromtimestamp(comment.created_utc).isoformat(),
                        'parent_id': comment.parent_id,
                        'is_submitter': comment.is_submitter
                    })
                    comment_count += 1
            
            post['comments'] = comments
        
        total_comments = sum(len(post['comments']) for post in posts)
        print(f"Fetched {total_comments} comments total")
        
        return posts
    
    def fetch_all_content(self, lookback_days: int = 30, post_limit: Optional[int] = None,
                         max_comments_per_post: int = 100) -> List[Dict]:
        """
        Fetch both posts and their comments in one call.
        
        Args:
            lookback_days: Number of days to look back
            post_limit: Maximum number of posts to fetch
            max_comments_per_post: Maximum comments per post
        
        Returns:
            List of posts with comments included
        """
        posts = self.fetch_posts(lookback_days, post_limit)
        if posts:
            posts = self.fetch_comments(posts, max_comments_per_post)
        return posts