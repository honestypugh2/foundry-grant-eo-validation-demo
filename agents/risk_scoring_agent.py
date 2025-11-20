"""
Risk Scoring Agent
Assigns risk scores based on compliance gaps and proposal quality.
"""

import logging
from typing import Dict, Any, List, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class RiskScoringAgent:
    """
    Agent responsible for calculating risk scores based on compliance
    validation results and proposal characteristics.
    """
    
    # Risk thresholds
    HIGH_RISK_THRESHOLD = 60
    MEDIUM_RISK_THRESHOLD = 75
    LOW_RISK_THRESHOLD = 90
    
    def __init__(self):
        """Initialize the Risk Scoring Agent."""
        pass
    
    def calculate_risk_score(
        self,
        compliance_report: Dict[str, Any],
        summary: Dict[str, Any],
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive risk score for the grant proposal.
        
        RISK SCORE (0-100):
        - Composite score measuring overall proposal risk
        - Higher score = lower risk (90+ is ideal)
        - Lower score = higher risk (<60 requires rejection)
        
        Calculation Formula:
            Risk = (Compliance × 60%) + (Quality × 25%) + (Completeness × 15%)
        
        Components:
        1. Compliance Risk (60% weight):
           - Based on compliance_score from ComplianceValidatorAgent
           - Primary factor: legal/regulatory alignment
           - Threshold: <70% triggers HIGH risk
        
        2. Quality Risk (25% weight):
           - Writing clarity, documentation quality, proposal structure
           - Subjective assessment of overall professionalism
        
        3. Completeness Risk (15% weight):
           - All required sections present and filled out
           - Budget details, timeline, objectives documented
        
        Risk Levels & Actions:
        - 90-100 (Low Risk): Approve
        - 75-89 (Medium Risk): Recommend approval with minor revisions
        - 60-74 (Medium-High Risk): Approve with major revisions required
        - <60 (High Risk): Recommend rejection or major rework
        
        Conservative Bias:
        - Formula intentionally prioritizes compliance (60% weight)
        - Appropriate for legal/regulatory context
        - Lower scores require stronger justification to approve
        
        Args:
            compliance_report: Results from ComplianceValidatorAgent
            summary: Summary from SummarizationAgent
            metadata: Document metadata
            
        Returns:
            Dictionary containing risk score, level, factors, and recommendations
            
        See docs/SCORING_SYSTEM.md for complete documentation.
        """
        logger.info("Calculating risk score")
        
        try:
            # Calculate individual risk factors
            compliance_risk = self._calculate_compliance_risk(compliance_report)
            quality_risk = self._calculate_quality_risk(summary, metadata)
            completeness_risk = self._calculate_completeness_risk(compliance_report, summary)
            
            # Calculate weighted overall risk score
            # RISK CALCULATION FORMULA:
            # Formula: Risk = (Compliance × 60%) + (Quality × 25%) + (Completeness × 15%)
            #
            # Weighting Rationale:
            # - Compliance (60%): Primary concern for legal/regulatory adherence
            #   * Most important factor for grant approval
            #   * Non-compliance can result in legal issues
            #   * Heavy weight ensures compliance issues significantly impact risk
            #
            # - Quality (25%): Secondary concern for proposal effectiveness
            #   * Poor quality reduces likelihood of successful execution
            #   * Impacts reviewer perception and approval likelihood
            #   * Moderate weight reflects importance without overshadowing compliance
            #
            # - Completeness (15%): Tertiary concern for administrative requirements
            #   * Missing sections can be addressed with revisions
            #   * Less critical than compliance or quality
            #   * Light weight reflects fixable nature of completeness issues
            #
            # Result Interpretation:
            # - Higher overall_score = Lower overall risk (90+ ideal)
            # - Lower overall_score = Higher overall risk (<60 rejection recommended)
            weights = {
                'compliance': 0.60,  # Compliance is most important
                'quality': 0.25,
                'completeness': 0.15
            }
            
            overall_score = (
                compliance_risk['score'] * weights['compliance'] +
                quality_risk['score'] * weights['quality'] +
                completeness_risk['score'] * weights['completeness']
            )
            
            # Determine risk level
            risk_level = self._determine_risk_level(overall_score)
            
            # Generate risk factors list
            risk_factors = []
            risk_factors.extend(compliance_risk['factors'])
            risk_factors.extend(quality_risk['factors'])
            risk_factors.extend(completeness_risk['factors'])
            
            # Generate recommendations
            recommendations = self._generate_risk_recommendations(
                risk_level,
                compliance_report,
                risk_factors
            )
            
            # Determine if email notification is needed
            requires_notification = overall_score < self.MEDIUM_RISK_THRESHOLD
            
            risk_report = {
                'overall_score': round(overall_score, 2),
                'risk_level': risk_level,
                'confidence': self._calculate_confidence(overall_score),
                'requires_notification': requires_notification,
                'risk_breakdown': {
                    'compliance_risk': compliance_risk,
                    'quality_risk': quality_risk,
                    'completeness_risk': completeness_risk
                },
                'risk_factors': risk_factors,
                'recommendations': recommendations,
                'relevant_executive_orders': compliance_report.get('relevant_executive_orders', []),
                'metadata': {
                    'calculation_timestamp': datetime.now().isoformat(),
                    'thresholds': {
                        'high_risk': self.HIGH_RISK_THRESHOLD,
                        'medium_risk': self.MEDIUM_RISK_THRESHOLD,
                        'low_risk': self.LOW_RISK_THRESHOLD
                    }
                }
            }
            
            logger.info(
                f"Risk score calculated: {overall_score:.2f} ({risk_level}). "
                f"Notification required: {requires_notification}"
            )
            return risk_report
            
        except Exception as e:
            logger.error(f"Error calculating risk score: {str(e)}")
            raise
    
    def _calculate_compliance_risk(self, compliance_report: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate risk based on compliance validation results."""
        compliance_score = compliance_report.get('compliance_score', 0)
        confidence_score = compliance_report.get('confidence_score', 70)  # From ComplianceAgent
        violations = compliance_report.get('violations', [])
        warnings = compliance_report.get('warnings', [])
        
        factors = []
        
        # Convert compliance score (0-100) to risk score (100 = low risk)
        # Weight by confidence score - lower confidence increases risk
        confidence_factor = confidence_score / 100.0
        risk_score = compliance_score * confidence_factor
        
        # Add risk factors based on violations
        if violations:
            factors.append({
                'factor': 'Compliance Violations',
                'severity': 'high',
                'count': len(violations),
                'description': f'{len(violations)} compliance violations detected'
            })
        
        if warnings:
            factors.append({
                'factor': 'Compliance Warnings',
                'severity': 'medium',
                'count': len(warnings),
                'description': f'{len(warnings)} compliance warnings identified'
            })
        
        if compliance_score < 60:
            factors.append({
                'factor': 'Low Compliance Score',
                'severity': 'high',
                'description': f'Compliance score of {compliance_score}% is below acceptable threshold'
            })
        
        # Flag low confidence in compliance analysis
        if confidence_score < 60:
            factors.append({
                'factor': 'Low Analysis Confidence',
                'severity': 'medium',
                'description': f'Compliance analysis confidence of {confidence_score}% suggests uncertainty - requires human review'
            })
            # Further reduce risk score for very low confidence
            risk_score = risk_score * 0.9
        
        return {
            'score': risk_score,
            'factors': factors,
            'violations_count': len(violations),
            'warnings_count': len(warnings)
        }
    
    def _calculate_quality_risk(
        self,
        summary: Dict[str, Any],
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate risk based on document quality indicators."""
        factors = []
        
        # Start with baseline quality score
        quality_score = 100
        
        # Check document completeness
        word_count = metadata.get('word_count', 0)
        page_count = metadata.get('page_count', 0)
        
        if word_count < 500:
            quality_score -= 30
            factors.append({
                'factor': 'Insufficient Content',
                'severity': 'high',
                'description': f'Document has only {word_count} words (minimum recommended: 500)'
            })
        elif word_count < 1000:
            quality_score -= 15
            factors.append({
                'factor': 'Limited Content',
                'severity': 'medium',
                'description': f'Document has only {word_count} words (recommended: 1000+)'
            })
        
        if page_count < 2:
            quality_score -= 10
            factors.append({
                'factor': 'Short Document',
                'severity': 'medium',
                'description': f'Document has only {page_count} page(s)'
            })
        
        # Check for key topics
        key_topics = summary.get('key_topics', [])
        if len(key_topics) < 3:
            quality_score -= 20
            factors.append({
                'factor': 'Limited Topic Coverage',
                'severity': 'medium',
                'description': f'Only {len(key_topics)} key topics identified'
            })
        
        # Ensure score doesn't go below 0
        quality_score = max(0, quality_score)
        
        return {
            'score': quality_score,
            'factors': factors,
            'word_count': word_count,
            'page_count': page_count
        }
    
    def _calculate_completeness_risk(
        self,
        compliance_report: Dict[str, Any],
        summary: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate risk based on proposal completeness."""
        factors = []
        completeness_score = 100
        
        # Check if key sections are present
        key_clauses = summary.get('key_clauses', [])
        if len(key_clauses) < 3:
            completeness_score -= 25
            factors.append({
                'factor': 'Missing Key Clauses',
                'severity': 'high',
                'description': f'Only {len(key_clauses)} key clauses identified (expected: 3+)'
            })
        
        # Check if relevant executive orders were found
        relevant_eos = compliance_report.get('relevant_executive_orders', [])
        if len(relevant_eos) == 0:
            completeness_score -= 40
            factors.append({
                'factor': 'No Relevant Executive Orders',
                'severity': 'high',
                'description': 'No relevant executive orders found for this proposal'
            })
        elif len(relevant_eos) < 2:
            completeness_score -= 20
            factors.append({
                'factor': 'Limited EO Coverage',
                'severity': 'medium',
                'description': 'Only one relevant executive order identified'
            })
        
        # Ensure score doesn't go below 0
        completeness_score = max(0, completeness_score)
        
        return {
            'score': completeness_score,
            'factors': factors
        }
    
    def _determine_risk_level(self, score: float) -> str:
        """Determine risk level from score."""
        if score >= self.LOW_RISK_THRESHOLD:
            return 'low'
        elif score >= self.MEDIUM_RISK_THRESHOLD:
            return 'medium'
        elif score >= self.HIGH_RISK_THRESHOLD:
            return 'medium-high'
        else:
            return 'high'
    
    def _calculate_confidence(self, score: float) -> float:
        """Calculate confidence level in the risk assessment."""
        # Confidence is higher when score is at extremes
        # and lower when score is in the middle
        distance_from_50 = abs(score - 50)
        confidence = 50 + (distance_from_50)
        return round(min(100, confidence), 2)
    
    def _generate_risk_recommendations(
        self,
        risk_level: str,
        compliance_report: Dict[str, Any],
        risk_factors: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate recommendations based on risk assessment."""
        recommendations = []
        
        # Risk level-based recommendations
        if risk_level == 'high':
            recommendations.append({
                'priority': 'critical',
                'action': 'Immediate Legal Review Required',
                'description': 'This proposal requires immediate attorney review before proceeding.'
            })
            recommendations.append({
                'priority': 'critical',
                'action': 'Address Compliance Issues',
                'description': 'All compliance violations must be resolved before submission.'
            })
        
        elif risk_level == 'medium-high':
            recommendations.append({
                'priority': 'high',
                'action': 'Legal Review Recommended',
                'description': 'Attorney review strongly recommended before submission.'
            })
        
        elif risk_level == 'medium':
            recommendations.append({
                'priority': 'medium',
                'action': 'Supervisory Review',
                'description': 'Department supervisor should review before final submission.'
            })
        
        # Factor-specific recommendations
        high_severity_factors = [f for f in risk_factors if f.get('severity') == 'high']
        if high_severity_factors:
            recommendations.append({
                'priority': 'high',
                'action': 'Address High-Severity Issues',
                'description': f'{len(high_severity_factors)} high-severity issues require attention.'
            })
        
        # Compliance-specific recommendations
        violations = compliance_report.get('violations', [])
        if violations:
            recommendations.append({
                'priority': 'high',
                'action': 'Revise Proposal for Compliance',
                'description': 'Revise proposal to address identified compliance violations.',
                'violations_count': len(violations)
            })
        
        return recommendations
    
    def should_send_email(self, risk_report: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Determine if email notification should be sent based on risk.
        
        Args:
            risk_report: Risk scoring results
            
        Returns:
            Tuple of (should_send, reason)
        """
        overall_score = risk_report['overall_score']
        risk_level = risk_report['risk_level']
        
        if risk_level == 'high':
            return (True, 'High risk proposal requires immediate attorney notification')
        
        elif risk_level == 'medium-high':
            return (True, 'Medium-high risk proposal requires attorney review')
        
        elif overall_score < self.MEDIUM_RISK_THRESHOLD:
            return (True, f'Risk score {overall_score} below threshold ({self.MEDIUM_RISK_THRESHOLD})')
        
        return (False, 'Risk level acceptable - no notification required')
