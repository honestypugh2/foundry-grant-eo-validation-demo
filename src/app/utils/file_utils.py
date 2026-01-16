"""
File utility functions for document handling.
"""

import os
import tempfile
from pathlib import Path
from typing import Optional

def save_uploaded_file(uploaded_file, directory: Optional[str] = None) -> str:
    """
    Save an uploaded file to a directory.
    
    Args:
        uploaded_file: Streamlit UploadedFile object
        directory: Target directory (uses temp if None)
        
    Returns:
        Path to saved file
    """
    if directory is None:
        directory = tempfile.gettempdir()
    
    # Create directory if it doesn't exist
    os.makedirs(directory, exist_ok=True)
    
    # Save file
    file_path = os.path.join(directory, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    return file_path

def get_file_extension(filename: str) -> str:
    """
    Get the file extension from a filename.
    
    Args:
        filename: Name of the file
        
    Returns:
        File extension (lowercase, with dot)
    """
    return Path(filename).suffix.lower()

def validate_file_type(filename: str, allowed_extensions: Optional[list] = None) -> bool:
    """
    Validate if a file type is allowed.
    
    Args:
        filename: Name of the file
        allowed_extensions: List of allowed extensions (e.g., ['.pdf', '.docx'])
        
    Returns:
        True if valid, False otherwise
    """
    if allowed_extensions is None:
        allowed_extensions = ['.pdf', '.docx', '.txt']
    
    ext = get_file_extension(filename)
    return ext in allowed_extensions

def get_file_size_mb(file_path: str) -> float:
    """
    Get file size in megabytes.
    
    Args:
        file_path: Path to the file
        
    Returns:
        File size in MB
    """
    size_bytes = os.path.getsize(file_path)
    return size_bytes / (1024 * 1024)

def cleanup_temp_file(file_path: str) -> bool:
    """
    Delete a temporary file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
    except Exception:
        pass
    return False
