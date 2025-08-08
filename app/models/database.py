"""
Database Models for SEC Filings QA Agent

This module defines the SQLite database schema and models for storing
SEC filing metadata and document chunks.

Best Practices Followed:
- Normalized database design with proper relationships
- Indexing for performance on common queries
- Data validation and constraints
- Clear documentation of each table's purpose
"""

import sqlite3
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import os

# Setup logging for this module
logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    Manages SQLite database operations for SEC filings data.
    
    This class handles:
    - Database initialization and schema creation
    - CRUD operations for companies, filings, and document chunks
    - Database connections and transaction management
    """
    
    def __init__(self, db_path: str):
        """
        Initialize database manager with SQLite database path.
        
        Args:
            db_path (str): Path to SQLite database file
        """
        self.db_path = db_path
        self.ensure_directory_exists()
        self.init_database()
        logger.info(f"Database manager initialized with path: {db_path}")
    
    def ensure_directory_exists(self):
        """Create database directory if it doesn't exist."""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
            logger.info(f"Created database directory: {db_dir}")
    
    def get_connection(self) -> sqlite3.Connection:
        """
        Get SQLite database connection with optimized settings.
        
        Returns:
            sqlite3.Connection: Database connection with foreign keys enabled
        """
        conn = sqlite3.connect(self.db_path)
        # Enable foreign key constraints for data integrity
        conn.execute("PRAGMA foreign_keys = ON")
        # Use row factory for easier data access
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """
        Initialize database schema with all required tables.
        Creates tables if they don't exist.
        """
        logger.info("Initializing database schema")
        
        with self.get_connection() as conn:
            # Create companies table for basic company information
            conn.execute("""
                CREATE TABLE IF NOT EXISTS companies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticker VARCHAR(10) NOT NULL UNIQUE,
                    company_name VARCHAR(255) NOT NULL,
                    cik VARCHAR(20) UNIQUE,
                    sector VARCHAR(100),
                    industry VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create index on ticker for fast lookups
            conn.execute("CREATE INDEX IF NOT EXISTS idx_companies_ticker ON companies(ticker)")
            
            # Create filings table for SEC filing metadata
            conn.execute("""
                CREATE TABLE IF NOT EXISTS filings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_id INTEGER NOT NULL,
                    filing_type VARCHAR(20) NOT NULL,
                    filing_date DATE NOT NULL,
                    period_end_date DATE,
                    accession_number VARCHAR(30) UNIQUE NOT NULL,
                    document_url TEXT NOT NULL,
                    html_content TEXT,
                    processed_content TEXT,
                    processing_status VARCHAR(20) DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (company_id) REFERENCES companies(id)
                )
            """)
            
            # Create indices for common query patterns
            conn.execute("CREATE INDEX IF NOT EXISTS idx_filings_company_id ON filings(company_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_filings_type_date ON filings(filing_type, filing_date)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_filings_accession ON filings(accession_number)")
            
            # Create document_chunks table for text chunks with embeddings
            conn.execute("""
                CREATE TABLE IF NOT EXISTS document_chunks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filing_id INTEGER NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    section_name VARCHAR(100),
                    chunk_text TEXT NOT NULL,
                    chunk_size INTEGER NOT NULL,
                    vector_id VARCHAR(100),
                    metadata_json TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (filing_id) REFERENCES filings(id),
                    UNIQUE(filing_id, chunk_index)
                )
            """)
            
            # Create indices for chunk retrieval
            conn.execute("CREATE INDEX IF NOT EXISTS idx_chunks_filing_id ON document_chunks(filing_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_chunks_vector_id ON document_chunks(vector_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_chunks_section ON document_chunks(section_name)")
            
            conn.commit()
            logger.info("Database schema initialized successfully")
    
    def insert_company(self, ticker: str, company_name: str, cik: str = None, 
                      sector: str = None, industry: str = None) -> int:
        """
        Insert or update company information.
        
        Args:
            ticker (str): Company ticker symbol
            company_name (str): Full company name
            cik (str): Central Index Key from SEC
            sector (str): Company sector
            industry (str): Company industry
            
        Returns:
            int: Company ID (primary key)
        """
        with self.get_connection() as conn:
            try:
                # Try to insert new company
                cursor = conn.execute("""
                    INSERT INTO companies (ticker, company_name, cik, sector, industry)
                    VALUES (?, ?, ?, ?, ?)
                """, (ticker, company_name, cik, sector, industry))
                
                company_id = cursor.lastrowid
                logger.info(f"Inserted new company: {ticker} (ID: {company_id})")
                
            except sqlite3.IntegrityError:
                # Company already exists, update it
                conn.execute("""
                    UPDATE companies 
                    SET company_name = ?, cik = ?, sector = ?, industry = ?, 
                        updated_at = CURRENT_TIMESTAMP
                    WHERE ticker = ?
                """, (company_name, cik, sector, industry, ticker))
                
                # Get the existing company ID
                cursor = conn.execute("SELECT id FROM companies WHERE ticker = ?", (ticker,))
                company_id = cursor.fetchone()[0]
                logger.info(f"Updated existing company: {ticker} (ID: {company_id})")
            
            return company_id
    
    def insert_filing(self, company_id: int, filing_type: str, filing_date: str,
                     accession_number: str, document_url: str, 
                     period_end_date: str = None, html_content: str = None) -> int:
        """
        Insert SEC filing metadata.
        
        Args:
            company_id (int): Company ID foreign key
            filing_type (str): Type of filing (10-K, 10-Q, 8-K, etc.)
            filing_date (str): Date filing was submitted
            accession_number (str): Unique SEC accession number
            document_url (str): URL to the filing document
            period_end_date (str): End date of reporting period
            html_content (str): Raw HTML content of filing
            
        Returns:
            int: Filing ID (primary key)
        """
        with self.get_connection() as conn:
            try:
                cursor = conn.execute("""
                    INSERT INTO filings 
                    (company_id, filing_type, filing_date, period_end_date, 
                     accession_number, document_url, html_content)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (company_id, filing_type, filing_date, period_end_date,
                      accession_number, document_url, html_content))
                
                filing_id = cursor.lastrowid
                logger.info(f"Inserted filing: {filing_type} for company {company_id} (ID: {filing_id})")
                return filing_id
                
            except sqlite3.IntegrityError as e:
                logger.error(f"Failed to insert filing {accession_number}: {e}")
                # Return existing filing ID if duplicate
                cursor = conn.execute("SELECT id FROM filings WHERE accession_number = ?", 
                                    (accession_number,))
                result = cursor.fetchone()
                return result[0] if result else None
    
    def insert_document_chunk(self, filing_id: int, chunk_index: int, chunk_text: str,
                            section_name: str = None, vector_id: str = None,
                            metadata: Dict[str, Any] = None) -> int:
        """
        Insert document chunk for vector search.
        
        Args:
            filing_id (int): Filing ID foreign key
            chunk_index (int): Index of chunk within document
            chunk_text (str): Text content of chunk
            section_name (str): Name of document section (Item 1, Item 2, etc.)
            vector_id (str): ID for vector database lookup
            metadata (Dict): Additional metadata as JSON
            
        Returns:
            int: Chunk ID (primary key)
        """
        metadata_json = json.dumps(metadata) if metadata else None
        
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT OR REPLACE INTO document_chunks 
                (filing_id, chunk_index, section_name, chunk_text, chunk_size, 
                 vector_id, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (filing_id, chunk_index, section_name, chunk_text, 
                  len(chunk_text), vector_id, metadata_json))
            
            chunk_id = cursor.lastrowid
            logger.debug(f"Inserted chunk {chunk_index} for filing {filing_id} (ID: {chunk_id})")
            return chunk_id
    
    def get_company_by_ticker(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Get company information by ticker symbol.
        
        Args:
            ticker (str): Company ticker symbol
            
        Returns:
            Dict[str, Any]: Company information or None if not found
        """
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM companies WHERE ticker = ?", (ticker,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_filings_by_company(self, company_id: int, filing_type: str = None,
                              limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get filings for a company with optional filtering.
        
        Args:
            company_id (int): Company ID
            filing_type (str): Filter by filing type (optional)
            limit (int): Maximum number of results
            
        Returns:
            List[Dict[str, Any]]: List of filing records
        """
        with self.get_connection() as conn:
            if filing_type:
                cursor = conn.execute("""
                    SELECT * FROM filings 
                    WHERE company_id = ? AND filing_type = ?
                    ORDER BY filing_date DESC LIMIT ?
                """, (company_id, filing_type, limit))
            else:
                cursor = conn.execute("""
                    SELECT * FROM filings 
                    WHERE company_id = ?
                    ORDER BY filing_date DESC LIMIT ?
                """, (company_id, limit))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_document_chunks(self, filing_id: int) -> List[Dict[str, Any]]:
        """
        Get all document chunks for a filing.
        
        Args:
            filing_id (int): Filing ID
            
        Returns:
            List[Dict[str, Any]]: List of document chunks
        """
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM document_chunks 
                WHERE filing_id = ?
                ORDER BY chunk_index
            """, (filing_id,))
            
            chunks = []
            for row in cursor.fetchall():
                chunk = dict(row)
                # Parse metadata JSON if present
                if chunk['metadata_json']:
                    chunk['metadata'] = json.loads(chunk['metadata_json'])
                chunks.append(chunk)
            
            return chunks
    
    def update_filing_processing_status(self, filing_id: int, status: str, 
                                      processed_content: str = None):
        """
        Update filing processing status and content.
        
        Args:
            filing_id (int): Filing ID
            status (str): Processing status (pending, processing, completed, failed)
            processed_content (str): Cleaned/processed text content
        """
        with self.get_connection() as conn:
            if processed_content:
                conn.execute("""
                    UPDATE filings 
                    SET processing_status = ?, processed_content = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (status, processed_content, filing_id))
            else:
                conn.execute("""
                    UPDATE filings 
                    SET processing_status = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (status, filing_id))
            
            logger.info(f"Updated filing {filing_id} status to: {status}")
    
    def get_database_stats(self) -> Dict[str, int]:
        """
        Get basic database statistics for monitoring.
        
        Returns:
            Dict[str, int]: Statistics including record counts
        """
        with self.get_connection() as conn:
            stats = {}
            
            # Count companies
            cursor = conn.execute("SELECT COUNT(*) FROM companies")
            stats['companies'] = cursor.fetchone()[0]
            
            # Count filings
            cursor = conn.execute("SELECT COUNT(*) FROM filings")
            stats['filings'] = cursor.fetchone()[0]
            
            # Count processed filings
            cursor = conn.execute("SELECT COUNT(*) FROM filings WHERE processing_status = 'completed'")
            stats['processed_filings'] = cursor.fetchone()[0]
            
            # Count chunks
            cursor = conn.execute("SELECT COUNT(*) FROM document_chunks")
            stats['document_chunks'] = cursor.fetchone()[0]
            
            logger.info(f"Database stats: {stats}")
            return stats
