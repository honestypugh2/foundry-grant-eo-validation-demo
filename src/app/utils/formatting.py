"""
Formatting utilities for display purposes.
"""

from typing import List, Dict, Any

def format_risk_level(risk_level: str) -> tuple:
    """
    Format risk level with appropriate color and icon.
    
    Args:
        risk_level: Risk level string (LOW, MEDIUM, HIGH, CRITICAL)
        
    Returns:
        Tuple of (color, icon)
    """
    risk_colors = {
        "LOW": ("green", "✅"),
        "MEDIUM": ("orange", "⚠️"),
        "HIGH": ("red", "🔴"),
        "CRITICAL": ("darkred", "🚨")
    }
    
    return risk_colors.get(risk_level.upper(), ("gray", "❓"))

def format_percentage(value: float, decimals: int = 1) -> str:
    """
    Format a float as a percentage string.
    
    Args:
        value: Value between 0 and 1 (or 0-100)
        decimals: Number of decimal places
        
    Returns:
        Formatted percentage string
    """
    # Handle both 0-1 and 0-100 scales
    if value <= 1.0:
        value *= 100
    
    return f"{value:.{decimals}f}%"

def format_violations(violations: List[Dict[str, Any]]) -> str:
    """
    Format violations list into a readable string.
    
    Args:
        violations: List of violation dictionaries
        
    Returns:
        Formatted string
    """
    if not violations:
        return "No violations found"
    
    result = []
    for i, violation in enumerate(violations, 1):
        eo = violation.get('executive_order', 'Unknown EO')
        section = violation.get('section', 'Unknown section')
        description = violation.get('description', 'No description')
        severity = violation.get('severity', 'MEDIUM')
        
        result.append(
            f"{i}. **{eo}** - {section}\n"
            f"   Severity: {severity}\n"
            f"   {description}\n"
        )
    
    return "\n".join(result)

def format_score(score: float, max_score: float = 100) -> str:
    """
    Format a score with visual indicator.
    
    Args:
        score: The score value
        max_score: Maximum possible score
        
    Returns:
        Formatted score string with indicator
    """
    percentage = (score / max_score) * 100
    
    if percentage >= 90:
        indicator = "🟢"
    elif percentage >= 70:
        indicator = "🟡"
    elif percentage >= 50:
        indicator = "🟠"
    else:
        indicator = "🔴"
    
    return f"{indicator} {score:.1f}/{max_score} ({percentage:.1f}%)"

def format_list_items(items: List[str], numbered: bool = True) -> str:
    """
    Format a list of items as a string.
    
    Args:
        items: List of strings
        numbered: Whether to use numbered list
        
    Returns:
        Formatted string
    """
    if not items:
        return "None"
    
    if numbered:
        return "\n".join(f"{i}. {item}" for i, item in enumerate(items, 1))
    else:
        return "\n".join(f"• {item}" for item in items)

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to a maximum length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix
