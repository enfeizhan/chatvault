# Custom Backend Examples

This guide shows how to implement your own storage and message backends for ChatVault using AWS services as examples.

## Overview

ChatVault uses two abstract base classes that you can extend:

- `FilesBackend` - For file storage (S3, GCS, Azure Blob, etc.)
- `MessagesBackend` - For conversation persistence (DynamoDB, PostgreSQL, Redis, etc.)

---

## Example 1: AWS S3 Files Backend

Here's how to create a custom backend for storing files in AWS S3:

```python
"""Custom S3 files backend for ChatVault."""

import boto3
from botocore.exceptions import ClientError
from typing import Optional
from chatvault.backends import FilesBackend


class S3Files(FilesBackend):
    """
    Store conversation attachments in AWS S3.
    
    Usage:
        files = S3Files(bucket="my-chat-files", region_name="us-east-1")
        vault = ChatVault(messages=..., files=files)
    """
    
    def __init__(self, bucket: str, region_name: Optional[str] = None, **kwargs):
        self.bucket = bucket
        self.s3 = boto3.client("s3", region_name=region_name, **kwargs)
    
    def upload(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> None:
        """Upload a file to S3."""
        self.s3.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=data,
            ContentType=content_type
        )
    
    def download(self, key: str) -> Optional[bytes]:
        """Download a file from S3."""
        try:
            response = self.s3.get_object(Bucket=self.bucket, Key=key)
            return response["Body"].read()
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                return None
            raise
    
    def delete(self, key: str) -> bool:
        """Delete a file from S3."""
        try:
            self.s3.delete_object(Bucket=self.bucket, Key=key)
            return True
        except ClientError:
            return False
    
    def exists(self, key: str) -> bool:
        """Check if a file exists in S3."""
        try:
            self.s3.head_object(Bucket=self.bucket, Key=key)
            return True
        except ClientError:
            return False
    
    def get_signed_url(
        self, 
        key: str, 
        expires_in: int = 3600,
        download_filename: Optional[str] = None,
    ) -> Optional[str]:
        """Generate a presigned S3 URL for downloading."""
        params = {"Bucket": self.bucket, "Key": key}
        
        if download_filename:
            params["ResponseContentDisposition"] = f'attachment; filename="{download_filename}"'
            
        try:
            return self.s3.generate_presigned_url("get_object", Params=params, ExpiresIn=expires_in)
        except ClientError:
            return None
```

---

## Example 2: AWS DynamoDB Messages Backend

Here's how to store conversations in DynamoDB:

```python
"""Custom DynamoDB messages backend for ChatVault."""

import json
from datetime import datetime
from typing import Optional, List
import boto3
from botocore.exceptions import ClientError
from chatvault.backends import MessagesBackend
from chatvault.conversation import Conversation, Message, FileAttachment


class DynamoMessages(MessagesBackend):
    """
    Store conversations in AWS DynamoDB.
    
    Table Schema:
    - Partition Key: conversation_id (String)
    - GSI: user_id-index (Partition Key: user_id) for get_by_user()
    
    Usage:
        messages = DynamoMessages(table_name="Conversations", region_name="us-east-1")
        vault = ChatVault(messages=messages, files=...)
    """
    
    def __init__(self, table_name: str, region_name: Optional[str] = None, **kwargs):
        self.dynamodb = boto3.resource("dynamodb", region_name=region_name, **kwargs)
        self.table = self.dynamodb.Table(table_name)
    
    def save(self, conversation: Conversation) -> None:
        """Save a conversation to DynamoDB."""
        self.table.put_item(Item={
            "conversation_id": conversation.conversation_id,
            "user_id": conversation.user_id or "",
            "title": conversation.title,
            "messages": json.dumps([m.to_dict() for m in conversation._messages]),
            "files": json.dumps([f.to_dict() for f in conversation._files]),
            "created_at": int(conversation.created_at.timestamp()),
            "last_active": int(conversation.last_active.timestamp()),
            "metadata": json.dumps(conversation.metadata),
        })
    
    def get(self, conversation_id: str) -> Optional[Conversation]:
        """Load a conversation from DynamoDB."""
        try:
            response = self.table.get_item(Key={"conversation_id": conversation_id})
            item = response.get("Item")
            if not item:
                return None
            return self._item_to_conversation(item)
        except ClientError:
            return None
    
    def get_by_user(self, user_id: str) -> List[Conversation]:
        """Get all conversations for a user using a GSI."""
        try:
            response = self.table.query(
                IndexName="user_id-index",
                KeyConditionExpression="user_id = :uid",
                ExpressionAttributeValues={":uid": user_id}
            )
            return [self._item_to_conversation(item) for item in response.get("Items", [])]
        except ClientError:
            return []
    
    def delete(self, conversation_id: str) -> bool:
        """Delete a conversation from DynamoDB."""
        try:
            self.table.delete_item(Key={"conversation_id": conversation_id})
            return True
        except ClientError:
            return False
    
    def _item_to_conversation(self, item: dict) -> Conversation:
        """Convert a DynamoDB item to a Conversation object."""
        return Conversation(
            conversation_id=item["conversation_id"],
            user_id=item.get("user_id") or None,
            title=item.get("title", ""),
            created_at=datetime.fromtimestamp(int(item.get("created_at", 0))),
            messages=[Message.from_dict(m) for m in json.loads(item.get("messages", "[]"))],
            files=[FileAttachment.from_dict(f) for f in json.loads(item.get("files", "[]"))],
            metadata=json.loads(item.get("metadata", "{}")),
        )
```

---

## Putting It Together

Once you've created your custom backends, use them like this:

```python
from chatvault import ChatVault

# Your custom backends
from my_project.backends import S3Files, DynamoMessages

vault = ChatVault(
    messages=DynamoMessages(table_name="Conversations", region_name="us-east-1"),
    files=S3Files(bucket="my-chat-attachments", region_name="us-east-1")
)

# Use the vault as normal
conversation = vault.create_conversation(user_id="user-123")
conversation.add_message("user", "Hello!")
```

---

## Tips

1. **Lazy Loading**: Only install the dependencies you need (e.g., `boto3` for AWS).
2. **Error Handling**: Wrap cloud API calls in try/except to handle transient failures.
3. **Credentials**: Use environment variables or IAM roles for production credentials.
4. **Testing**: Use `MemoryMessages` and `LocalFiles` for local development and tests.
