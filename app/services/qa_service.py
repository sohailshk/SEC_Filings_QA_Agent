"""
Question-Answering Service using Google Gemini

This module provides Q&A capabilities for SEC filings using Google Gemini
through LangChain integration for document retrieval and answer generation.

Best Practices Followed:
- Integration with LangChain for document Q&A
- Source attribution for all answers
- Error handling and logging
- Structured response format
- Context management for better answers
"""

import logging
from typing import List, Dict, Any, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import re
from datetime import datetime

# Setup logging for this module
logger = logging.getLogger(__name__)

class QAService:
    """
    Question-Answering service for SEC filings using Google Gemini.
    
    This service handles:
    - Query processing and understanding
    - Document retrieval using vector search
    - Answer generation with source attribution
    - Response formatting and validation
    """
    
    def __init__(self, gemini_api_key: str, model_name: str = "gemini-2.0-flash"):
        """
        Initialize Q&A service with Google Gemini.
        
        Args:
            gemini_api_key (str): Google Gemini API key
            model_name (str): Name of Gemini model to use
        """
        self.gemini_api_key = gemini_api_key
        self.model_name = model_name
        
        # Initialize Gemini LLM through LangChain
        logger.info(f"Initializing Gemini model: {model_name}")
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=gemini_api_key,
            temperature=0.1,  # Low temperature for more factual responses
            convert_system_message_to_human=True  # Required for Gemini
        )
        
        # Create prompts for different types of questions
        self.setup_prompts()
        
        logger.info("Q&A service initialized successfully")
    
    def setup_prompts(self):
        """Setup prompt templates for different Q&A scenarios."""
        
        # Main Q&A prompt for structured financial analysis
        self.qa_prompt = PromptTemplate(
            input_variables=["context", "question", "company_info"],
            template="""You are a senior financial analyst specializing in SEC filings analysis. Your task is to provide well-structured, professional analysis.

COMPANY INFORMATION:
{company_info}

CONTEXT FROM SEC FILINGS:
{context}

QUESTION: {question}

INSTRUCTIONS:
1. Provide a comprehensive answer based ONLY on the information provided in the context
2. Structure your response using clear markdown formatting with:
   - Main headings (##) for major topics
   - Subheadings (###) for subtopics
   - Bullet points (-) for key details
   - Bold text (**text**) for emphasis on important figures and company names
3. Organize information by company when analyzing multiple companies
4. Include specific financial figures with time periods in bold
5. Always cite sources using the format (Source X) after each key point
6. If information is insufficient, clearly state what's missing
7. Use professional financial language appropriate for executive-level reporting

ANSWER FORMAT:
## Executive Summary
[Brief overview of key findings]

## Detailed Analysis
### [Topic/Company Name]
- **Key Point 1:** [Description] (Source X)
- **Financial Figure:** [Amount and period] (Source X)

[Continue with structured analysis...]

## Key Takeaways
- [Summary point 1]
- [Summary point 2]

ANSWER:"""
        )
        
        # Prompt for summarizing document sections
        self.summary_prompt = PromptTemplate(
            input_variables=["content", "section_name", "company_info"],
            template="""You are a financial analyst assistant. Please provide a concise summary of the following section from a SEC filing.

Company Information:
{company_info}

Section: {section_name}

Content:
{content}

Please provide a clear, structured summary that highlights:
1. Key points and main themes
2. Important financial information or metrics (if any)
3. Significant risks, opportunities, or changes mentioned
4. Any notable trends or strategic initiatives

Summary:"""
        )
        
        # Prompt for extracting specific information
        self.extraction_prompt = PromptTemplate(
            input_variables=["context", "extraction_target", "company_info"],
            template="""You are a financial analyst assistant. Please extract specific information from the SEC filing content.

Company Information:
{company_info}

Extract information about: {extraction_target}

Content:
{context}

Instructions:
1. Extract only factual information directly stated in the content
2. Organize the information in a clear, structured format
3. Include relevant financial figures with their context
4. Note the source section if identifiable
5. If the requested information is not found, state this clearly

Extracted Information:"""
        )
    
    def answer_question(self, question: str, relevant_chunks: List[Dict[str, Any]], 
                       company_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate an answer to a question using relevant document chunks.
        
        Args:
            question (str): User's question
            relevant_chunks (List[Dict[str, Any]]): Retrieved document chunks
            company_info (Dict[str, Any]): Company information for context
            
        Returns:
            Dict[str, Any]: Answer with sources and metadata
        """
        logger.info(f"Answering question: {question[:100]}...")
        
        try:
            # Prepare context from relevant chunks
            context = self.prepare_context_from_chunks(relevant_chunks)
            
            # Format company information
            company_context = self.format_company_info(company_info)
            
            # Generate answer using Gemini
            qa_chain = LLMChain(llm=self.llm, prompt=self.qa_prompt)
            
            response = qa_chain.run(
                context=context,
                question=question,
                company_info=company_context
            )
            
            # Process and format the response
            formatted_response = self.format_qa_response(
                question=question,
                answer=response,
                sources=relevant_chunks,
                company_info=company_info
            )
            
            logger.info("Successfully generated answer")
            return formatted_response
            
        except Exception as e:
            logger.error(f"Failed to generate answer: {e}")
            return self.create_error_response(question, str(e))
    
    def prepare_context_from_chunks(self, chunks: List[Dict[str, Any]]) -> str:
        """
        Prepare context text from retrieved document chunks.
        
        Args:
            chunks (List[Dict[str, Any]]): Document chunks with text and metadata
            
        Returns:
            str: Formatted context text
        """
        if not chunks:
            return "No relevant information found."
        
        context_parts = []
        
        for i, chunk in enumerate(chunks[:5]):  # Limit to top 5 chunks to avoid context overflow
            text = chunk.get('text', '')
            metadata = chunk.get('metadata', {})
            
            # Add source information
            source_info = []
            if metadata.get('section_name'):
                source_info.append(f"Section: {metadata['section_name']}")
            if metadata.get('filing_type'):
                source_info.append(f"Filing: {metadata['filing_type']}")
            if metadata.get('filing_date'):
                source_info.append(f"Date: {metadata['filing_date']}")
            
            source_label = f"[Source {i+1}" + (f" - {', '.join(source_info)}" if source_info else "") + "]"
            
            context_parts.append(f"{source_label}\n{text}\n")
        
        return "\n---\n".join(context_parts)
    
    def format_company_info(self, company_info: Dict[str, Any]) -> str:
        """
        Format company information for use in prompts.
        
        Args:
            company_info (Dict[str, Any]): Company metadata
            
        Returns:
            str: Formatted company information
        """
        if not company_info:
            return "Company information not available."
        
        info_parts = []
        
        if company_info.get('company_name'):
            info_parts.append(f"Company: {company_info['company_name']}")
        if company_info.get('ticker'):
            info_parts.append(f"Ticker: {company_info['ticker']}")
        if company_info.get('sector'):
            info_parts.append(f"Sector: {company_info['sector']}")
        if company_info.get('industry'):
            info_parts.append(f"Industry: {company_info['industry']}")
        
        return "\n".join(info_parts) if info_parts else "Company information not available."
    
    def format_qa_response(self, question: str, answer: str, 
                          sources: List[Dict[str, Any]], 
                          company_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format the complete Q&A response with metadata.
        
        Args:
            question (str): Original question
            answer (str): Generated answer
            sources (List[Dict[str, Any]]): Source document chunks
            company_info (Dict[str, Any]): Company information
            
        Returns:
            Dict[str, Any]: Formatted response
        """
        # Clean the answer text
        cleaned_answer = self.clean_answer_text(answer)
        
        # Extract source information for attribution
        source_references = []
        for i, chunk in enumerate(sources):
            metadata = chunk.get('metadata', {})
            
            # Get similarity score and convert to confidence percentage
            similarity_score = chunk.get('similarity_score', 0.0)
            confidence = min(similarity_score, 1.0)  # Ensure it's between 0 and 1
            
            source_ref = {
                'source_id': i + 1,
                'ticker': metadata.get('ticker', 'Unknown'),
                'filing_type': metadata.get('filing_type', 'Unknown'),
                'filing_date': metadata.get('filing_date', 'Unknown'),
                'section_name': metadata.get('section_name'),
                'text': chunk.get('text', 'No excerpt available'),
                'confidence': confidence,
                'similarity_score': similarity_score,
                'chunk_index': metadata.get('chunk_index', 0)
            }
            source_references.append(source_ref)

        return {
            'question': question,
            'answer': cleaned_answer,
            'company_info': company_info,
            'sources': source_references,
            'confidence_indicators': self.assess_answer_confidence(cleaned_answer, sources),
            'timestamp': datetime.now().isoformat(),
            'model_used': self.model_name,
            'num_sources_used': len(sources)
        }
    
    def clean_answer_text(self, answer: str) -> str:
        """
        Clean and structure answer text for better readability while preserving formatting.
        
        Args:
            answer (str): Raw answer text
            
        Returns:
            str: Cleaned and structured answer text
        """
        if not answer:
            return "No answer available"
        
        # First, clean up any malformed markdown
        cleaned = answer.strip()
        
        # Fix common markdown issues
        cleaned = re.sub(r'\*\*([^*]+)\*\*', r'**\1**', cleaned)  # Fix bold formatting
        cleaned = re.sub(r'^\s*#+\s*', '## ', cleaned, flags=re.MULTILINE)  # Standardize headers
        
        # Ensure proper spacing around sections
        cleaned = re.sub(r'\n\s*\n\s*\n+', '\n\n', cleaned)  # Remove excessive newlines
        cleaned = re.sub(r'([.!?])\s*([A-Z##])', r'\1\n\n\2', cleaned)  # Add breaks after sentences before headers
        
        # Ensure bullet points are properly formatted
        cleaned = re.sub(r'\n\s*[-•]\s*', '\n- ', cleaned)
        
        # Clean up source citations
        cleaned = re.sub(r'\(Source\s+(\d+)[^)]*\)', r'(Source \1)', cleaned)
        
        return cleaned if cleaned else "No answer available"
    
    def assess_answer_confidence(self, answer: str, sources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Assess confidence in the generated answer based on various indicators.
        
        Args:
            answer (str): Generated answer text
            sources (List[Dict[str, Any]]): Source documents used
            
        Returns:
            Dict[str, Any]: Confidence indicators
        """
        indicators = {
            'source_quality': 'high' if sources and len(sources) >= 2 else 'medium' if sources else 'low',
            'answer_specificity': 'high' if len(answer) > 200 and any(word in answer.lower() for word in ['specific', 'according to', 'states that']) else 'medium',
            'uncertainty_markers': bool(re.search(r'\b(may|might|could|uncertain|unclear|not specified)\b', answer.lower())),
            'numerical_data_present': bool(re.search(r'\$[\d,]+|\d+%|\d+\s+(million|billion)', answer)),
            'avg_source_similarity': sum(s.get('similarity_score', 0) for s in sources) / len(sources) if sources else 0.0
        }
        
        return indicators
    
    def summarize_section(self, content: str, section_name: str, 
                         company_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a summary of a specific section from a SEC filing.
        
        Args:
            content (str): Section content to summarize
            section_name (str): Name of the section
            company_info (Dict[str, Any]): Company information
            
        Returns:
            Dict[str, Any]: Summary with metadata
        """
        logger.info(f"Summarizing section: {section_name}")
        
        try:
            company_context = self.format_company_info(company_info)
            
            summary_chain = LLMChain(llm=self.llm, prompt=self.summary_prompt)
            
            summary = summary_chain.run(
                content=content[:4000],  # Limit content length to avoid context overflow
                section_name=section_name,
                company_info=company_context
            )
            
            return {
                'section_name': section_name,
                'summary': summary.strip(),
                'company_info': company_info,
                'content_length': len(content),
                'timestamp': datetime.now().isoformat(),
                'model_used': self.model_name
            }
            
        except Exception as e:
            logger.error(f"Failed to summarize section {section_name}: {e}")
            return {
                'section_name': section_name,
                'summary': f"Error generating summary: {str(e)}",
                'error': True,
                'timestamp': datetime.now().isoformat()
            }
    
    def extract_information(self, content: str, extraction_target: str,
                           company_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract specific information from SEC filing content.
        
        Args:
            content (str): Document content
            extraction_target (str): What to extract (e.g., "revenue figures", "risk factors")
            company_info (Dict[str, Any]): Company information
            
        Returns:
            Dict[str, Any]: Extracted information with metadata
        """
        logger.info(f"Extracting information: {extraction_target}")
        
        try:
            company_context = self.format_company_info(company_info)
            
            extraction_chain = LLMChain(llm=self.llm, prompt=self.extraction_prompt)
            
            extracted_info = extraction_chain.run(
                context=content[:4000],
                extraction_target=extraction_target,
                company_info=company_context
            )
            
            return {
                'extraction_target': extraction_target,
                'extracted_information': extracted_info.strip(),
                'company_info': company_info,
                'content_length': len(content),
                'timestamp': datetime.now().isoformat(),
                'model_used': self.model_name
            }
            
        except Exception as e:
            logger.error(f"Failed to extract information '{extraction_target}': {e}")
            return {
                'extraction_target': extraction_target,
                'extracted_information': f"Error extracting information: {str(e)}",
                'error': True,
                'timestamp': datetime.now().isoformat()
            }
    
    def create_error_response(self, question: str, error_message: str) -> Dict[str, Any]:
        """
        Create a standardized error response.
        
        Args:
            question (str): Original question
            error_message (str): Error description
            
        Returns:
            Dict[str, Any]: Error response
        """
        return {
            'question': question,
            'answer': f"I apologize, but I encountered an error while processing your question: {error_message}",
            'error': True,
            'timestamp': datetime.now().isoformat(),
            'sources': [],
            'company_info': {},
            'confidence_indicators': {'source_quality': 'none'},
            'model_used': self.model_name
        }
