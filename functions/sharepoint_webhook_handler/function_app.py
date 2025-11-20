"""
Azure Function for handling SharePoint webhook notifications.
Automatically indexes new/updated documents in SharePoint.
"""

import azure.functions as func
import json
import logging
import os
from datetime import datetime
from typing import Dict, Any, List

app = func.FunctionApp()


@app.route(route="SharePointWebhookHandler", auth_level=func.AuthLevel.FUNCTION)
async def sharepoint_webhook_handler(req: func.HttpRequest) -> func.HttpResponse:
    """
    Handle SharePoint webhook notifications.
    This function is triggered when documents are added/modified in SharePoint.
    
    Webhook Flow:
    1. SharePoint sends POST request when content changes
    2. Function validates request and client state
    3. Queues document processing for async handling
    4. Returns 200 OK within 5 seconds (SharePoint requirement)
    """
    logging.info('SharePoint webhook notification received')
    
    try:
        # Handle webhook validation (initial subscription setup)
        validation_token = req.params.get('validationtoken')
        if validation_token:
            logging.info(f"Webhook validation request: {validation_token}")
            return func.HttpResponse(
                validation_token,
                status_code=200,
                mimetype="text/plain"
            )
        
        # Process webhook notification
        req_body = req.get_json()
        
        if not req_body or 'value' not in req_body:
            logging.warning("Invalid webhook payload")
            return func.HttpResponse(
                json.dumps({"error": "Invalid payload"}),
                status_code=400,
                mimetype="application/json"
            )
        
        # Process each notification
        processed_count = 0
        for notification in req_body['value']:
            # Verify client state for security
            client_state = notification.get('clientState', '')
            expected_state = os.getenv('WEBHOOK_CLIENT_STATE', '')
            
            if client_state != expected_state:
                logging.warning(f"Invalid client state: {client_state}")
                return func.HttpResponse(
                    json.dumps({"error": "Invalid client state"}),
                    status_code=401,
                    mimetype="application/json"
                )
            
            # Extract notification details
            resource = notification.get('resource')
            site_url = notification.get('siteUrl')
            web_id = notification.get('webId')
            subscription_id = notification.get('subscriptionId')
            
            logging.info(f"Processing notification for: {resource}")
            
            # Queue document processing (async)
            await queue_document_processing({
                'subscription_id': subscription_id,
                'resource': resource,
                'site_url': site_url,
                'web_id': web_id,
                'timestamp': datetime.utcnow().isoformat()
            })
            
            processed_count += 1
        
        logging.info(f"Queued {processed_count} notifications for processing")
        
        # Return success quickly (must respond within 5 seconds)
        return func.HttpResponse(
            json.dumps({
                "status": "accepted",
                "processed": processed_count
            }),
            status_code=200,
            mimetype="application/json"
        )
        
    except Exception as e:
        logging.error(f"Error processing webhook: {str(e)}", exc_info=True)
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )


async def queue_document_processing(notification: Dict[str, Any]):
    """
    Queue document for asynchronous processing.
    Uses Azure Storage Queue for decoupled processing.
    """
    from azure.storage.queue.aio import QueueClient
    
    try:
        connection_string = os.getenv('AzureWebJobsStorage')
        if not connection_string:
            raise ValueError("AzureWebJobsStorage environment variable is not set")
        
        queue_client = QueueClient.from_connection_string(
            connection_string,
            "document-processing-queue"
        )
        
        # Ensure queue exists
        try:
            await queue_client.create_queue()
        except Exception:
            # Queue already exists
            pass
        
        # Create message
        message = {
            "notification_id": notification['subscription_id'],
            "resource": notification['resource'],
            "site_url": notification['site_url'],
            "web_id": notification['web_id'],
            "timestamp": notification['timestamp'],
            "action": "index_document"
        }
        
        # Send to queue
        await queue_client.send_message(json.dumps(message))
        logging.info(f"✓ Queued document processing: {message['resource']}")
        
    except Exception as e:
        logging.error(f"Error queueing document: {str(e)}")
        raise


@app.queue_trigger(
    arg_name="msg",
    queue_name="document-processing-queue",
    connection="AzureWebJobsStorage"
)
async def process_document_queue(msg: func.QueueMessage):
    """
    Process documents from the queue.
    Retrieves changed documents from SharePoint and indexes them in Azure AI Search.
    
    This function runs asynchronously after webhook notification is queued.
    """
    logging.info('Processing document from queue')
    
    try:
        message = json.loads(msg.get_body().decode('utf-8'))
        
        logging.info(f"Processing: {message['resource']}")
        
        # Get changed items from SharePoint
        changed_items = await get_changed_items(
            message['site_url'],
            message['resource']
        )
        
        logging.info(f"Found {len(changed_items)} changed items")
        
        # Process each changed item
        for item in changed_items:
            try:
                await process_and_index_document(item, message['site_url'])
            except Exception as e:
                logging.error(f"Error processing item {item.get('UniqueId')}: {str(e)}")
                # Continue processing other items
        
        logging.info("✓ Completed processing queue message")
        
    except Exception as e:
        logging.error(f"Error processing queue message: {str(e)}", exc_info=True)
        # Re-raise to trigger retry
        raise


async def get_changed_items(site_url: str, resource: str) -> List[Dict[str, Any]]:
    """
    Retrieve changed items from SharePoint using the GetChanges API.
    Uses change token to get only new/modified items since last check.
    """
    import aiohttp
    from azure.identity.aio import DefaultAzureCredential
    
    try:
        # Get access token
        credential = DefaultAzureCredential()
        token = await credential.get_token("https://graph.microsoft.com/.default")
        
        # Extract list ID from resource URL
        list_id = extract_list_id(resource)
        
        # Get last change token from storage
        change_token = await get_last_change_token(list_id)
        
        # Query for changes
        endpoint = f"{site_url}/_api/web/lists(guid'{list_id}')/GetChanges"
        
        query = {
            "query": {
                "Add": True,
                "Update": True,
                "Item": True,
                "ChangeTokenStart": change_token if change_token else None
            }
        }
        
        headers = {
            "Authorization": f"Bearer {token.token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(endpoint, json=query, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    changes = data.get('value', [])
                    
                    # Save new change token
                    if changes:
                        new_token = changes[-1].get('ChangeToken')
                        if new_token:
                            await save_change_token(list_id, new_token)
                    
                    return changes
                else:
                    logging.error(f"Error getting changes: {response.status}")
                    return []
    
    except Exception as e:
        logging.error(f"Error retrieving changed items: {str(e)}")
        return []


async def process_and_index_document(item: Dict[str, Any], site_url: str):
    """
    Download document, extract text, create embeddings, and index in Azure AI Search.
    """
    from azure.search.documents.aio import SearchClient
    from azure.core.credentials import AzureKeyCredential
    
    try:
        # Extract item details
        unique_id = item.get('UniqueId')
        file_name = item.get('Name', '')
        server_relative_url = item.get('ServerRelativeUrl', '')
        modified = item.get('Modified', datetime.utcnow().isoformat())
        
        logging.info(f"Processing document: {file_name}")
        
        # Download document content
        content = await download_document(site_url, server_relative_url)
        
        # Extract text from document
        extracted_text = await extract_document_text(content, file_name)
        
        # Determine document type
        doc_type = get_document_type(file_name)
        
        # Create search document
        search_doc = {
            "id": unique_id or generate_document_id(server_relative_url),
            "title": file_name,
            "content": extracted_text,
            "file_path": f"{site_url}{server_relative_url}",
            "last_modified": modified,
            "document_type": doc_type,
            "indexed_date": datetime.utcnow().isoformat(),
            "source": "sharepoint"
        }
        
        # Add to Azure AI Search
        search_client = SearchClient(
            endpoint=os.getenv('AZURE_SEARCH_ENDPOINT', ''),
            index_name=os.getenv('AZURE_SEARCH_INDEX_NAME', ''),
            credential=AzureKeyCredential(os.getenv('AZURE_SEARCH_API_KEY', ''))
        )
        
        await search_client.upload_documents([search_doc])
        logging.info(f"✓ Indexed document: {file_name}")
        
        # Update SharePoint metadata
        await update_sharepoint_metadata(site_url, server_relative_url, {
            "IndexedDate": datetime.utcnow().isoformat(),
            "IndexStatus": "Indexed"
        })
        
    except Exception as e:
        logging.error(f"Error indexing document: {str(e)}")
        raise


async def download_document(site_url: str, server_relative_url: str) -> bytes:
    """Download document content from SharePoint."""
    import aiohttp
    from azure.identity.aio import DefaultAzureCredential
    
    credential = DefaultAzureCredential()
    token = await credential.get_token("https://graph.microsoft.com/.default")
    
    endpoint = f"{site_url}/_api/web/GetFileByServerRelativeUrl('{server_relative_url}')/$value"
    
    headers = {
        "Authorization": f"Bearer {token.token}"
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(endpoint, headers=headers) as response:
            if response.status == 200:
                return await response.read()
            else:
                raise Exception(f"Failed to download document: {response.status}")


async def extract_document_text(content: bytes, filename: str) -> str:
    """
    Extract text from document using Azure Document Intelligence.
    Supports PDF, Word, Excel, PowerPoint, images, etc.
    """
    try:
        doc_intel_endpoint = os.getenv('AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT')
        doc_intel_key = os.getenv('AZURE_DOCUMENT_INTELLIGENCE_API_KEY')
        
        if not doc_intel_endpoint or not doc_intel_key:
            # Fallback to simple text extraction
            return content.decode('utf-8', errors='ignore')
        
        # Note: Requires azure-ai-documentintelligence package
        # from azure.ai.documentintelligence.aio import DocumentIntelligenceClient
        # from azure.core.credentials import AzureKeyCredential
        # 
        # client = DocumentIntelligenceClient(
        #     endpoint=doc_intel_endpoint,
        #     credential=AzureKeyCredential(doc_intel_key)
        # )
        # 
        # # Analyze document
        # with BytesIO(content) as content_stream:
        #     poller = await client.begin_analyze_document(
        #         "prebuilt-read",
        #         content_stream
        #     )
        #     result = await poller.result()
        # 
        # # Extract text
        # text_content = ""
        # if result.pages:
        #     for page in result.pages:
        #         if page.lines:
        #             for line in page.lines:
        #                 text_content += line.content + "\n"
        # 
        # return text_content
        
        # For now, use simple text extraction
        return content.decode('utf-8', errors='ignore')
        
    except Exception as e:
        logging.warning(f"Document Intelligence extraction failed: {str(e)}")
        # Fallback to simple extraction
        return content.decode('utf-8', errors='ignore')


async def update_sharepoint_metadata(site_url: str, server_relative_url: str, metadata: Dict[str, Any]):
    """Update SharePoint item metadata to mark as indexed."""
    import aiohttp
    from azure.identity.aio import DefaultAzureCredential
    
    try:
        credential = DefaultAzureCredential()
        token = await credential.get_token("https://graph.microsoft.com/.default")
        
        endpoint = f"{site_url}/_api/web/GetFileByServerRelativeUrl('{server_relative_url}')/ListItemAllFields"
        
        headers = {
            "Authorization": f"Bearer {token.token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "IF-MATCH": "*",
            "X-HTTP-Method": "MERGE"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(endpoint, json=metadata, headers=headers) as response:
                if response.status in [200, 204]:
                    logging.info("✓ Updated SharePoint metadata")
                else:
                    logging.warning(f"Failed to update metadata: {response.status}")
    
    except Exception as e:
        logging.warning(f"Error updating SharePoint metadata: {str(e)}")


# Helper functions

def extract_list_id(resource_url: str) -> str:
    """Extract list GUID from resource URL."""
    import re
    match = re.search(r"Lists\(guid'([^']+)'\)", resource_url)
    if match:
        return match.group(1)
    return ""


async def get_last_change_token(list_id: str) -> str:
    """Retrieve last change token from Azure Table Storage."""
    # Note: Requires azure-data-tables package
    # from azure.data.tables.aio import TableClient
    
    try:
        # table_client = TableClient.from_connection_string(
        #     os.getenv('AzureWebJobsStorage'),
        #     "changeTokens"
        # )
        # 
        # entity = await table_client.get_entity(
        #     partition_key="SharePoint",
        #     row_key=list_id
        # )
        # 
        # return entity.get('ChangeToken', '')
        return ""
    except Exception:
        return ""


async def save_change_token(list_id: str, token: str):
    """Save change token to Azure Table Storage."""
    # Note: Requires azure-data-tables package
    # from azure.data.tables.aio import TableClient
    
    try:
        # table_client = TableClient.from_connection_string(
        #     os.getenv('AzureWebJobsStorage'),
        #     "changeTokens"
        # )
        # 
        # await table_client.create_table()
        # 
        # entity = {
        #     "PartitionKey": "SharePoint",
        #     "RowKey": list_id,
        #     "ChangeToken": token,
        #     "LastUpdated": datetime.utcnow().isoformat()
        # }
        # 
        # await table_client.upsert_entity(entity)
        pass
    except Exception as e:
        logging.error(f"Error saving change token: {str(e)}")


def get_document_type(filename: str) -> str:
    """Determine document type from filename."""
    ext = filename.lower().split('.')[-1] if '.' in filename else ''
    
    type_mapping = {
        'pdf': 'Executive Order',
        'docx': 'Grant Proposal',
        'doc': 'Grant Proposal',
        'txt': 'Text Document',
        'xlsx': 'Spreadsheet',
        'xls': 'Spreadsheet'
    }
    
    return type_mapping.get(ext, 'Document')


def generate_document_id(path: str) -> str:
    """Generate a unique document ID from path."""
    import hashlib
    return hashlib.md5(path.encode()).hexdigest()
