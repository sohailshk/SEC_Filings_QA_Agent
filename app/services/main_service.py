"""
Main Service Integration Module

This module integrates all services (SEC API, Database, Vector DB, Document Processing, Q&A)
into a cohesive system for processing SEC filings and answering questions.

Best Practices Followed:
- Service orchestration with clear data flow
- Error handling and transaction management
- Logging and monitoring at each step
- Modular design for easy testing and maintenance
"""

import logging
from typing import Dict, List, Any, Optional
import os
from datetime import datetime

# Import our custom services
from .sec_api_service import SECAPIService, SECAPIError
from .vector_service import VectorDatabaseService
from .document_processor import DocumentProcessor
from .qa_service import QAService
from ..models.database import DatabaseManager

# Setup logging for this module
logger = logging.getLogger(__name__)

class SECFilingsService:
    """
    Main service class that orchestrates all SEC filings operations.
    
    This service provides high-level methods for:
    - Processing SEC filings from ticker symbols
    - Storing and indexing documents
    - Answering questions about filings
    - Managing the complete data pipeline
    """
    
    def __init__(self, config):
        """
        Initialize the main SEC filings service with all dependencies.
        
        Args:
            config: Configuration object with all required settings
        """
        self.config = config
        
        # Initialize all services
        logger.info("Initializing SEC Filings Service")
        
        # SEC API service for fetching filings
        self.sec_api = SECAPIService(
            api_key=config.SEC_API_KEY,
            base_url=config.SEC_API_BASE_URL
        )
        
        # Database manager for metadata storage
        self.db_manager = DatabaseManager(config.DATABASE_PATH)
        
        # Vector database for semantic search
        self.vector_service = VectorDatabaseService(
            vector_db_path=config.VECTOR_DB_PATH,
            embedding_model=config.EMBEDDING_MODEL
        )
        
        # Document processor for text extraction and chunking
        self.document_processor = DocumentProcessor(
            chunk_size=config.CHUNK_SIZE,
            chunk_overlap=config.CHUNK_OVERLAP
        )
        
        # Q&A service using Gemini
        self.qa_service = QAService(
            gemini_api_key=config.GEMINI_API_KEY,
            model_name=config.GEMINI_MODEL
        )
        
        logger.info("SEC Filings Service initialized successfully")
    
    def process_company_filings(self, ticker: str, filing_type: str = "8-K", 
                               limit: int = 5) -> Dict[str, Any]:
        """
        Process recent filings for a company from SEC API to local storage.
        
        Args:
            ticker (str): Company ticker symbol (e.g., 'AAPL')
            filing_type (str): Type of filing to process (10-K, 10-Q, 8-K)
            limit (int): Maximum number of filings to process
            
        Returns:
            Dict[str, Any]: Processing results with statistics
        """
        logger.info(f"Processing {filing_type} filings for {ticker}")
        
        try:
            # Step 1: Get company information
            company_info = self.sec_api.get_company_info(ticker)
            
            # Step 2: Store/update company in database
            company_id = self.db_manager.insert_company(
                ticker=ticker,
                company_name=company_info.get('name', ticker),
                cik=company_info.get('cik'),
                sector=company_info.get('sector'),
                industry=company_info.get('industry')
            )
            
            # Step 3: Search for recent filings
            filings = self.sec_api.search_filings(
                ticker=ticker,
                filing_type=filing_type,
                limit=limit
            )
            
            processed_filings = []
            total_chunks = 0
            
            # Step 4: Process each filing
            for filing in filings:
                try:
                    result = self.process_single_filing(filing, company_id)
                    processed_filings.append(result)
                    total_chunks += result.get('num_chunks', 0)
                    
                except Exception as e:
                    logger.error(f"Failed to process filing {filing.get('accessionNumber', 'Unknown')}: {e}")
                    continue
            
            # Step 5: Save vector index to disk
            self.vector_service.save_index()
            
            # Step 6: Compile results
            results = {
                'ticker': ticker,
                'company_id': company_id,
                'filing_type': filing_type,
                'filings_found': len(filings),
                'filings_processed': len(processed_filings),
                'total_chunks_created': total_chunks,
                'processed_filings': processed_filings,
                'processing_timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Successfully processed {len(processed_filings)} filings for {ticker}")
            return results
            
        except SECAPIError as e:
            logger.error(f"SEC API error processing {ticker}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error processing {ticker}: {e}")
            raise
    
    def process_single_filing(self, filing_data: Dict[str, Any], company_id: int) -> Dict[str, Any]:
        """
        Process a single SEC filing through the complete pipeline.
        
        Args:
            filing_data (Dict[str, Any]): Filing metadata from SEC API
            company_id (int): Company ID in database
            
        Returns:
            Dict[str, Any]: Processing results for this filing
        """
        accession_number = filing_data.get('accessionNumber', 'Unknown')
        logger.info(f"Processing filing: {accession_number}")
        
        # Step 1: Store filing metadata in database
        filing_id = self.db_manager.insert_filing(
            company_id=company_id,
            filing_type=filing_data.get('formType', 'Unknown'),
            filing_date=filing_data.get('filedAt', ''),
            accession_number=accession_number,
            document_url=filing_data.get('linkToFilingDetails', ''),
            period_end_date=filing_data.get('periodOfReport'),
            html_content=None  # Will be filled later
        )
        
        if not filing_id:
            logger.warning(f"Filing {accession_number} already exists, skipping")
            return {'accession_number': accession_number, 'status': 'skipped', 'num_chunks': 0}
        
        try:
            # Step 2: Update processing status
            self.db_manager.update_filing_processing_status(filing_id, 'processing')
            
            # Step 3: Download filing content
            # Based on SEC API documentation, prioritize linkToTxt (plain text) over HTML
            filing_urls = [
                filing_data.get('linkToTxt', ''),           # Plain text - most reliable
                filing_data.get('linkToFilingDetails', ''), # HTML content - often blocked
                filing_data.get('linkToHtml', '')           # Index page - last resort
            ]
            
            html_content = None
            last_error = None
            
            for url_field, filing_url in [('linkToTxt', filing_urls[0]), 
                                         ('linkToFilingDetails', filing_urls[1]), 
                                         ('linkToHtml', filing_urls[2])]:
                if not filing_url:
                    continue
                    
                try:
                    logger.debug(f"Attempting download from {url_field}: {filing_url}")
                    html_content = self.sec_api.get_filing_content(filing_url)
                    logger.info(f"Successfully downloaded content from {url_field}")
                    break
                except Exception as e:
                    last_error = e
                    logger.warning(f"Failed to download from {url_field}: {e}")
                    continue
            
            if not html_content:
                raise Exception(f"Failed to download filing content from any source. Last error: {last_error}")
            
            # Step 4: Process document (extract text, create chunks)
            filing_metadata = {
                'filing_id': filing_id,
                'company_id': company_id,
                'ticker': filing_data.get('ticker', ''),
                'filing_type': filing_data.get('formType', ''),
                'filing_date': filing_data.get('filedAt', ''),
                'accession_number': accession_number
            }
            
            processed_doc = self.document_processor.process_sec_filing(html_content, filing_metadata)
            
            # Step 5: Store document chunks in vector database
            chunk_texts = [chunk['text'] for chunk in processed_doc['chunks']]
            chunk_metadata = [chunk['metadata'] for chunk in processed_doc['chunks']]
            
            # Check if we have any chunks to process
            if not chunk_texts:
                logger.warning(f"No chunks extracted from filing {accession_number}. Filing may be empty or have processing issues.")
                self.db_manager.update_filing_processing_status(filing_id, 'completed', 'No content extracted')
                return {
                    'accession_number': accession_number,
                    'filing_id': filing_id,
                    'status': 'completed_no_content',
                    'num_chunks': 0,
                    'processing_stats': processed_doc['processing_stats']
                }
            
            vector_ids = self.vector_service.add_documents(chunk_texts, chunk_metadata)
            
            # Step 6: Store chunks in database with vector IDs
            for i, (chunk_data, vector_id) in enumerate(zip(processed_doc['chunks'], vector_ids)):
                self.db_manager.insert_document_chunk(
                    filing_id=filing_id,
                    chunk_index=i,
                    chunk_text=chunk_data['text'],
                    section_name=chunk_data['metadata'].get('section_name'),
                    vector_id=str(vector_id),
                    metadata=chunk_data['metadata']
                )
            
            # Step 7: Update filing with processed content and completion status
            self.db_manager.update_filing_processing_status(
                filing_id,
                'completed',
                processed_doc['cleaned_text']
            )
            
            logger.info(f"Successfully processed filing {accession_number} with {len(processed_doc['chunks'])} chunks")
            
            return {
                'accession_number': accession_number,
                'filing_id': filing_id,
                'status': 'completed',
                'num_chunks': len(processed_doc['chunks']),
                'processing_stats': processed_doc['processing_stats']
            }
            
        except Exception as e:
            # Update status to failed
            self.db_manager.update_filing_processing_status(filing_id, 'failed')
            logger.error(f"Failed to process filing {accession_number}: {e}")
            raise
    
    def answer_question(self, question: str, ticker: str = None, 
                       filing_type: str = None, k: int = 5) -> Dict[str, Any]:
        """
        Answer a question using SEC filings with semantic search.
        
        Args:
            question (str): Question to answer
            ticker (str): Optional company ticker to filter by
            filing_type (str): Optional filing type to filter by
            k (int): Number of similar chunks to retrieve
            
        Returns:
            Dict[str, Any]: Answer with sources and metadata
        """
        logger.info(f"Answering question for ticker={ticker}: {question[:100]}...")
        
        try:
            # Step 1: Prepare metadata filter
            metadata_filter = {}
            if ticker:
                metadata_filter['ticker'] = ticker.upper()
            if filing_type:
                metadata_filter['filing_type'] = filing_type
            
            # Step 2: Search for relevant document chunks
            similar_chunks = self.vector_service.search_similar(
                query_text=question,
                k=k,
                metadata_filter=metadata_filter if metadata_filter else None
            )
            
            if not similar_chunks:
                return {
                    'question': question,
                    'answer': "I couldn't find any relevant information in the available SEC filings to answer your question.",
                    'sources': [],
                    'ticker_filter': ticker,
                    'filing_type_filter': filing_type
                }
            
            # Step 3: Get company information for context
            company_info = {}
            if ticker:
                company_info = self.db_manager.get_company_by_ticker(ticker) or {}
            
            # Step 4: Generate answer using Q&A service
            answer_response = self.qa_service.answer_question(
                question=question,
                relevant_chunks=similar_chunks,
                company_info=company_info
            )
            
            # Step 5: Add filtering information to response
            answer_response['filters_applied'] = {
                'ticker': ticker,
                'filing_type': filing_type,
                'chunks_retrieved': len(similar_chunks)
            }
            
            logger.info("Successfully generated answer with sources")
            return answer_response
            
        except Exception as e:
            logger.error(f"Failed to answer question: {e}")
            return self.qa_service.create_error_response(question, str(e))
    
    def get_company_summary(self, ticker: str) -> Dict[str, Any]:
        """
        Get a comprehensive summary of a company's recent filings.
        
        Args:
            ticker (str): Company ticker symbol
            
        Returns:
            Dict[str, Any]: Company summary with recent filings info
        """
        logger.info(f"Getting company summary for {ticker}")
        
        try:
            # Get company information
            company_info = self.db_manager.get_company_by_ticker(ticker)
            if not company_info:
                return {'error': f'Company {ticker} not found in database'}
            
            # Get recent filings
            filings = self.db_manager.get_filings_by_company(company_info['id'], limit=10)
            
            # Get database stats
            db_stats = self.db_manager.get_database_stats()
            vector_stats = self.vector_service.get_stats()
            
            return {
                'company_info': company_info,
                'recent_filings': filings,
                'total_filings': len(filings),
                'database_stats': db_stats,
                'vector_stats': vector_stats,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get company summary for {ticker}: {e}")
            return {'error': str(e)}
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Get comprehensive system status and statistics.
        
        Returns:
            Dict[str, Any]: System status information
        """
        try:
            db_stats = self.db_manager.get_database_stats()
            vector_stats = self.vector_service.get_stats()
            processor_stats = self.document_processor.get_processing_stats()
            
            return {
                'database': db_stats,
                'vector_database': vector_stats,
                'document_processor': processor_stats,
                'services_initialized': True,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get system status: {e}")
            return {'error': str(e), 'services_initialized': False}
    
    def search_filings(self, query: str, ticker: str = None, k: int = 10) -> List[Dict[str, Any]]:
        """
        Search for relevant filing chunks using semantic search.
        
        Args:
            query (str): Search query
            ticker (str): Optional ticker filter
            k (int): Number of results to return
            
        Returns:
            List[Dict[str, Any]]: Search results with metadata
        """
        logger.info(f"Searching filings with query: {query[:100]}...")
        
        try:
            metadata_filter = {'ticker': ticker.upper()} if ticker else None
            
            results = self.vector_service.search_similar(
                query_text=query,
                k=k,
                metadata_filter=metadata_filter
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to search filings: {e}")
            return []
