# PP-WA-Sync
## Usage
1. Clone repository
1. Add wa-key file with WA API key in it
1. Configure paypalrestdk in paypalfunctions.py
1. Install virtual environment and require packages: `pipenv install`
1. Activate virtual environment: `pipenv shell`
1. Parse WA audit log to populate db with link between WA ID and PP Recurring Profile ID: `python get_links.py`
1. Periodically get recent transactions for active Reccurring Profiles and create payments in WA: `python associate_payments.py`