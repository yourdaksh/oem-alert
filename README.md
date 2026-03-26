# OEM Vulnerability Alert Platform

A comprehensive platform for monitoring critical and high-severity vulnerabilities from major IT/OT hardware and software OEMs.

## Features

- **Automated Scraping**: Monitors 10+ OEM websites for new vulnerabilities
- **Real-time Dashboard**: Clean Streamlit interface for browsing and filtering
- **Email Alerts**: Customizable subscriptions based on OEM/product preferences
- **Analytics**: Charts and insights on vulnerability trends
- **Manual Scanning**: On-demand vulnerability checks
- **Modular Design**: Easy to add new OEMs and extend functionality

## Quick Start

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Initialize Database**
   ```bash
   python setup_database.py
   ```

3. **Configure Email Settings** (Optional)
   ```bash
   cp .env.example .env
   # Edit .env with your SMTP settings
   ```

4. **Run the Application**
   ```bash
   ./run.sh
   # Or manually: streamlit run app.py
   ```

5. **Access Dashboard**
   Open your browser to: http://localhost:8501

## 🤖 AI Features Setup

To use the **AI Analyst** feature:
1.  Get a free API key from [Google AI Studio](https://aistudio.google.com/).
2.  Add it to your `.env` file:
    ```
    GEMINI_API_KEY=your_api_key_here
    ```

## 💬 Slack Integration Setup

To use **Slack Alerts**:
1.  Create a [Incoming Webhook](https://api.slack.com/messaging/webhooks) in your Slack workspace.
2.  Go to the **Settings** page in the dashboard.
3.  Paste the Webhook URL and save.

## Setup Cron Job (Linux/macOS)

Add this to your crontab for hourly scanning:
```bash
0 * * * * cd /path/to/oem-alert && ./venv/bin/python run_scrapers.py
```

## Adding New OEMs

1. Create a new scraper class in `scrapers/`
2. Add configuration to `config/oems.yaml`
3. Register the scraper in `scrapers/__init__.py`

## Project Structure

```
oem-alert/
├── app.py                 # Main Streamlit application
├── config/               # Configuration files
│   ├── oems.yaml        # OEM definitions and URLs
│   └── database.py      # Database configuration
├── scrapers/            # OEM scraper modules
│   ├── __init__.py
│   ├── base.py         # Base scraper class
│   ├── microsoft.py    # Microsoft scraper
│   ├── cisco.py        # Cisco scraper
│   └── ...             # Other OEM scrapers
├── database/           # Database models and operations
│   ├── __init__.py
│   ├── models.py       # SQLAlchemy models
│   └── operations.py   # Database operations
├── email/              # Email notification system
│   ├── __init__.py
│   └── notifications.py
├── utils/              # Utility functions
│   ├── __init__.py
│   └── helpers.py
├── run_scrapers.py     # Main scraper runner
├── setup_database.py   # Database initialization
└── requirements.txt    # Python dependencies
```

## Configuration

### Email Settings
Create a `.env` file with your SMTP settings:
```
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USERNAME=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
```

### OEM Configuration
Edit `config/oems.yaml` to add new OEMs or modify existing ones.

## Usage

1. **Dashboard**: Browse vulnerabilities, filter by OEM/severity/date
2. **Manual Scan**: Click "Scan Now" to trigger immediate scraping
3. **Email Subscriptions**: Subscribe to alerts for specific OEMs/products
4. **Analytics**: View vulnerability trends and distributions

## Troubleshooting

- **Database Issues**: Run `python setup_database.py` to reinitialize
- **Scraping Errors**: Check OEM websites for changes in structure
- **Email Issues**: Verify SMTP settings in `.env` file
- **Performance**: Adjust scraping frequency in cron job

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add your OEM scraper
4. Test thoroughly
5. Submit a pull request

## License

MIT License - see LICENSE file for details
