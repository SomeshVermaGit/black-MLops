"""
Real-time Collaborative Code Editor Service
Adapted from BroCode project
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import asyncio


@dataclass
class User:
    id: str
    username: str
    cursor_position: int = 0
    connected_at: datetime = field(default_factory=datetime.now)


@dataclass
class Operation:
    """Represents a text operation (insert/delete)"""
    type: str  # 'insert' or 'delete'
    position: int
    content: str
    user_id: str
    version: int
    timestamp: datetime = field(default_factory=datetime.now)


class Document:
    """Represents a collaborative document"""

    def __init__(self, doc_id: str, initial_content: str = ""):
        self.id = doc_id
        self.content = initial_content
        self.version = 0
        self.operations_history: List[Operation] = []

    def apply_operation(self, operation: Operation) -> bool:
        """Apply an operation to the document"""
        try:
            if operation.type == 'insert':
                self.content = (
                    self.content[:operation.position] +
                    operation.content +
                    self.content[operation.position:]
                )
            elif operation.type == 'delete':
                end_pos = operation.position + len(operation.content)
                self.content = (
                    self.content[:operation.position] +
                    self.content[end_pos:]
                )

            self.version += 1
            self.operations_history.append(operation)
            return True
        except Exception as e:
            print(f"Error applying operation: {e}")
            return False


class OperationalTransform:
    """Operational Transform for conflict resolution"""

    @staticmethod
    def transform(op1: Operation, op2: Operation) -> Operation:
        """Transform op2 against op1 for concurrent operations"""
        if op1.type == 'insert' and op2.type == 'insert':
            if op1.position <= op2.position:
                # Adjust op2 position
                op2.position += len(op1.content)
        elif op1.type == 'delete' and op2.type == 'insert':
            if op1.position < op2.position:
                op2.position -= len(op1.content)
        elif op1.type == 'insert' and op2.type == 'delete':
            if op1.position <= op2.position:
                op2.position += len(op1.content)

        return op2


class CollaborativeSession:
    """Manages a collaborative editing session"""

    def __init__(self, session_id: str, document_id: str):
        self.id = session_id
        self.document = Document(document_id)
        self.users: Dict[str, User] = {}
        self.pending_operations: List[Operation] = []

    def add_user(self, user: User):
        """Add user to session"""
        self.users[user.id] = user
        print(f"👤 User {user.username} joined session {self.id}")

    def remove_user(self, user_id: str):
        """Remove user from session"""
        if user_id in self.users:
            user = self.users.pop(user_id)
            print(f"👋 User {user.username} left session {self.id}")

    async def process_operation(self, operation: Operation) -> Dict[str, Any]:
        """Process incoming operation with OT"""
        # Transform against pending operations
        transformed_op = operation
        for pending_op in self.pending_operations:
            transformed_op = OperationalTransform.transform(pending_op, transformed_op)

        # Apply to document
        success = self.document.apply_operation(transformed_op)

        if success:
            # Broadcast to other users
            return {
                "success": True,
                "operation": transformed_op,
                "document_version": self.document.version,
                "content": self.document.content
            }
        else:
            return {"success": False, "error": "Failed to apply operation"}

    def get_state(self) -> Dict[str, Any]:
        """Get current session state"""
        return {
            "session_id": self.id,
            "document_id": self.document.id,
            "content": self.document.content,
            "version": self.document.version,
            "users": [
                {"id": u.id, "username": u.username, "cursor": u.cursor_position}
                for u in self.users.values()
            ]
        }


class CollabEditorService:
    """Main collaborative editor service"""

    def __init__(self):
        self.sessions: Dict[str, CollaborativeSession] = {}

    def create_session(self, session_id: str, document_id: str) -> CollaborativeSession:
        """Create or get existing session"""
        if session_id not in self.sessions:
            self.sessions[session_id] = CollaborativeSession(session_id, document_id)
            print(f"📝 Created new session: {session_id}")
        return self.sessions[session_id]

    def get_session(self, session_id: str) -> Optional[CollaborativeSession]:
        """Get existing session"""
        return self.sessions.get(session_id)

    async def join_session(
        self,
        session_id: str,
        user_id: str,
        username: str
    ) -> Dict[str, Any]:
        """User joins a session"""
        session = self.get_session(session_id)
        if not session:
            return {"success": False, "error": "Session not found"}

        user = User(id=user_id, username=username)
        session.add_user(user)

        return {
            "success": True,
            "session_state": session.get_state()
        }

    async def handle_operation(
        self,
        session_id: str,
        operation: Operation
    ) -> Dict[str, Any]:
        """Handle incoming operation"""
        session = self.get_session(session_id)
        if not session:
            return {"success": False, "error": "Session not found"}

        result = await session.process_operation(operation)
        return result
