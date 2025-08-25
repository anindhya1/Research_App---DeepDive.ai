# DeepDive.ai Research Platform

AI-powered research assistant that delivers comprehensive insights on any topic.

**[Live Demo](https://researchapp-deepdiveai-production.up.railway.app/)**

## Overview

DeepDive.ai uses AI agents to automatically research topics, generate detailed reports, and deliver results via web interface, PDF, and email. The system plans search strategies, gathers information from multiple sources, and synthesizes findings into professional reports.

## Features

- **Intelligent Research Planning**: AI develops optimal search strategies
- **Multi-Source Data Gathering**: Concurrent web searches across diverse sources
- **Professional Report Generation**: Detailed markdown reports with citations
- **PDF Export**: Downloadable reports with proper formatting
- **Email Distribution**: Automatic delivery of completed research
- **Real-time Updates**: Live progress streaming during research
- **Modern UI**: WebGL2 shader background with glassmorphism design

## Tech Stack

- **Backend**: Python 3.11, Flask, OpenAI Agents, Gunicorn + Gevent
- **Frontend**: Vanilla JavaScript, P5.js (WebGL2), Marked.js
- **Infrastructure**: Docker, Railway
- **APIs**: OpenAI GPT-4, SendGrid

## Quick Start

### Local Development

```bash
git clone https://github.com/anindhya1/Research_App---DeepDive.ai.git
cd Research_App---DeepDive.ai
pip install -r requirements.txt

# Add API keys to .env file
echo "OPENAI_API_KEY=your_key_here" > .env
echo "SENDGRID_API_KEY=your_key_here" >> .env

python app.py
```

### Docker Deployment

```bash
docker build -t deepdive-ai .
docker run -p 8000:8000 --env-file .env deepdive-ai
```

### Railway Deployment

1. Connect repository to Railway
2. Add environment variables: `OPENAI_API_KEY`, `SENDGRID_API_KEY`
3. Deploy automatically via Dockerfile

## Configuration

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key for AI agents | Yes |
| `SENDGRID_API_KEY` | SendGrid key for email delivery | No |
| `FLASK_ENV` | Environment (development/production) | No |

## API

### Research Endpoint
```http
POST /research
Content-Type: application/json

{"query": "Research topic"}
```
Returns Server-Sent Events stream with progress and results.

### Health Check
```http
GET /health
```

## Architecture

The system uses specialized AI agents:
- **Planner**: Develops search strategies
- **Search**: Executes web searches and summarizes results
- **Writer**: Creates comprehensive reports (1000+ words)
- **Download**: Converts reports to PDF
- **Email**: Formats and sends reports

## License

MIT License - see [LICENSE](LICENSE) file for details.
