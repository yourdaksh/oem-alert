# Vulnerability Scrapper

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

2. **Configure Database** (Choose one)
   
   **Option A: SQLite (Default - Simple Setup)**
   ```bash
   # No configuration needed, uses SQLite by default
   ```
   
   **Option B: Supabase PostgreSQL (Recommended for Production)**
   ```bash
   cp env.example .env
   # Edit .env and set DATABASE_TYPE=supabase
   # Add your Supabase credentials (see SUPABASE_SETUP.md)
   ```

3. **Initialize Database**
   ```bash
   python setup_database.py
   ```

4. **Configure Email Settings** (Optional)
   ```bash
   cp env.example .env
   # Edit .env with your SMTP settings
   ```

5. **Run the Application**
   ```bash
   streamlit run app.py
   ```

6. **Access Dashboard**
   Open your browser to: http://localhost:8501
   
   **Login Credentials:**
   - If using Supabase: Sign up with email/password or use existing account
   - If using SQLite: Username: `admin`, Password: `admin123`

## Setup Cron Job (Linux/macOS)

Add this to your crontab for hourly scanning:
```bash
0 * * * * cd /path/to/oem-alert && python run_scrapers.py
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

### Database Configuration

**SQLite (Default)**
- No configuration needed
- Database file: `vulnerability_alerts.db`

**Supabase PostgreSQL**
- See [SUPABASE_SETUP.md](SUPABASE_SETUP.md) for detailed instructions
- Set `DATABASE_TYPE=supabase` in `.env`
- Requires Supabase project credentials

### Email Settings
Create a `.env` file with your SMTP settings:
```
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USERNAME=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
```

### Authentication

**SQLite Mode:**
- Default credentials: Username: `admin`, Password: `admin123`

**Supabase Mode:**
- User sign-up and login via email/password
- Secure session management
- Password reset functionality

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
