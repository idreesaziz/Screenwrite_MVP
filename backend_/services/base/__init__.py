"""Services base package - Abstract provider interfaces."""

from services.base.ChatProvider import ChatProvider, ChatMessage, ChatResponse
from services.base.StorageProvider import StorageProvider, StorageFile, UploadResult

__all__ = [
    'ChatProvider',
    'ChatMessage',
    'ChatResponse',
    'StorageProvider',
    'StorageFile',
    'UploadResult',
]
