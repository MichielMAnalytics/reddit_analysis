#!/usr/bin/env python3

import click
import json
from datetime import datetime
from reddit_fetcher import RedditFetcher
from openai_analyzer import OpenAIAnalyzer
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()


def validate_environment():
    """Check if required environment variables are set."""
    required_vars = [
        "REDDIT_CLIENT_ID",
        "REDDIT_CLIENT_SECRET",
        "OPENAI_API_KEY"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("Error: Missing required environment variables:")
        for var in missing_vars:
            print(f"  - {var}")
        print("\nPlease copy .env.example to .env and fill in your API credentials.")
        exit(1)


@click.command()
@click.option('--lookback', '-l', default=30, help='Number of days to look back (default: 30)')
@click.option('--post-limit', '-p', default=None, type=int, help='Maximum number of posts to fetch (default: all)')
@click.option('--comments-per-post', '-c', default=50, help='Maximum comments per post (default: 50)')
@click.option('--save-raw', '-s', is_flag=True, help='Save raw Reddit data to JSON file')
@click.option('--load-from-file', '-f', type=str, help='Load Reddit data from existing JSON file instead of fetching')
@click.option('--output', '-o', default='recruitment_problems_report', help='Output filename prefix (default: recruitment_problems_report)')
def main(lookback, post_limit, comments_per_post, save_raw, load_from_file, output):
    """
    Fetch posts from r/recruitinghell and analyze recruitment problems using GPT.
    
    Examples:
        # Fetch last 7 days of posts
        python main.py --lookback 7
        
        # Fetch last 30 days, limit to 100 posts, save raw data
        python main.py --lookback 30 --post-limit 100 --save-raw
        
        # Analyze from previously saved data
        python main.py --load-from-file reddit_data_2024-01-15.json
    """
    print("🔍 Reddit Recruitment Hell Analyzer")
    print("=" * 50)
    
    # Validate environment
    validate_environment()
    
    # Step 1: Get Reddit data
    if load_from_file:
        print(f"Loading Reddit data from {load_from_file}...")
        try:
            with open(load_from_file, 'r', encoding='utf-8') as f:
                posts = json.load(f)
            print(f"Loaded {len(posts)} posts from file")
        except FileNotFoundError:
            print(f"Error: File {load_from_file} not found")
            exit(1)
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON in {load_from_file}")
            exit(1)
    else:
        # Fetch from Reddit
        print(f"Fetching posts from last {lookback} days...")
        fetcher = RedditFetcher()
        
        try:
            posts = fetcher.fetch_all_content(
                lookback_days=lookback,
                post_limit=post_limit,
                max_comments_per_post=comments_per_post
            )
        except Exception as e:
            print(f"Error fetching Reddit data: {e}")
            print("Make sure your Reddit API credentials are correct in .env")
            exit(1)
        
        # Optionally save raw data
        if save_raw and posts:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
            raw_filename = f"reddit_data_{timestamp}.json"
            with open(raw_filename, 'w', encoding='utf-8') as f:
                json.dump(posts, f, indent=2, ensure_ascii=False)
            print(f"Raw Reddit data saved to {raw_filename}")
    
    if not posts:
        print("No posts found for the specified period.")
        exit(0)
    
    # Display summary statistics
    print("\n📊 Data Summary:")
    print(f"  Total posts: {len(posts)}")
    total_comments = sum(len(post['comments']) for post in posts)
    print(f"  Total comments: {total_comments}")
    
    # Calculate date range
    timestamps = [post['created_utc'] for post in posts]
    if timestamps:
        oldest = datetime.fromtimestamp(min(timestamps))
        newest = datetime.fromtimestamp(max(timestamps))
        print(f"  Date range: {oldest.strftime('%Y-%m-%d')} to {newest.strftime('%Y-%m-%d')}")
    
    # Step 2: Analyze with OpenAI
    print("\n🤖 Analyzing recruitment problems with GPT...")
    analyzer = OpenAIAnalyzer()
    
    try:
        analysis = analyzer.analyze_recruitment_problems(posts)
        
        # Save results
        output_json = f"{output}.json"
        analyzer.generate_report(analysis, output_json)
        
        # Display top findings
        if "top_problems" in analysis:
            print("\n🎯 Top Recruitment Problems Identified:")
            for i, problem in enumerate(analysis["top_problems"][:5], 1):
                print(f"\n{i}. {problem.get('title', 'Unknown')}")
                print(f"   {problem.get('description', '')[:150]}...")
        
        print(f"\n✅ Analysis complete! Check {output_json} for full results.")
        
    except Exception as e:
        print(f"Error during OpenAI analysis: {e}")
        print("Make sure your OpenAI API key is correct in .env")
        exit(1)


if __name__ == "__main__":
    main()