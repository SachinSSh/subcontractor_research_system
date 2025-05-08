import os
import logging
import json
import csv
import io
from typing import List, Dict, Any
from datetime import datetime

def get_env_var(name: str, default: str = None) -> str:
    """Get environment variable with fallback to default"""
    return os.environ.get(name, default)

def setup_logging() -> logging.Logger:
    """Configure logging for the application"""
    logger = logging.getLogger("subcontractor_research")
    
    # Configure logging level based on environment
    log_level = get_env_var("LOG_LEVEL", "INFO")
    logger.setLevel(getattr(logging, log_level))
    
    # Create console handler
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger

def export_results_to_csv(results: List[Dict[str, Any]], filename: str) -> str:
    """Export research results to CSV file"""
    if not results:
        return ""
        
    # Define field order
    fields = [
        "name", "website", "email", "phone_number", "city", "state",
        "lic_active", "lic_number", "bond_amount", "tx_projects_past_5yrs",
        "score", "evidence_url", "evidence_text", "last_checked"
    ]
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    
    for result in results:
        # Only include fields that exist in our field list
        row = {field: result.get(field, "") for field in fields}
        writer.writerow(row)
    
    # Save to file
    with open(filename, 'w', newline='') as file:
        file.write(output.getvalue())
    
    return output.getvalue()

def generate_markdown_table(results: List[Dict[str, Any]], limit: int = 10) -> str:
    """Generate markdown table of top results"""
    if not results:
        return "No results found."
        
    # Limit to top N results
    top_results = results[:limit]
    
    # Build table header
    table = "| Rank | Company | Location | License | Bond | TX Projects | Score |\n"
    table += "|------|---------|----------|---------|------|-------------|-------|\n"
    
    # Add rows
    for i, result in enumerate(top_results):
        name = result.get("name", "Unknown")
        location = f"{result.get('city', 'Unknown')}, {result.get('state', '')}"
        
        # Format license status
        license_status = "Active" if result.get("lic_active") else "Inactive"
        if result.get("lic_number"):
            license_status += f" ({result.get('lic_number')})"
        
        # Format bond amount
        bond = "Unknown"
        if result.get("bond_amount"):
            bond_amount = result.get("bond_amount")
            if bond_amount >= 1000000:
                bond = f"${bond_amount/1000000:.1f}M"
            else:
                bond = f"${bond_amount:,}"
        
        # Format projects
        projects = result.get("tx_projects_past_5yrs", 0)
        
        # Format score
        score = result.get("score", 0)
        
        # Add row to table
        table += f"| {i+1} | {name} | {location} | {license_status} | {bond} | {projects} | {score} |\n"
    
    return table
