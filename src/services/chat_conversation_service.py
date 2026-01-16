from typing import Optional, List
from datetime import datetime
from ..models.chat_conversation import ChatConversation, ChatConversationCreate, ChatConversationUpdate, Message


class ChatConversationService:
    def __init__(self):
        # In a real implementation, this would connect to a database
        # For now, using in-memory storage for demonstration
        self.conversations_db = {}

    async def get_conversation(self, conversation_id: str) -> Optional[ChatConversation]:
        """Get a conversation by ID"""
        conv_data = self.conversations_db.get(conversation_id)
        if conv_data:
            return ChatConversation(**conv_data)
        return None

    async def create_conversation(self, conversation: ChatConversationCreate) -> ChatConversation:
        """Create a new conversation"""
        import uuid
        conv_id = str(uuid.uuid4())
        now = datetime.now()
        conv_data = {
            "id": conv_id,
            "user_id": conversation.user_id,
            "messages": [msg.dict() for msg in conversation.messages],
            "created_at": now,
            "updated_at": now
        }
        self.conversations_db[conv_id] = conv_data
        return ChatConversation(**conv_data)

    async def update_conversation(self, conversation_id: str, update_data: ChatConversationUpdate) -> Optional[ChatConversation]:
        """Update a conversation"""
        existing = await self.get_conversation(conversation_id)
        if not existing:
            return None

        conv_data = self.conversations_db[conversation_id]
        if update_data.messages is not None:
            conv_data["messages"] = [msg.dict() for msg in update_data.messages]
        conv_data["updated_at"] = datetime.now()

        self.conversations_db[conversation_id] = conv_data
        return ChatConversation(**conv_data)

    async def add_message(self, conversation_id: str, message: Message) -> Optional[ChatConversation]:
        """Add a message to a conversation"""
        existing = await self.get_conversation(conversation_id)
        if not existing:
            return None

        conv_data = self.conversations_db[conversation_id]
        conv_data["messages"].append(message.dict())
        conv_data["updated_at"] = datetime.now()

        self.conversations_db[conversation_id] = conv_data
        return ChatConversation(**conv_data)

    async def get_user_conversations(self, user_id: str) -> List[ChatConversation]:
        """Get all conversations for a user"""
        user_convs = []
        for conv_id, conv_data in self.conversations_db.items():
            if conv_data.get("user_id") == user_id:
                user_convs.append(ChatConversation(**conv_data))
        return user_convs