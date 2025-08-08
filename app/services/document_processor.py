"""
Document Processing Pipeline for SEC Filings

This module handles the processing of SEC filings including:
- HTML parsing and text extraction
- Document chunking with fixed character count
- Metadata extraction and preservation
- Text cleaning and normalization

Best Practices Followed:
- Modular design with clear separation of concerns
- Comprehensive error handling and logging
- Configurable chunking strategies
- Preservation of document structure and metadata
"""

import re
import logging
from typing import List, Dict, Any, Tuple, Optional
from bs4 import BeautifulSoup
import html
from datetime import datetime

# Setup logging for this module
logger = logging.getLogger(__name__)

class DocumentProcessor:
    """
    Processes SEC filing documents for text extraction and chunking.
    
    This class handles:
    - HTML parsing and cleaning
    - Text extraction from SEC filings
    - Document chunking with overlap
    - Metadata extraction and preservation
    """
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Initialize document processor with chunking configuration.
        
        Args:
            chunk_size (int): Target size for text chunks in characters
            chunk_overlap (int): Number of characters to overlap between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Validate configuration
        if chunk_overlap >= chunk_size:
            raise ValueError("Chunk overlap must be less than chunk size")
        
        logger.info(f"Document processor initialized: chunk_size={chunk_size}, overlap={chunk_overlap}")
    
    def process_sec_filing(self, html_content: str, filing_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a complete SEC filing from HTML to chunks.
        
        Args:
            html_content (str): Raw HTML content of SEC filing
            filing_metadata (Dict[str, Any]): Metadata about the filing
            
        Returns:
            Dict[str, Any]: Processed document with chunks and metadata
        """
        logger.info(f"Processing SEC filing: {filing_metadata.get('accession_number', 'Unknown')}")
        
        try:
            # Step 1: Clean and extract text from HTML
            cleaned_text = self.extract_text_from_html(html_content)
            
            # Step 2: Extract sections if possible (SEC filings have standard structure)
            sections = self.extract_sec_sections(cleaned_text)
            
            # Step 3: Create chunks from the cleaned text
            chunks = self.create_text_chunks(cleaned_text, filing_metadata)
            
            # Step 4: Compile results
            processed_document = {
                'filing_metadata': filing_metadata,
                'cleaned_text': cleaned_text,
                'sections': sections,
                'chunks': chunks,
                'processing_stats': {
                    'original_html_length': len(html_content),
                    'cleaned_text_length': len(cleaned_text),
                    'num_sections': len(sections),
                    'num_chunks': len(chunks),
                    'processing_timestamp': datetime.now().isoformat()
                }
            }
            
            logger.info(f"Successfully processed filing into {len(chunks)} chunks")
            return processed_document
            
        except Exception as e:
            logger.error(f"Failed to process SEC filing: {e}")
            raise
    
    def extract_text_from_html(self, html_content: str) -> str:
        """
        Extract and clean text from SEC filing HTML.
        
        Args:
            html_content (str): Raw HTML content
            
        Returns:
            str: Cleaned text content
        """
        logger.debug("Extracting text from HTML content")
        
        try:
            # Parse HTML with BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Remove common SEC filing table headers and navigation elements
            for element in soup.find_all(['table'], {'class': ['tableFile', 'tableHeader']}):
                element.decompose()
            
            # Extract text
            text = soup.get_text()
            
            # Clean up the text
            text = self.clean_text(text)
            
            logger.debug(f"Extracted {len(text)} characters of text")
            return text
            
        except Exception as e:
            logger.error(f"Failed to extract text from HTML: {e}")
            # Fallback: try to strip HTML tags manually
            return self.fallback_text_extraction(html_content)
    
    def clean_text(self, text: str) -> str:
        """
        Clean and normalize extracted text.
        
        Args:
            text (str): Raw extracted text
            
        Returns:
            str: Cleaned and normalized text
        """
        # Decode HTML entities
        text = html.unescape(text)
        
        # Replace multiple whitespaces with single space
        text = re.sub(r'\s+', ' ', text)
        
        # Remove excessive line breaks
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        # Remove common SEC filing artifacts
        text = re.sub(r'Table of Contents', '', text, flags=re.IGNORECASE)
        text = re.sub(r'UNITED STATES\s+SECURITIES AND EXCHANGE COMMISSION', '', text, flags=re.IGNORECASE)
        
        return text
    
    def fallback_text_extraction(self, html_content: str) -> str:
        """
        Fallback method for text extraction using regex.
        
        Args:
            html_content (str): HTML content
            
        Returns:
            str: Extracted text
        """
        logger.warning("Using fallback text extraction method")
        
        # Remove script and style tags
        text = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove all HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Clean up
        text = self.clean_text(text)
        
        return text
    
    def extract_sec_sections(self, text: str) -> Dict[str, str]:
        """
        Extract standard SEC filing sections (Item 1, Item 2, etc.).
        
        Args:
            text (str): Cleaned text content
            
        Returns:
            Dict[str, str]: Dictionary mapping section names to content
        """
        logger.debug("Extracting SEC filing sections")
        
        sections = {}
        
        # Common SEC filing section patterns
        section_patterns = [
            (r'ITEM\s+1\.\s+BUSINESS', 'Item 1 - Business'),
            (r'ITEM\s+1A\.\s+RISK\s+FACTORS', 'Item 1A - Risk Factors'),
            (r'ITEM\s+2\.\s+PROPERTIES', 'Item 2 - Properties'),
            (r'ITEM\s+3\.\s+LEGAL\s+PROCEEDINGS', 'Item 3 - Legal Proceedings'),
            (r'ITEM\s+4\.\s+MINE\s+SAFETY', 'Item 4 - Mine Safety'),
            (r'ITEM\s+5\.\s+MARKET\s+FOR', 'Item 5 - Market for Securities'),
            (r'ITEM\s+6\.\s+SELECTED\s+FINANCIAL', 'Item 6 - Selected Financial Data'),
            (r'ITEM\s+7\.\s+MANAGEMENT\'S\s+DISCUSSION', 'Item 7 - MD&A'),
            (r'ITEM\s+8\.\s+FINANCIAL\s+STATEMENTS', 'Item 8 - Financial Statements'),
            (r'ITEM\s+9\.\s+CHANGES\s+IN\s+AND\s+DISAGREEMENTS', 'Item 9 - Changes and Disagreements'),
            (r'ITEM\s+10\.\s+DIRECTORS', 'Item 10 - Directors and Officers'),
            (r'ITEM\s+11\.\s+EXECUTIVE\s+COMPENSATION', 'Item 11 - Executive Compensation'),
            (r'ITEM\s+12\.\s+SECURITY\s+OWNERSHIP', 'Item 12 - Security Ownership'),
            (r'ITEM\s+13\.\s+CERTAIN\s+RELATIONSHIPS', 'Item 13 - Certain Relationships'),
            (r'ITEM\s+14\.\s+PRINCIPAL\s+ACCOUNTING', 'Item 14 - Principal Accounting'),
            (r'ITEM\s+15\.\s+EXHIBITS', 'Item 15 - Exhibits')
        ]
        
        try:
            for pattern, section_name in section_patterns:
                matches = list(re.finditer(pattern, text, re.IGNORECASE))
                if matches:
                    start_pos = matches[0].start()
                    
                    # Find the end position (start of next section or end of document)
                    end_pos = len(text)
                    for next_pattern, _ in section_patterns:
                        if pattern == next_pattern:
                            continue
                        next_matches = list(re.finditer(next_pattern, text[start_pos + 100:], re.IGNORECASE))
                        if next_matches:
                            candidate_end = start_pos + 100 + next_matches[0].start()
                            if candidate_end > start_pos:
                                end_pos = min(end_pos, candidate_end)
                    
                    section_content = text[start_pos:end_pos].strip()
                    sections[section_name] = section_content
                    
                    logger.debug(f"Extracted section: {section_name} ({len(section_content)} characters)")
            
            logger.info(f"Extracted {len(sections)} sections from SEC filing")
            
        except Exception as e:
            logger.error(f"Failed to extract sections: {e}")
        
        return sections
    
    def create_text_chunks(self, text: str, filing_metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Create overlapping text chunks from document text.
        
        Args:
            text (str): Document text to chunk
            filing_metadata (Dict[str, Any]): Metadata to attach to each chunk
            
        Returns:
            List[Dict[str, Any]]: List of text chunks with metadata
        """
        logger.debug(f"Creating chunks from text ({len(text)} characters)")
        
        chunks = []
        chunk_index = 0
        
        # Calculate step size (chunk_size - overlap)
        step_size = self.chunk_size - self.chunk_overlap
        
        for start_pos in range(0, len(text), step_size):
            end_pos = min(start_pos + self.chunk_size, len(text))
            chunk_text = text[start_pos:end_pos]
            
            # Skip very small chunks at the end
            if len(chunk_text.strip()) < 100:
                break
            
            # Try to break at sentence boundaries for better chunks
            chunk_text = self.optimize_chunk_boundaries(chunk_text)
            
            # Create chunk metadata
            chunk_metadata = {
                **filing_metadata,  # Include all filing metadata
                'chunk_index': chunk_index,
                'start_position': start_pos,
                'end_position': end_pos,
                'chunk_length': len(chunk_text),
                'section_name': self.identify_section(chunk_text),
                'chunk_type': 'text'
            }
            
            chunk = {
                'text': chunk_text,
                'metadata': chunk_metadata
            }
            
            chunks.append(chunk)
            chunk_index += 1
        
        logger.debug(f"Created {len(chunks)} text chunks")
        return chunks
    
    def optimize_chunk_boundaries(self, chunk_text: str) -> str:
        """
        Optimize chunk boundaries to break at sentence endings when possible.
        
        Args:
            chunk_text (str): Raw chunk text
            
        Returns:
            str: Optimized chunk text
        """
        # If chunk is already at optimal length, return as-is
        if len(chunk_text) <= self.chunk_size * 0.9:
            return chunk_text
        
        # Look for sentence endings near the end of the chunk
        search_start = max(0, len(chunk_text) - 200)  # Look in last 200 characters
        sentence_endings = []
        
        for match in re.finditer(r'[.!?]\s+', chunk_text[search_start:]):
            sentence_endings.append(search_start + match.end())
        
        # If we found sentence endings, use the last one
        if sentence_endings:
            optimal_end = sentence_endings[-1]
            return chunk_text[:optimal_end].strip()
        
        # Fallback: look for paragraph breaks
        paragraph_breaks = []
        for match in re.finditer(r'\n\s*\n', chunk_text[search_start:]):
            paragraph_breaks.append(search_start + match.start())
        
        if paragraph_breaks:
            optimal_end = paragraph_breaks[-1]
            return chunk_text[:optimal_end].strip()
        
        # No good breaking point found, return original
        return chunk_text
    
    def identify_section(self, chunk_text: str) -> Optional[str]:
        """
        Identify which SEC filing section a chunk belongs to.
        
        Args:
            chunk_text (str): Text chunk to analyze
            
        Returns:
            str: Section name if identified, None otherwise
        """
        # Look for section headers in the chunk
        section_patterns = {
            r'ITEM\s+1\.\s+BUSINESS': 'Item 1 - Business',
            r'ITEM\s+1A\.\s+RISK\s+FACTORS': 'Item 1A - Risk Factors',
            r'ITEM\s+7\.\s+MANAGEMENT\'S\s+DISCUSSION': 'Item 7 - MD&A',
            r'ITEM\s+8\.\s+FINANCIAL\s+STATEMENTS': 'Item 8 - Financial Statements',
        }
        
        for pattern, section_name in section_patterns.items():
            if re.search(pattern, chunk_text, re.IGNORECASE):
                return section_name
        
        return None
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the document processor configuration.
        
        Returns:
            Dict[str, Any]: Processor statistics
        """
        return {
            'chunk_size': self.chunk_size,
            'chunk_overlap': self.chunk_overlap,
            'step_size': self.chunk_size - self.chunk_overlap,
            'processor_type': 'fixed_character_count'
        }
