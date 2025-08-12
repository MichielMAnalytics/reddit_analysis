# Reddit Recruitment Hell Analyzer

Analyzes posts and comments from r/recruitinghell to identify top recruitment problems using OpenAI GPT.

## Features

- Fetches posts from r/recruitinghell with configurable lookback period
- Extracts all comments from posts
- Analyzes content using OpenAI GPT to identify recruitment problems
- Generates comprehensive reports in JSON format
- Progress tracking and batch processing for large datasets

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure API credentials:**
   - Copy `.env.example` to `.env`
   - Add your Reddit API credentials (get from https://www.reddit.com/prefs/apps)
   - Add your OpenAI API key (get from https://platform.openai.com)

   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

## Usage

### Basic usage (analyze last 30 days):
```bash
python main.py
```

### Specify lookback period:
```bash
# Last 7 days
python main.py --lookback 7

# Last 60 days
python main.py --lookback 60
```

### Limit number of posts:
```bash
# Analyze only 50 posts
python main.py --post-limit 50
```

### Save raw Reddit data:
```bash
python main.py --save-raw
```

### Analyze from saved data:
```bash
python main.py --load-from-file reddit_data_2024-01-15.json
```

### All options:
```bash
python main.py --help
```

## Output

The tool generates:
- `recruitment_problems_report.json` - Detailed analysis in JSON format with top problems, themes, and recommendations

## Example Output

The analysis identifies problems such as:
- Ghost jobs and fake postings
- Unrealistic job requirements
- Poor communication from recruiters
- Discriminatory practices
- Salary transparency issues
- Excessive interview rounds
- And more...

## API Rate Limits

- Reddit API: ~60 requests per minute
- OpenAI API: Depends on your tier

The tool handles rate limiting automatically with progress bars showing fetch status.
