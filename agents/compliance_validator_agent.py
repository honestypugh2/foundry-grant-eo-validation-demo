"""
Compliance Validator Agent
Checks eligibility, legal clauses, and grant conditions against executive orders.
"""

import os
import logging
from typing import Dict, Any, List
from pathlib import Path

logger = logging.getLogger(__name__)


class ComplianceValidatorAgent:
    """
    Agent responsible for validating grant proposals against executive orders
    and compliance requirements using Azure AI Search.
    """
    
    def __init__(self, use_azure_search: bool = False):
        """
        Initialize the Compliance Validator Agent.
        
        Args:
            use_azure_search: If True, use Azure AI Search. Otherwise, use local knowledge base.
        """
        self.use_azure_search = use_azure_search
        self.search_endpoint = os.getenv('AZURE_SEARCH_ENDPOINT')
        self.search_key = os.getenv('AZURE_SEARCH_API_KEY')
        self.search_index = os.getenv('AZURE_SEARCH_INDEX_NAME', 'grant-compliance-index')
        self.knowledge_base_path = Path(__file__).parent.parent / 'knowledge_base'
        
        if self.use_azure_search and not self.search_endpoint:
            logger.warning("Azure AI Search not configured. Using local knowledge base.")
            self.use_azure_search = False
        
        # Load local knowledge base
        self.executive_orders = self._load_local_knowledge_base()
    
    def validate_compliance(
        self,
        proposal_text: str,
        summary: Dict[str, Any],
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate grant proposal compliance against executive orders.
        
        Args:
            proposal_text: Full text of the proposal
            summary: Summary data from SummarizationAgent
            metadata: Document metadata
            
        Returns:
            Dictionary containing compliance results, violations, and recommendations
        """
        logger.info("Validating compliance against executive orders")
        
        try:
            # Search for relevant executive orders
            relevant_eos = self._find_relevant_executive_orders(
                proposal_text,
                summary.get('key_topics', [])
            )
            
            # Perform compliance checks
            compliance_results = self._check_compliance(
                proposal_text,
                summary,
                relevant_eos
            )
            
            # Generate compliance report
            report = {
                'overall_status': compliance_results['status'],
                'compliance_score': compliance_results['score'],
                'relevant_executive_orders': [
                    {
                        'name': eo['name'],
                        'relevance': eo['relevance'],
                        'key_requirements': eo.get('requirements', [])
                    }
                    for eo in relevant_eos
                ],
                'compliance_checks': compliance_results['checks'],
                'violations': compliance_results['violations'],
                'warnings': compliance_results['warnings'],
                'recommendations': compliance_results['recommendations'],
                'metadata': {
                    'validation_method': 'azure_search' if self.use_azure_search else 'local',
                    'eo_count': len(relevant_eos),
                    'checks_performed': len(compliance_results['checks'])
                }
            }
            
            logger.info(f"Compliance validation complete. Status: {report['overall_status']}")
            return report
            
        except Exception as e:
            logger.error(f"Error during compliance validation: {str(e)}")
            raise
    
    def _load_local_knowledge_base(self) -> List[Dict[str, Any]]:
        """Load executive orders from local knowledge base."""
        executive_orders = []
        eo_path = self.knowledge_base_path / 'sample_executive_orders'
        
        if not eo_path.exists():
            logger.warning(f"Knowledge base path not found: {eo_path}")
            return []
        
        for file_path in eo_path.glob('*.txt'):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract EO number and title from filename
                filename = file_path.stem
                parts = filename.split('_', 1)
                eo_number = parts[0] if parts else 'Unknown'
                eo_title = parts[1].replace('_', ' ') if len(parts) > 1 else 'Unknown'
                
                executive_orders.append({
                    'name': f"{eo_number}: {eo_title}",
                    'number': eo_number,
                    'title': eo_title,
                    'content': content,
                    'file_path': str(file_path)
                })
                
            except Exception as e:
                logger.warning(f"Error loading {file_path}: {str(e)}")
        
        logger.info(f"Loaded {len(executive_orders)} executive orders from local knowledge base")
        return executive_orders
    
    def _find_relevant_executive_orders(
        self,
        proposal_text: str,
        topics: List[str]
    ) -> List[Dict[str, Any]]:
        """Find executive orders relevant to the proposal."""
        if self.use_azure_search:
            return self._search_azure(proposal_text, topics)
        else:
            return self._search_local(proposal_text, topics)
    
    def _search_local(self, proposal_text: str, topics: List[str]) -> List[Dict[str, Any]]:
        """Search local knowledge base for relevant executive orders."""
        relevant = []
        
        for eo in self.executive_orders:
            relevance_score = 0
            content_lower = eo['content'].lower()
            
            # Check topic matches
            topic_matches = []
            for topic in topics:
                if topic.lower() in content_lower:
                    relevance_score += 10
                    topic_matches.append(topic)
            
            # Check for key compliance terms
            compliance_terms = [
                'shall', 'must', 'required', 'requirement', 'compliance',
                'eligible', 'eligibility', 'condition', 'standard', 'regulation'
            ]
            
            for term in compliance_terms:
                if term in content_lower:
                    relevance_score += 2
            
            if relevance_score > 0:
                eo_copy = eo.copy()
                eo_copy['relevance'] = relevance_score
                eo_copy['matched_topics'] = topic_matches
                eo_copy['requirements'] = self._extract_requirements(eo['content'])
                relevant.append(eo_copy)
        
        # Sort by relevance and return top 5
        relevant.sort(key=lambda x: x['relevance'], reverse=True)
        return relevant[:5]
    
    def _search_azure(self, proposal_text: str, topics: List[str]) -> List[Dict[str, Any]]:
        """Search Azure AI Search for relevant executive orders."""
        from azure.core.exceptions import ResourceNotFoundError, HttpResponseError
        
        try:
            from azure.search.documents import SearchClient
            from azure.core.credentials import AzureKeyCredential
            
            if not self.search_endpoint or not self.search_key:
                logger.info("Azure Search not configured. Using local knowledge base.")
                return self._search_local(proposal_text, topics)
            
            search_client = SearchClient(
                endpoint=self.search_endpoint,
                index_name=self.search_index,
                credential=AzureKeyCredential(self.search_key)
            )
            
            # Construct search query
            search_query = ' '.join(topics[:5])  # Use top topics
            
            results = search_client.search(
                search_text=search_query,
                top=5,
                select=['id', 'title', 'content', 'eo_number'],
                search_mode='any'
            )
            
            relevant = []
            for result in results:
                relevant.append({
                    'name': f"{result.get('eo_number', 'EO')}: {result.get('title', 'Unknown')}",
                    'number': result.get('eo_number', 'Unknown'),
                    'title': result.get('title', 'Unknown'),
                    'content': result.get('content', ''),
                    'relevance': result.get('@search.score', 0) * 100,
                    'requirements': self._extract_requirements(result.get('content', ''))
                })
            
            logger.info(f"Azure Search returned {len(relevant)} relevant executive orders")
            return relevant
            
        except ResourceNotFoundError:
            logger.info(f"Azure Search index '{self.search_index}' not found. Using local knowledge base instead.")
            logger.info("To create the index, run: python scripts/index_knowledge_base.py")
            return self._search_local(proposal_text, topics)
        except HttpResponseError as e:
            logger.info(f"Azure Search error: {e.message}. Using local knowledge base.")
            return self._search_local(proposal_text, topics)
        except Exception as e:
            logger.info(f"Azure Search unavailable ({type(e).__name__}). Using local knowledge base.")
            return self._search_local(proposal_text, topics)
    
    def _extract_requirements(self, eo_text: str) -> List[str]:
        """Extract requirement statements from executive order text."""
        requirements = []
        sentences = eo_text.split('.')
        
        requirement_keywords = ['shall', 'must', 'required', 'requirement', 'ensure']
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 30:  # Minimum length
                sentence_lower = sentence.lower()
                if any(keyword in sentence_lower for keyword in requirement_keywords):
                    requirements.append(sentence + '.')
                    if len(requirements) >= 5:
                        break
        
        return requirements
    
    def _check_compliance(
        self,
        proposal_text: str,
        summary: Dict[str, Any],
        relevant_eos: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Perform detailed compliance checks."""
        checks = []
        violations = []
        warnings = []
        recommendations = []
        
        total_score = 0
        max_score = 0
        
        proposal_lower = proposal_text.lower()
        
        for eo in relevant_eos:
            eo_name = eo['name']
            requirements = eo.get('requirements', [])
            
            for req in requirements:
                max_score += 10
                req_lower = req.lower()
                
                # Simple compliance check: look for key terms from requirement in proposal
                key_terms = [word for word in req_lower.split() if len(word) > 5]
                matches = sum(1 for term in key_terms if term in proposal_lower)
                match_ratio = matches / len(key_terms) if key_terms else 0
                
                if match_ratio > 0.3:
                    total_score += 10
                    status = 'compliant'
                elif match_ratio > 0.1:
                    total_score += 5
                    status = 'partial'
                    warnings.append({
                        'requirement': req,
                        'executive_order': eo_name,
                        'message': 'Partial compliance detected. Review recommended.'
                    })
                else:
                    status = 'non_compliant'
                    violations.append({
                        'requirement': req,
                        'executive_order': eo_name,
                        'message': 'Requirement not adequately addressed in proposal.'
                    })
                
                checks.append({
                    'requirement': req[:200] + '...' if len(req) > 200 else req,
                    'executive_order': eo_name,
                    'status': status,
                    'match_ratio': round(match_ratio, 2)
                })
        
        # Calculate overall score
        overall_score = (total_score / max_score * 100) if max_score > 0 else 0
        
        # Determine overall status
        if overall_score >= 80:
            overall_status = 'compliant'
        elif overall_score >= 60:
            overall_status = 'partial_compliance'
        else:
            overall_status = 'non_compliant'
        
        # Generate recommendations
        if violations:
            recommendations.append({
                'priority': 'high',
                'message': f'Address {len(violations)} compliance violations before submission.'
            })
        
        if warnings:
            recommendations.append({
                'priority': 'medium',
                'message': f'Review {len(warnings)} warnings to strengthen compliance.'
            })
        
        if overall_score < 80:
            recommendations.append({
                'priority': 'high',
                'message': 'Consider consulting with legal counsel before proceeding.'
            })
        
        return {
            'status': overall_status,
            'score': round(overall_score, 2),
            'checks': checks,
            'violations': violations,
            'warnings': warnings,
            'recommendations': recommendations
        }
