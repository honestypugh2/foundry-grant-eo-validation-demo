#!/usr/bin/env python3
"""
Generate Grant Proposal Compliance Automation Architecture Diagram
Based on the solution architecture described in README.md
"""

from pathlib import Path
from diagrams import Diagram, Cluster, Edge
from diagrams.azure.storage import BlobStorage, StorageAccounts
from diagrams.azure.ml import CognitiveServices
from diagrams.azure.aimachinelearning import CognitiveSearch, AIStudio, AzureOpenai
from diagrams.azure.compute import FunctionApps
from diagrams.onprem.client import Users, User

# Determine output path - always relative to project root
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
OUTPUT_DIR = PROJECT_ROOT / "images"
OUTPUT_PATH = OUTPUT_DIR / "architecture_diagram"

# Ensure output directory exists
OUTPUT_DIR.mkdir(exist_ok=True)

# Configure diagram
graph_attr = {
    "fontsize": "14",
    "bgcolor": "white",
    "pad": "0.5",
    "splines": "polyspline",
}

node_attr = {
    "fontsize": "12",
}

edge_attr = {
    "fontsize": "10",
}

with Diagram(
    "Grant Proposal Compliance Automation Architecture",
    filename=str(OUTPUT_PATH),
    direction="LR",
    graph_attr=graph_attr,
    node_attr=node_attr,
    edge_attr=edge_attr,
    show=False,
):
    # Input Sources
    departments = Users("County Departments")
    document_submission = StorageAccounts("Documents\n(Email/Forms)")
    
    # Storage Layer
    with Cluster("Document Storage"):
        sharepoint = StorageAccounts("SharePoint\nStorage")
        blob_storage = BlobStorage("Azure Blob\nStorage")
    
    # Azure AI Foundry Processing
    with Cluster("Azure AI Foundry Processing"):
        # Document Processing
        with Cluster("Document Processing"):
            doc_intelligence = CognitiveServices("Azure Document\nIntelligence\n(OCR/Extract)")
            ai_search = CognitiveSearch("Azure AI Search\n(Semantic)")
        
        # AI Agents
        with Cluster("AI Agents"):
            ai_foundry = AIStudio("Azure AI Foundry")
            compliance_agent = AzureOpenai("Compliance Agent\n• Query knowledge base\n• Generate summary\n• Provide citations")
    
    # Notification Layer
    with Cluster("Notification & Review"):
        function_apps = FunctionApps("Azure Function Apps\n(Email Notifications)")
        attorney = User("Attorney\nReview &\nValidation")
    
    # Output
    client = User("Client\nNotification")
    
    # Flow connections
    departments >> Edge(label="Submit") >> document_submission  # type: ignore # noqa
    document_submission >> Edge(label="Store") >> sharepoint # type: ignore
    sharepoint >> Edge(label="Process") >> doc_intelligence # type: ignore
    
    # Alternative storage path
    document_submission >> Edge(label="Upload", style="dashed") >> blob_storage # type: ignore
    blob_storage >> Edge(label="Process", style="dashed") >> doc_intelligence # type: ignore
    
    # Document processing flow
    doc_intelligence >> Edge(label="Extract &\nIndex") >> ai_search # type: ignore
    ai_search >> Edge(label="Semantic\nRetrieval") >> ai_foundry # type: ignore
    ai_foundry >> Edge(label="Orchestrate") >> compliance_agent # type: ignore
    
    # Notification flow
    compliance_agent >> Edge(label="Analysis\nResults") >> function_apps # type: ignore
    function_apps >> Edge(label="Email\nNotification") >> attorney # type: ignore
    
    # Review and response
    attorney >> Edge(label="Validated\nDecision") >> client # type: ignore

print("✅ Architecture diagram generated successfully!")
print(f"📊 Output file: {OUTPUT_PATH}.png")

# Verify file was created
if (OUTPUT_PATH.parent / f"{OUTPUT_PATH.name}.png").exists():
    file_size = (OUTPUT_PATH.parent / f"{OUTPUT_PATH.name}.png").stat().st_size
    print(f"✓ File size: {file_size:,} bytes")
else:
    print("⚠️  Warning: Output file not found!")
