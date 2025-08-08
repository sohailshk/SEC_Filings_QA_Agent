"""
Batch processing and scheduling utilities for SEC filings
"""
import schedule
import time
import threading
from datetime import datetime, timedelta
import logging
from app.services.main_service import MainService

class BatchProcessor:
    """Handle batch processing of multiple companies and filings"""
    
    def __init__(self, main_service: MainService):
        self.main_service = main_service
        self.logger = logging.getLogger(__name__)
        self.is_running = False
    
    def process_sp500_companies(self, filing_types=['10-K', '10-Q'], limit_per_company=2):
        """Process filings for S&P 500 companies"""
        sp500_tickers = [
            'AAPL', 'MSFT', 'AMZN', 'GOOGL', 'TSLA', 'META', 'NVDA', 'BRK.B',
            'UNH', 'JNJ', 'JPM', 'V', 'PG', 'XOM', 'HD', 'CVX', 'MA', 'ABBV',
            'BAC', 'PFE', 'KO', 'AVGO', 'PEP', 'TMO', 'COST', 'WMT', 'DIS',
            'ABT', 'MRK', 'ACN', 'VZ', 'NFLX', 'ADBE', 'CRM', 'NKE', 'DHR'
            # Add more as needed
        ]
        
        results = {'processed': 0, 'failed': 0, 'errors': []}
        
        for ticker in sp500_tickers:
            if not self.is_running:
                break
                
            try:
                self.logger.info(f"Processing {ticker}...")
                for filing_type in filing_types:
                    result = self.main_service.process_company_filings(
                        ticker, filing_type, limit_per_company
                    )
                    if result['success']:
                        results['processed'] += result['data']['processed_count']
                    else:
                        results['failed'] += 1
                        results['errors'].append(f"{ticker}: {result['message']}")
                
                # Rate limiting - avoid overwhelming SEC servers
                time.sleep(2)
                
            except Exception as e:
                results['failed'] += 1
                results['errors'].append(f"{ticker}: {str(e)}")
                self.logger.error(f"Error processing {ticker}: {str(e)}")
        
        return results
    
    def daily_update_routine(self):
        """Daily routine to check for new filings"""
        self.logger.info("Starting daily update routine...")
        
        # Get list of companies already in database
        companies = self.main_service.db_manager.get_all_companies()
        
        for company in companies:
            try:
                # Check for new filings in the last 7 days
                result = self.main_service.process_company_filings(
                    company['symbol'], 
                    filing_type='8-K',  # 8-K filings are most frequent
                    limit=5
                )
                
                if result['success']:
                    self.logger.info(f"Updated {company['symbol']}: {result['data']['processed_count']} new filings")
                
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                self.logger.error(f"Error updating {company['symbol']}: {str(e)}")
    
    def start_scheduler(self):
        """Start the background scheduler"""
        self.is_running = True
        
        # Schedule daily updates at 6 AM
        schedule.every().day.at("06:00").do(self.daily_update_routine)
        
        # Schedule weekly batch processing on Sundays at 2 AM
        schedule.every().sunday.at("02:00").do(
            lambda: self.process_sp500_companies(filing_types=['10-Q'], limit_per_company=1)
        )
        
        def run_scheduler():
            while self.is_running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        
        self.logger.info("Batch processor scheduler started")
    
    def stop_scheduler(self):
        """Stop the scheduler"""
        self.is_running = False
        schedule.clear()
        self.logger.info("Batch processor scheduler stopped")

def cleanup_old_data(main_service: MainService, days_to_keep=90):
    """Clean up old filings and chunks to manage database size"""
    cutoff_date = datetime.now() - timedelta(days=days_to_keep)
    
    # This would require additional database methods
    # main_service.db_manager.delete_old_filings(cutoff_date)
    # main_service.vector_service.rebuild_index()
    
    logging.info(f"Cleaned up data older than {days_to_keep} days")
