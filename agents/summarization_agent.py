"""
Summarization Agent
Generates concise summaries of proposal sections and highlights key clauses.
"""

import os
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class SummarizationAgent:
    """
    Agent responsible for generating summaries of grant proposals.
    Creates executive summaries and identifies key clauses.
    """
    
    def __init__(self, use_azure: bool = True):
        """
        Initialize the Summarization Agent.
        
        Args:
            use_azure: If True, use Azure OpenAI for summarization. Otherwise, use simple extraction.
        """
        self.use_azure = use_azure
        self.endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
        self.api_key = os.getenv('AZURE_OPENAI_API_KEY')
        self.deployment = os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME', 'gpt-4')
        self.api_version = os.getenv('AZURE_OPENAI_API_VERSION', '2024-10-01-preview')
        
        if self.use_azure and not self.endpoint:
            logger.warning("Azure OpenAI not configured. Using local summarization.")
            self.use_azure = False
    
    def generate_summary(self, document_text: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a comprehensive summary of the grant proposal.
        
        Args:
            document_text: Full text of the document
            metadata: Document metadata
            
        Returns:
            Dictionary containing executive summary and key highlights
        """
        logger.info("Generating document summary")
        
        try:
            if self.use_azure:
                summary_data = self._generate_with_azure(document_text)
            else:
                summary_data = self._generate_locally(document_text)
            
            # Add metadata
            summary_data['metadata'] = {
                'summary_method': 'azure_openai' if self.use_azure else 'local',
                'original_word_count': metadata.get('word_count', 0),
                'original_page_count': metadata.get('page_count', 0)
            }
            
            logger.info("Successfully generated summary")
            return summary_data
            
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            raise
    
    def _generate_locally(self, text: str) -> Dict[str, Any]:
        """Generate summary using simple text extraction."""
        lines = text.split('\n')
        paragraphs = [line.strip() for line in lines if line.strip() and len(line.strip()) > 50]
        
        # Take first few paragraphs as summary
        executive_summary = '\n\n'.join(paragraphs[:3]) if paragraphs else text[:500]
        
        # Extract potential key phrases
        key_clauses = []
        keywords = ['compliance', 'requirement', 'objective', 'budget', 'timeline', 'deliverable']
        
        for paragraph in paragraphs:
            para_lower = paragraph.lower()
            if any(keyword in para_lower for keyword in keywords):
                key_clauses.append(paragraph)
                if len(key_clauses) >= 5:
                    break
        
        return {
            'executive_summary': executive_summary,
            'key_clauses': key_clauses[:5],
            'key_topics': keywords,
            'summary_length': len(executive_summary.split())
        }
    
    def _generate_with_azure(self, text: str) -> Dict[str, Any]:
        """Generate summary using Azure OpenAI."""
        try:
            from openai import AzureOpenAI
            
            if not self.endpoint:
                raise ValueError("Azure OpenAI endpoint is not configured")
            
            client = AzureOpenAI(
                api_key=self.api_key,
                api_version=self.api_version,
                azure_endpoint=self.endpoint
            )
            
            # Generate executive summary
            summary_prompt = f"""Analyze this grant proposal and provide:
1. A concise executive summary (3-4 sentences)
2. Key objectives (bullet points)
3. Budget highlights
4. Timeline/deliverables
5. Critical compliance requirements mentioned
6. A comprehensive summary

Grant Proposal:
{text}  # Limit to avoid token limits
"""
            
            summary_response = client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {"role": "system", "content": "You are an expert grant proposal analyst. Provide clear, concise, and comprehensive summaries."},
                    {"role": "user", "content": summary_prompt}
                ],
                temperature=0.3,
                # max_tokens=1000
            )
            
            summary_text = summary_response.choices[0].message.content
            
            # Extract key clauses
            clauses_prompt = f"""Extract the specific clauses, phrases or requirements from this grant proposal that may pose compliance risks. 
For each clause, provide:
- The clause text (verbatim if possible)
- Why it's important
- Any compliance implications

Grant Proposal:
{text}
"""
            
            clauses_response = client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {"role": "system", "content": "You are an expert at identifying critical clauses in legal and grant documents."},
                    {"role": "user", "content": clauses_prompt}
                ],
                temperature=0.2,
                # max_tokens=1500
            )
            
            clauses_text = clauses_response.choices[0].message.content
            
            # Parse clauses (simple split for now)
            key_clauses = [clause.strip() for clause in (clauses_text or "").split('\n\n') if clause.strip()]
            
            return {
                'executive_summary': summary_text,
                'key_clauses': key_clauses[:5],
                'key_topics': self._extract_topics(summary_text or ""),
                'summary_length': len((summary_text or "").split()),
                'detailed_analysis': clauses_text
            }
            
        except Exception as e:
            logger.warning(f"Azure summarization failed: {str(e)}. Using local method.")
            return self._generate_locally(text)
    
    def _extract_topics(self, text: str) -> List[str]:
        """Extract key topics from summary text."""
        keywords = [
            'compliance', 'budget', 'timeline', 'deliverable', 'requirement',
            'objective', 'sustainability', 'equity', 'cybersecurity', 'climate',
            'workforce', 'education', 'infrastructure', 'community', 'innovation'
        ]
        
        text_lower = text.lower()
        found_topics = [kw for kw in keywords if kw in text_lower]
        
        return found_topics[:8]
    
    def highlight_sections(self, text: str, topics: List[str]) -> Dict[str, str]:
        """
        Extract and highlight specific sections related to topics.
        
        Args:
            text: Full document text
            topics: List of topics to highlight
            
        Returns:
            Dictionary mapping topics to relevant text sections
        """
        sections = {}
        paragraphs = text.split('\n\n')
        
        for topic in topics:
            topic_lower = topic.lower()
            relevant_paras = []
            
            for para in paragraphs:
                if topic_lower in para.lower() and len(para.strip()) > 50:
                    relevant_paras.append(para.strip())
                    if len(relevant_paras) >= 3:
                        break
            
            if relevant_paras:
                sections[topic] = '\n\n'.join(relevant_paras)
        
        return sections
