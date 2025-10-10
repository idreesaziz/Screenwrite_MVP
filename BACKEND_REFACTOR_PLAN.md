# Backend Refactor Plan

## Overview
This document outlines the comprehensive refactoring of the Screenwrite backend from a monolithic structure to a clean 3-tier architecture with strict naming conventions and semantic consistency.

---

## 1. Naming Conventions & Style Guide

### 1.1 Directory Naming
- **Pattern**: `snake_case`, descriptive, plural for collections
- **Examples**:
  - `services/` - collection of service modules
  - `api/` - collection of API routes
  - `business_logic/` - collection of business logic modules
  - `tests/` - collection of test modules
  - `core/` - core utilities and configuration

### 1.2 File Naming

#### Python Class Files
- **Pattern**: `PascalCase` matching the primary class name
- **Structure**: `{ServiceName}{BaseClassName}.py`
- **Examples**:
  - `ChatProvider.py` - contains `ChatProvider` base class
  - `GeminiChatProvider.py` - contains `GeminiChatProvider` class
  - `StorageProvider.py` - contains `StorageProvider` base class
  - `GCStorageProvider.py` - contains `GCStorageProvider` class

#### Utility/Module Files
- **Pattern**: `snake_case`, descriptive
- **Examples**:
  - `config.py` - configuration management
  - `security.py` - security utilities
  - `logger.py` - logging setup
  - `dependencies.py` - FastAPI dependency injection setup

### 1.3 Class Naming

#### Base Classes (Abstract)
- **Pattern**: `{Capability}Provider`
- **Examples**:
  - `ChatProvider` - abstract base for chat/LLM providers
  - `ImageGenerationProvider` - abstract base for image generation
  - `VideoGenerationProvider` - abstract base for video generation
  - `MediaProvider` - abstract base for stock media APIs
  - `StorageProvider` - abstract base for cloud storage

#### Implementation Classes
- **Pattern**: `{ServiceName}{BaseClassName}`
- **Examples**:
  - `GeminiChatProvider` - Gemini implementation of ChatProvider
  - `ImagenGenerationProvider` - Imagen implementation of ImageGenerationProvider
  - `VEOGenerationProvider` - Veo implementation of VideoGenerationProvider
  - `PexelsMediaProvider` - Pexels implementation of MediaProvider
  - `GCStorageProvider` - Google Cloud Storage implementation of StorageProvider

#### Business Logic Classes
- **Pattern**: `{Domain}{Purpose}Service` or `{Domain}Manager`
- **Examples**:
  - `VideoAnalysisService` - handles video analysis logic
  - `ContentGenerationService` - handles content generation orchestration
  - `CompositionManager` - manages composition creation and validation
  - `BlueprintParserService` - handles blueprint parsing

### 1.4 Function/Method Naming

#### Service Provider Methods
- **Pattern**: `verb_noun` or `verb_object_modifier`
- **Consistency**: All providers implementing the same base class must have identical method signatures
- **Examples**:
  ```python
  # ChatProvider methods
  async def generate_chat_response(self, messages: List[Message], **kwargs) -> ChatResponse
  async def stream_chat_response(self, messages: List[Message], **kwargs) -> AsyncIterator[str]
  
  # StorageProvider methods
  async def upload_file(self, file_path: str, destination: str, **kwargs) -> UploadResult
  async def download_file(self, source: str, destination: str, **kwargs) -> DownloadResult
  async def generate_signed_url(self, file_path: str, expiration: int) -> str
  async def delete_file(self, file_path: str) -> bool
  
  # ImageGenerationProvider methods
  async def generate_image(self, prompt: str, **kwargs) -> ImageResult
  async def generate_image_batch(self, prompts: List[str], **kwargs) -> List[ImageResult]
  ```

#### Business Logic Methods
- **Pattern**: `verb_noun` or `verb_domain_object`
- **Examples**:
  ```python
  async def analyze_video_content(self, video_url: str, user_id: str) -> VideoAnalysis
  async def generate_composition_code(self, blueprint: Blueprint) -> str
  async def validate_composition_structure(self, composition: dict) -> ValidationResult
  async def parse_user_prompt(self, prompt: str, context: dict) -> ParsedPrompt
  ```

#### Utility Functions
- **Pattern**: `verb_noun` or `get_noun` / `set_noun` / `is_condition` / `has_property`
- **Examples**:
  ```python
  def get_current_timestamp() -> str
  def parse_file_extension(filename: str) -> str
  def validate_jwt_token(token: str) -> bool
  def is_video_file(filename: str) -> bool
  def has_valid_format(data: dict) -> bool
  ```

### 1.5 Endpoint Naming

#### URL Structure
- **Pattern**: `/api/v{version}/{resource}/{action}` or `/api/v{version}/{resource}/{id}/{action}`
- **Rules**:
  - Use lowercase with hyphens for multi-word resources
  - Use plural nouns for collections
  - Use verbs only for actions that don't fit REST (e.g., analyze, generate)
  - Version all APIs

#### Examples:
```
# RESTful resource endpoints
POST   /api/v1/media                    # Upload media
GET    /api/v1/media/{id}               # Get specific media
GET    /api/v1/media                    # List media
DELETE /api/v1/media/{id}               # Delete media

# Action-based endpoints (non-CRUD)
POST   /api/v1/videos/analyze           # Analyze video content
POST   /api/v1/content/generate         # Generate content
POST   /api/v1/compositions/generate    # Generate composition
POST   /api/v1/stock-media/fetch        # Fetch stock media

# Agent/AI endpoints
POST   /api/v1/ai/agent                 # AI agent interaction
POST   /api/v1/ai/chat                  # AI chat
```

### 1.6 Variable Naming

#### General Rules
- **Pattern**: `snake_case`, descriptive, no abbreviations unless universally understood
- **Avoid**: Single letter variables (except in comprehensions/loops), ambiguous names

#### Examples:
```python
# Good
user_id: str
video_file_path: str
generated_composition: dict
analysis_result: VideoAnalysis
signed_url_expiration_seconds: int

# Avoid
uid: str
path: str
comp: dict
result: Any
exp: int
```

#### Constants
- **Pattern**: `SCREAMING_SNAKE_CASE`
- **Examples**:
  ```python
  MAX_FILE_SIZE_MB = 100
  DEFAULT_SIGNED_URL_EXPIRATION_DAYS = 7
  SUPPORTED_VIDEO_FORMATS = ['.mp4', '.mov', '.avi']
  GEMINI_MODEL_NAME = 'gemini-1.5-pro'
  ```

### 1.7 Test Naming

#### Test Files
- **Pattern**: `test_{module_name}.py`
- **Examples**:
  - `test_GeminiChatProvider.py`
  - `test_GCStorageProvider.py`
  - `test_VideoAnalysisService.py`
  - `test_upload_media_endpoint.py`

#### Test Classes
- **Pattern**: `Test{ClassName}` or `Test{Functionality}`
- **Examples**:
  ```python
  class TestGeminiChatProvider:
  class TestStorageProviderUpload:
  class TestVideoAnalysisService:
  ```

#### Test Methods
- **Pattern**: `test_{method_name}_{scenario}_{expected_outcome}`
- **Examples**:
  ```python
  def test_generate_chat_response_with_valid_input_returns_response():
  def test_upload_file_with_invalid_path_raises_error():
  def test_analyze_video_content_with_empty_video_returns_validation_error():
  def test_generate_composition_code_with_valid_blueprint_returns_code():
  ```

---

## 2. Current State Analysis

### 2.1 Existing Structure
```
backend/
├── main.py                    # Monolithic file with all endpoints (900+ lines)
├── analyzer.py                # Video analysis logic
├── blueprint_parser.py        # Blueprint parsing logic
├── code_generator.py          # Code generation logic
├── gcs_storage.py            # GCS operations
├── media_checker.py          # Media validation
├── prompts.py                # AI prompts
├── providers.py              # External API integrations
├── schema.py                 # Pydantic models
├── synth.py                  # Content synthesis
└── auth.py                   # JWT authentication
```

### 2.2 Pain Points
- **Monolithic main.py**: All endpoints in one file, hard to maintain
- **Mixed concerns**: Business logic mixed with API routing and external service calls
- **No abstraction**: Direct coupling to Google services (hard to swap providers)
- **Limited testing**: No clear test structure
- **No dependency injection**: Services instantiated inline
- **Configuration scattered**: Environment variables accessed directly throughout code

---

## 3. Target Architecture

### 3.1 Three-Tier Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        API Layer                             │
│  (FastAPI routes, request/response handling, validation)    │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   Business Logic Layer                       │
│  (Orchestration, domain logic, workflow coordination)       │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                     Services Layer                           │
│  (External integrations: Storage, LLM, Image/Video Gen)     │
│  - Base abstract classes (contracts)                         │
│  - Provider implementations (Google, OpenAI, etc.)          │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Key Principles
- **Separation of Concerns**: Each layer has a single responsibility
- **Dependency Injection**: Services injected via FastAPI Depends()
- **Interface Segregation**: Abstract base classes define contracts
- **Testability**: Each component can be tested in isolation
- **Provider Agnostic**: Easy to swap implementations

---

## 4. Directory Structure

```
backend_/
├── .env                              # Environment variables (copied from backend/)
├── screenwrite-gcs-credentials.json  # GCS credentials (copied from backend/)
├── pyproject.toml                    # Python project configuration
├── uv.lock                           # UV lock file
├── README.md                         # Backend documentation
│
├── main.py                           # FastAPI application entry point
│
├── core/                             # Core utilities and configuration
│   ├── __init__.py
│   ├── config.py                     # Configuration management (Pydantic BaseSettings)
│   ├── security.py                   # JWT authentication, authorization
│   ├── logger.py                     # Logging configuration
│   └── dependencies.py               # FastAPI dependency injection setup
│
├── api/                              # API Layer (routing)
│   ├── __init__.py
│   ├── v1/                           # API version 1
│   │   ├── __init__.py
│   │   ├── router.py                 # Main router aggregating all v1 routes
│   │   ├── media_endpoints.py        # Media upload/management endpoints
│   │   ├── video_endpoints.py        # Video analysis endpoints
│   │   ├── content_endpoints.py      # Content generation endpoints
│   │   ├── composition_endpoints.py  # Composition generation endpoints
│   │   ├── stock_media_endpoints.py  # Stock media fetch endpoints
│   │   └── ai_endpoints.py           # AI agent/chat endpoints
│
├── business_logic/                   # Business Logic Layer (orchestration)
│   ├── __init__.py
│   ├── VideoAnalysisService.py       # Orchestrates video analysis workflow
│   ├── ContentGenerationService.py   # Orchestrates content generation
│   ├── CompositionGenerationService.py  # Orchestrates composition creation
│   ├── StockMediaService.py          # Orchestrates stock media fetching
│   ├── BlueprintParserService.py     # Parses and validates blueprints
│   ├── CodeGeneratorService.py       # Generates composition code
│   └── AIAgentService.py             # Orchestrates AI agent interactions
│
├── services/                         # Services Layer (external integrations)
│   ├── __init__.py
│   │
│   ├── base/                         # Abstract base classes (contracts)
│   │   ├── __init__.py
│   │   ├── ChatProvider.py           # Abstract chat/LLM provider
│   │   ├── ImageGenerationProvider.py  # Abstract image generation provider
│   │   ├── VideoGenerationProvider.py  # Abstract video generation provider
│   │   ├── MediaProvider.py          # Abstract stock media provider
│   │   └── StorageProvider.py        # Abstract storage provider
│   │
│   ├── google/                       # Google service implementations
│   │   ├── __init__.py
│   │   ├── GeminiChatProvider.py     # Gemini implementation of ChatProvider
│   │   ├── ImagenGenerationProvider.py  # Imagen implementation
│   │   ├── VEOGenerationProvider.py  # Veo implementation
│   │   └── GCStorageProvider.py      # GCS implementation of StorageProvider
│   │
│   └── pexels/                       # Pexels service implementations
│       ├── __init__.py
│       └── PexelsMediaProvider.py    # Pexels implementation of MediaProvider
│
├── models/                           # Pydantic models (schemas)
│   ├── __init__.py
│   ├── requests/                     # Request models
│   │   ├── __init__.py
│   │   ├── MediaUploadRequest.py
│   │   ├── VideoAnalysisRequest.py
│   │   ├── ContentGenerationRequest.py
│   │   ├── CompositionGenerationRequest.py
│   │   ├── StockMediaRequest.py
│   │   └── AIAgentRequest.py
│   │
│   └── responses/                    # Response models
│       ├── __init__.py
│       ├── MediaUploadResponse.py
│       ├── VideoAnalysisResponse.py
│       ├── ContentGenerationResponse.py
│       ├── CompositionGenerationResponse.py
│       ├── StockMediaResponse.py
│       └── AIAgentResponse.py
│
├── prompts/                          # AI prompts and structured output schemas
│   ├── __init__.py
│   ├── schemas/                      # JSON schemas for structured LLM output
│   │   ├── __init__.py
│   │   ├── blueprint_schema.py       # Schema for blueprint generation
│   │   ├── video_analysis_schema.py  # Schema for video analysis output
│   │   └── agent_response_schema.py  # Schema for agent responses
│   ├── video_analysis_prompts.py
│   ├── content_generation_prompts.py
│   ├── composition_generation_prompts.py
│   └── agent_prompts.py
│
├── utils/                            # Utility functions
│   ├── __init__.py
│   ├── file_utils.py                 # File handling utilities
│   ├── validation_utils.py           # Validation helpers
│   └── time_utils.py                 # Time/timestamp utilities
│
└── tests/                            # Test suite
    ├── __init__.py
    ├── conftest.py                   # Pytest fixtures and configuration
    │
    ├── unit/                         # Unit tests (isolated components)
    │   ├── __init__.py
    │   ├── services/
    │   │   ├── test_GeminiChatProvider.py
    │   │   ├── test_GCStorageProvider.py
    │   │   ├── test_ImagenGenerationProvider.py
    │   │   ├── test_VEOGenerationProvider.py
    │   │   └── test_PexelsMediaProvider.py
    │   │
    │   └── business_logic/
    │       ├── test_VideoAnalysisService.py
    │       ├── test_ContentGenerationService.py
    │       ├── test_CompositionGenerationService.py
    │       └── test_AIAgentService.py
    │
    └── integration/                  # Integration tests (API endpoints)
        ├── __init__.py
        ├── test_media_endpoints.py
        ├── test_video_endpoints.py
        ├── test_content_endpoints.py
        ├── test_composition_endpoints.py
        ├── test_stock_media_endpoints.py
        └── test_ai_endpoints.py
```

---

## 5. Service Provider Contracts

### 5.1 ChatProvider (Base Class)

```python
# services/base/ChatProvider.py

from abc import ABC, abstractmethod
from typing import List, Dict, Any, AsyncIterator, Optional
from dataclasses import dataclass

@dataclass
class ChatMessage:
    role: str  # 'user', 'assistant', 'system'
    content: str
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class ChatResponse:
    content: str
    model: str
    usage: Optional[Dict[str, int]] = None
    metadata: Optional[Dict[str, Any]] = None

class ChatProvider(ABC):
    """Abstract base class for chat/LLM providers."""
    
    @abstractmethod
    async def generate_chat_response(
        self,
        messages: List[ChatMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> ChatResponse:
        """Generate a single chat response."""
        pass
    
    @abstractmethod
    async def stream_chat_response(
        self,
        messages: List[ChatMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """Stream chat response chunks."""
        pass
    
    @abstractmethod
    async def generate_chat_response_with_schema(
        self,
        messages: List[ChatMessage],
        response_schema: Dict[str, Any],
        temperature: float = 0.7,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate structured response matching a JSON schema."""
        pass
```

### 5.2 StorageProvider (Base Class)

```python
# services/base/StorageProvider.py

from abc import ABC, abstractmethod
from typing import Optional, BinaryIO
from dataclasses import dataclass
from datetime import datetime

@dataclass
class UploadResult:
    file_path: str
    url: str
    size_bytes: int
    content_type: str
    uploaded_at: datetime

@dataclass
class DownloadResult:
    content: bytes
    content_type: str
    size_bytes: int

class StorageProvider(ABC):
    """Abstract base class for cloud storage providers."""
    
    @abstractmethod
    async def upload_file(
        self,
        file_content: BinaryIO,
        destination_path: str,
        content_type: str,
        metadata: Optional[dict] = None,
        **kwargs
    ) -> UploadResult:
        """Upload a file to cloud storage."""
        pass
    
    @abstractmethod
    async def upload_file_from_url(
        self,
        source_url: str,
        destination_path: str,
        content_type: str,
        **kwargs
    ) -> UploadResult:
        """Upload a file from URL to cloud storage."""
        pass
    
    @abstractmethod
    async def download_file(
        self,
        file_path: str,
        **kwargs
    ) -> DownloadResult:
        """Download a file from cloud storage."""
        pass
    
    @abstractmethod
    async def generate_signed_url(
        self,
        file_path: str,
        expiration_seconds: int = 604800,  # 7 days default
        **kwargs
    ) -> str:
        """Generate a signed URL for secure file access."""
        pass
    
    @abstractmethod
    async def delete_file(
        self,
        file_path: str,
        **kwargs
    ) -> bool:
        """Delete a file from cloud storage."""
        pass
    
    @abstractmethod
    async def file_exists(
        self,
        file_path: str,
        **kwargs
    ) -> bool:
        """Check if a file exists in cloud storage."""
        pass
```

### 5.3 ImageGenerationProvider (Base Class)

```python
# services/base/ImageGenerationProvider.py

from abc import ABC, abstractmethod
from typing import Optional, List
from dataclasses import dataclass
from enum import Enum

class ImageSize(Enum):
    SMALL = "256x256"
    MEDIUM = "512x512"
    LARGE = "1024x1024"
    XLARGE = "1536x1536"

@dataclass
class ImageGenerationResult:
    image_url: str
    revised_prompt: Optional[str] = None
    size: str = "1024x1024"
    format: str = "png"
    metadata: Optional[dict] = None

class ImageGenerationProvider(ABC):
    """Abstract base class for image generation providers."""
    
    @abstractmethod
    async def generate_image(
        self,
        prompt: str,
        size: ImageSize = ImageSize.LARGE,
        quality: str = "standard",
        **kwargs
    ) -> ImageGenerationResult:
        """Generate a single image from prompt."""
        pass
    
    @abstractmethod
    async def generate_image_batch(
        self,
        prompts: List[str],
        size: ImageSize = ImageSize.LARGE,
        quality: str = "standard",
        **kwargs
    ) -> List[ImageGenerationResult]:
        """Generate multiple images from prompts."""
        pass
```

### 5.4 VideoGenerationProvider (Base Class)

```python
# services/base/VideoGenerationProvider.py

from abc import ABC, abstractmethod
from typing import Optional
from dataclasses import dataclass

@dataclass
class VideoGenerationResult:
    video_url: str
    duration_seconds: float
    width: int
    height: int
    format: str = "mp4"
    metadata: Optional[dict] = None

class VideoGenerationProvider(ABC):
    """Abstract base class for video generation providers."""
    
    @abstractmethod
    async def generate_video(
        self,
        prompt: str,
        duration_seconds: int = 5,
        width: int = 1920,
        height: int = 1080,
        **kwargs
    ) -> VideoGenerationResult:
        """Generate a video from prompt."""
        pass
    
    @abstractmethod
    async def check_generation_status(
        self,
        job_id: str,
        **kwargs
    ) -> dict:
        """Check the status of a video generation job."""
        pass
```

### 5.5 MediaProvider (Base Class)

```python
# services/base/MediaProvider.py

from abc import ABC, abstractmethod
from typing import List, Optional
from dataclasses import dataclass
from enum import Enum

class MediaType(Enum):
    VIDEO = "video"
    IMAGE = "image"

class Orientation(Enum):
    LANDSCAPE = "landscape"
    PORTRAIT = "portrait"
    SQUARE = "square"

@dataclass
class MediaAsset:
    id: str
    type: MediaType
    url: str
    thumbnail_url: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    duration_seconds: Optional[float] = None
    source: str = ""
    metadata: Optional[dict] = None

@dataclass
class MediaSearchResult:
    assets: List[MediaAsset]
    total_results: int
    page: int
    per_page: int

class MediaProvider(ABC):
    """Abstract base class for stock media providers."""
    
    @abstractmethod
    async def search_videos(
        self,
        query: str,
        page: int = 1,
        per_page: int = 15,
        orientation: Optional[Orientation] = None,
        **kwargs
    ) -> MediaSearchResult:
        """Search for stock videos."""
        pass
    
    @abstractmethod
    async def search_images(
        self,
        query: str,
        page: int = 1,
        per_page: int = 15,
        orientation: Optional[Orientation] = None,
        **kwargs
    ) -> MediaSearchResult:
        """Search for stock images."""
        pass
    
    @abstractmethod
    async def get_asset_details(
        self,
        asset_id: str,
        asset_type: MediaType,
        **kwargs
    ) -> MediaAsset:
        """Get detailed information about a specific asset."""
        pass
```

---

## 6. Implementation Plan

### Phase 1: Service Layer Foundation

#### Step 1.1: Create Base Directory Structure
```bash
mkdir -p backend_/core
mkdir -p backend_/api/v1
mkdir -p backend_/business_logic
mkdir -p backend_/services/base
mkdir -p backend_/services/google
mkdir -p backend_/services/pexels
mkdir -p backend_/models/requests
mkdir -p backend_/models/responses
mkdir -p backend_/prompts
mkdir -p backend_/utils
mkdir -p backend_/tests/unit/services
mkdir -p backend_/tests/unit/business_logic
mkdir -p backend_/tests/integration
```

#### Step 1.2: Copy Configuration Files
```bash
cp backend/.env backend_/.env
cp backend/screenwrite-gcs-credentials.json backend_/screenwrite-gcs-credentials.json
cp backend/pyproject.toml backend_/pyproject.toml
cp backend/uv.lock backend_/uv.lock
```

#### Step 1.3: Create Base Classes (Abstract Providers)
**Order of implementation:**
1. `services/base/ChatProvider.py`
2. `services/base/StorageProvider.py`
3. `services/base/ImageGenerationProvider.py`
4. `services/base/VideoGenerationProvider.py`
5. `services/base/MediaProvider.py`

**Testing approach:** No unit tests for abstract classes (they define contracts only)

#### Step 1.4: Implement Google Providers
**Order of implementation:**

1. **GCStorageProvider** (foundational, needed by others)
   - File: `services/google/GCStorageProvider.py`
   - Functionality: Upload, download, signed URLs, delete
   - Test: `tests/unit/services/test_GCStorageProvider.py`
   - Test scenarios:
     - `test_upload_file_with_valid_content_returns_upload_result`
     - `test_upload_file_from_url_with_valid_url_returns_upload_result`
     - `test_generate_signed_url_with_valid_path_returns_url`
     - `test_delete_file_with_existing_file_returns_true`
     - `test_file_exists_with_existing_file_returns_true`
     - `test_upload_file_with_invalid_content_raises_error`

2. **GeminiChatProvider** (most used, critical path)
   - File: `services/google/GeminiChatProvider.py`
   - Functionality: Chat, streaming, structured output
   - Test: `tests/unit/services/test_GeminiChatProvider.py`
   - Test scenarios:
     - `test_generate_chat_response_with_valid_messages_returns_response`
     - `test_stream_chat_response_with_valid_messages_yields_chunks`
     - `test_generate_chat_response_with_schema_returns_structured_data`
     - `test_generate_chat_response_with_invalid_messages_raises_error`
     - `test_generate_chat_response_with_temperature_applies_correctly`

3. **ImagenGenerationProvider**
   - File: `services/google/ImagenGenerationProvider.py`
   - Functionality: Image generation, batch generation
   - Test: `tests/unit/services/test_ImagenGenerationProvider.py`
   - Test scenarios:
     - `test_generate_image_with_valid_prompt_returns_image_result`
     - `test_generate_image_batch_with_valid_prompts_returns_results`
     - `test_generate_image_with_different_sizes_returns_correct_size`
     - `test_generate_image_with_invalid_prompt_raises_error`

4. **VEOGenerationProvider**
   - File: `services/google/VEOGenerationProvider.py`
   - Functionality: Video generation, status checking
   - Test: `tests/unit/services/test_VEOGenerationProvider.py`
   - Test scenarios:
     - `test_generate_video_with_valid_prompt_returns_video_result`
     - `test_check_generation_status_with_valid_job_returns_status`
     - `test_generate_video_with_duration_parameter_respects_duration`
     - `test_generate_video_with_invalid_prompt_raises_error`

#### Step 1.5: Implement Pexels Provider

5. **PexelsMediaProvider**
   - File: `services/pexels/PexelsMediaProvider.py`
   - Functionality: Video search, image search, asset details
   - Test: `tests/unit/services/test_PexelsMediaProvider.py`
   - Test scenarios:
     - `test_search_videos_with_valid_query_returns_results`
     - `test_search_images_with_valid_query_returns_results`
     - `test_get_asset_details_with_valid_id_returns_asset`
     - `test_search_videos_with_orientation_filter_applies_correctly`
     - `test_search_videos_with_pagination_returns_correct_page`

#### Step 1.6: Phase 1 Validation Checklist
- [ ] All base classes created and documented
- [ ] All Google providers implemented
- [ ] Pexels provider implemented
- [ ] All unit tests passing (100% coverage target)
- [ ] All providers follow naming conventions
- [ ] Code reviewed and documented
- [ ] Integration between GCS and other providers tested

---

### Phase 2: Business Logic Layer

#### Step 2.1: Core Configuration Setup

1. **Create core/config.py**
   - Load environment variables using Pydantic BaseSettings
   - Configuration classes:
     - `GoogleCloudConfig` - GCS bucket, credentials path
     - `GeminiConfig` - API key, model names
     - `PexelsConfig` - API key
     - `AuthConfig` - Supabase URL, JWT secret
     - `AppConfig` - Main config aggregating all above

2. **Create core/security.py**
   - JWT token validation
   - User authentication from JWT
   - Dependency functions for FastAPI

3. **Create core/dependencies.py**
   - Provider factory functions
   - Dependency injection setup for FastAPI
   - Singleton instances of providers

#### Step 2.2: Implement Business Logic Services

**Order of implementation:**

1. **VideoAnalysisService**
   - File: `business_logic/VideoAnalysisService.py`
   - Dependencies: `GeminiChatProvider`, `GCStorageProvider`
   - Functionality: Orchestrate video analysis with Gemini
   - Test: `tests/unit/business_logic/test_VideoAnalysisService.py`
   - Test scenarios:
     - `test_analyze_video_content_with_valid_url_returns_analysis`
     - `test_analyze_video_content_with_invalid_url_raises_error`
     - `test_analyze_video_content_with_storage_failure_handles_gracefully`

2. **BlueprintParserService**
   - File: `business_logic/BlueprintParserService.py`
   - Dependencies: None (pure logic)
   - Functionality: Parse and validate blueprint structures
   - Test: `tests/unit/business_logic/test_BlueprintParserService.py`
   - Test scenarios:
     - `test_parse_blueprint_with_valid_structure_returns_parsed_data`
     - `test_validate_blueprint_with_invalid_structure_raises_error`
     - `test_parse_blueprint_with_missing_fields_handles_defaults`

3. **CodeGeneratorService**
   - File: `business_logic/CodeGeneratorService.py`
   - Dependencies: `GeminiChatProvider`
   - Functionality: Generate composition code from blueprints
   - Test: `tests/unit/business_logic/test_CodeGeneratorService.py`
   - Test scenarios:
     - `test_generate_composition_code_with_valid_blueprint_returns_code`
     - `test_generate_composition_code_with_invalid_blueprint_raises_error`
     - `test_generate_composition_code_validates_output_syntax`

4. **ContentGenerationService**
   - File: `business_logic/ContentGenerationService.py`
   - Dependencies: `GeminiChatProvider`, `ImagenGenerationProvider`, `VEOGenerationProvider`, `GCStorageProvider`
   - Functionality: Orchestrate content generation (text, images, videos)
   - Test: `tests/unit/business_logic/test_ContentGenerationService.py`
   - Test scenarios:
     - `test_generate_content_with_text_prompt_returns_text_content`
     - `test_generate_content_with_image_request_returns_image_url`
     - `test_generate_content_with_video_request_returns_video_url`
     - `test_generate_content_uploads_to_gcs_successfully`

5. **StockMediaService**
   - File: `business_logic/StockMediaService.py`
   - Dependencies: `PexelsMediaProvider`, `GCStorageProvider`
   - Functionality: Search and fetch stock media, upload to GCS
   - Test: `tests/unit/business_logic/test_StockMediaService.py`
   - Test scenarios:
     - `test_fetch_stock_video_with_query_returns_videos`
     - `test_fetch_stock_video_uploads_to_gcs_successfully`
     - `test_fetch_stock_image_with_query_returns_images`
     - `test_fetch_stock_media_with_failed_upload_handles_error`

6. **CompositionGenerationService**
   - File: `business_logic/CompositionGenerationService.py`
   - Dependencies: `GeminiChatProvider`, `BlueprintParserService`, `CodeGeneratorService`
   - Functionality: Orchestrate full composition generation workflow
   - Test: `tests/unit/business_logic/test_CompositionGenerationService.py`
   - Test scenarios:
     - `test_generate_composition_with_prompt_returns_composition`
     - `test_generate_composition_validates_blueprint_structure`
     - `test_generate_composition_generates_valid_code`
     - `test_generate_composition_with_invalid_prompt_raises_error`

7. **AIAgentService**
   - File: `business_logic/AIAgentService.py`
   - Dependencies: `GeminiChatProvider`, `ContentGenerationService`, `StockMediaService`
   - Functionality: Orchestrate conversational AI agent interactions
   - Test: `tests/unit/business_logic/test_AIAgentService.py`
   - Test scenarios:
     - `test_process_agent_message_with_chat_intent_returns_response`
     - `test_process_agent_message_with_generate_intent_calls_content_service`
     - `test_process_agent_message_with_search_intent_calls_stock_service`
     - `test_process_agent_message_maintains_conversation_context`

#### Step 2.3: Phase 2 Validation Checklist
- [ ] Core configuration setup complete
- [ ] All business logic services implemented
- [ ] All unit tests passing
- [ ] Services properly use dependency injection
- [ ] Error handling implemented consistently
- [ ] Logging added to all services
- [ ] Code reviewed and documented

---

### Phase 3: API Layer (Endpoints)

#### Step 3.1: Create Pydantic Models

**Request Models** (`models/requests/`)
1. `MediaUploadRequest.py`
2. `VideoAnalysisRequest.py`
3. `ContentGenerationRequest.py`
4. `CompositionGenerationRequest.py`
5. `StockMediaRequest.py`
6. `AIAgentRequest.py`

**Response Models** (`models/responses/`)
1. `MediaUploadResponse.py`
2. `VideoAnalysisResponse.py`
3. `ContentGenerationResponse.py`
4. `CompositionGenerationResponse.py`
5. `StockMediaResponse.py`
6. `AIAgentResponse.py`

#### Step 3.2: Implement API Endpoints

**Order of implementation:**

1. **Media Endpoints** (`api/v1/media_endpoints.py`)
   - Endpoints:
     - `POST /api/v1/media` - Upload media file
     - `GET /api/v1/media/{id}` - Get media details
     - `DELETE /api/v1/media/{id}` - Delete media
   - Dependencies: `GCStorageProvider`
   - Test: `tests/integration/test_media_endpoints.py`
   - Test scenarios:
     - `test_upload_media_with_valid_file_returns_200_and_url`
     - `test_upload_media_without_auth_returns_401`
     - `test_get_media_with_valid_id_returns_200_and_details`
     - `test_delete_media_with_valid_id_returns_200`

2. **Video Endpoints** (`api/v1/video_endpoints.py`)
   - Endpoints:
     - `POST /api/v1/videos/analyze` - Analyze video content
   - Dependencies: `VideoAnalysisService`
   - Test: `tests/integration/test_video_endpoints.py`
   - Test scenarios:
     - `test_analyze_video_with_valid_url_returns_200_and_analysis`
     - `test_analyze_video_without_auth_returns_401`
     - `test_analyze_video_with_invalid_url_returns_400`

3. **Content Endpoints** (`api/v1/content_endpoints.py`)
   - Endpoints:
     - `POST /api/v1/content/generate` - Generate content
   - Dependencies: `ContentGenerationService`
   - Test: `tests/integration/test_content_endpoints.py`
   - Test scenarios:
     - `test_generate_content_with_text_prompt_returns_200_and_content`
     - `test_generate_content_with_image_request_returns_200_and_url`
     - `test_generate_content_without_auth_returns_401`

4. **Stock Media Endpoints** (`api/v1/stock_media_endpoints.py`)
   - Endpoints:
     - `POST /api/v1/stock-media/fetch` - Fetch stock media
   - Dependencies: `StockMediaService`
   - Test: `tests/integration/test_stock_media_endpoints.py`
   - Test scenarios:
     - `test_fetch_stock_video_with_query_returns_200_and_videos`
     - `test_fetch_stock_video_uploads_to_gcs_returns_url`
     - `test_fetch_stock_media_without_auth_returns_401`

5. **Composition Endpoints** (`api/v1/composition_endpoints.py`)
   - Endpoints:
     - `POST /api/v1/compositions/generate` - Generate composition
   - Dependencies: `CompositionGenerationService`
   - Test: `tests/integration/test_composition_endpoints.py`
   - Test scenarios:
     - `test_generate_composition_with_prompt_returns_200_and_composition`
     - `test_generate_composition_validates_input_returns_400_on_invalid`
     - `test_generate_composition_without_auth_returns_401`

6. **AI Endpoints** (`api/v1/ai_endpoints.py`)
   - Endpoints:
     - `POST /api/v1/ai/agent` - AI agent interaction
     - `POST /api/v1/ai/chat` - Direct chat (legacy support)
   - Dependencies: `AIAgentService`
   - Test: `tests/integration/test_ai_endpoints.py`
   - Test scenarios:
     - `test_ai_agent_with_chat_message_returns_200_and_response`
     - `test_ai_agent_maintains_conversation_context`
     - `test_ai_agent_without_auth_returns_401`

#### Step 3.3: Create Main Router

**File:** `api/v1/router.py`
- Aggregate all endpoint routers
- Include in main FastAPI app

**File:** `main.py`
- FastAPI application setup
- CORS configuration
- Include v1 router
- Error handlers
- Startup/shutdown events

#### Step 3.4: Phase 3 Validation Checklist
- [ ] All Pydantic models created
- [ ] All endpoints implemented
- [ ] All integration tests passing
- [ ] JWT authentication working on all protected endpoints
- [ ] Error handling consistent across all endpoints
- [ ] API documentation (OpenAPI) generated correctly
- [ ] CORS configured properly
- [ ] Response models validated

---

## 7. Testing Strategy

### 7.1 Unit Testing

**Framework:** pytest + pytest-asyncio + pytest-mock

**Coverage Target:** 90%+ for services and business logic

**Mock Strategy:**
- Mock external API calls (Gemini, Imagen, Veo, Pexels, GCS)
- Use dependency injection to inject mocks
- Create fixtures for common test data

**Example Test Structure:**
```python
# tests/unit/services/test_GeminiChatProvider.py

import pytest
from unittest.mock import AsyncMock, MagicMock
from services.google.GeminiChatProvider import GeminiChatProvider
from services.base.ChatProvider import ChatMessage, ChatResponse

@pytest.fixture
def mock_gemini_client():
    """Mock Google Gemini client."""
    mock = MagicMock()
    # Setup mock responses
    return mock

@pytest.fixture
def gemini_provider(mock_gemini_client):
    """Create GeminiChatProvider with mocked client."""
    provider = GeminiChatProvider(api_key="test-key")
    provider.client = mock_gemini_client
    return provider

@pytest.mark.asyncio
async def test_generate_chat_response_with_valid_messages_returns_response(gemini_provider, mock_gemini_client):
    # Arrange
    messages = [ChatMessage(role="user", content="Hello")]
    mock_gemini_client.generate_content.return_value = MagicMock(text="Hi there!")
    
    # Act
    response = await gemini_provider.generate_chat_response(messages)
    
    # Assert
    assert isinstance(response, ChatResponse)
    assert response.content == "Hi there!"
    assert mock_gemini_client.generate_content.called
```

### 7.2 Integration Testing

**Framework:** pytest + httpx (for async testing)

**Strategy:**
- Test full request/response cycle
- Use TestClient from FastAPI
- Mock external APIs but use real services/business logic
- Test authentication flow

**Example Test Structure:**
```python
# tests/integration/test_media_endpoints.py

import pytest
from httpx import AsyncClient
from main import app

@pytest.fixture
def auth_headers():
    """Mock authentication headers."""
    return {"Authorization": "Bearer test-token"}

@pytest.mark.asyncio
async def test_upload_media_with_valid_file_returns_200_and_url(auth_headers):
    # Arrange
    async with AsyncClient(app=app, base_url="http://test") as client:
        files = {"file": ("test.mp4", b"fake video content", "video/mp4")}
        
        # Act
        response = await client.post(
            "/api/v1/media",
            files=files,
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "url" in data
        assert "id" in data
```

### 7.3 Test Configuration

**File:** `tests/conftest.py`
```python
import pytest
from fastapi.testclient import TestClient
from main import app

@pytest.fixture
def test_client():
    """Create test client for FastAPI app."""
    return TestClient(app)

@pytest.fixture
def mock_auth():
    """Mock authentication for testing."""
    # Override get_current_user dependency
    pass

@pytest.fixture
def sample_video_analysis_response():
    """Sample video analysis response for testing."""
    return {
        "summary": "Test video summary",
        "key_points": ["Point 1", "Point 2"],
        "duration": 120.0
    }

# Add more common fixtures
```

---

## 8. Migration Execution Plan

### Phase 1: Service Layer (Week 1-2)

**Day 1-2:**
- [ ] Create directory structure
- [ ] Copy configuration files
- [ ] Create all base classes (abstract providers)
- [ ] Review and validate base class contracts

**Day 3-5:**
- [ ] Implement `GCStorageProvider`
- [ ] Write unit tests for `GCStorageProvider`
- [ ] Implement `GeminiChatProvider`
- [ ] Write unit tests for `GeminiChatProvider`

**Day 6-8:**
- [ ] Implement `ImagenGenerationProvider`
- [ ] Write unit tests for `ImagenGenerationProvider`
- [ ] Implement `VEOGenerationProvider`
- [ ] Write unit tests for `VEOGenerationProvider`

**Day 9-10:**
- [ ] Implement `PexelsMediaProvider`
- [ ] Write unit tests for `PexelsMediaProvider`
- [ ] Phase 1 validation and review

### Phase 2: Business Logic Layer (Week 3)

**Day 11-12:**
- [ ] Create core configuration (`config.py`, `security.py`, `dependencies.py`)
- [ ] Implement `VideoAnalysisService`
- [ ] Write unit tests for `VideoAnalysisService`

**Day 13-14:**
- [ ] Implement `BlueprintParserService` and `CodeGeneratorService`
- [ ] Write unit tests for both services

**Day 15-16:**
- [ ] Implement `ContentGenerationService` and `StockMediaService`
- [ ] Write unit tests for both services

**Day 17:**
- [ ] Implement `CompositionGenerationService` and `AIAgentService`
- [ ] Write unit tests for both services
- [ ] Phase 2 validation and review

### Phase 3: API Layer (Week 4)

**Day 18-19:**
- [ ] Create all Pydantic request/response models
- [ ] Implement media endpoints
- [ ] Write integration tests for media endpoints

**Day 20-21:**
- [ ] Implement video and content endpoints
- [ ] Write integration tests

**Day 22-23:**
- [ ] Implement stock media and composition endpoints
- [ ] Write integration tests

**Day 24:**
- [ ] Implement AI endpoints
- [ ] Write integration tests
- [ ] Create main router and application setup

### Phase 4: Integration & Testing (Week 5)

**Day 25-26:**
- [ ] End-to-end testing of all endpoints
- [ ] Performance testing
- [ ] Load testing (basic)

**Day 27:**
- [ ] Security audit
- [ ] Code review
- [ ] Documentation review

**Day 28:**
- [ ] Final validation
- [ ] Deployment preparation
- [ ] Rollback plan testing

**Day 29-30:**
- [ ] Deploy new backend
- [ ] Monitor for issues
- [ ] Gradual traffic migration

---

## 9. Rollback Strategy

### 9.1 Pre-Deployment Checklist
- [ ] All tests passing (unit + integration)
- [ ] Code coverage > 90%
- [ ] Performance benchmarks met
- [ ] Security audit completed
- [ ] Documentation updated
- [ ] Old backend still functional

### 9.2 Deployment Plan
1. Deploy new backend to staging environment
2. Run smoke tests in staging
3. Deploy to production (keep old backend running)
4. Route 10% traffic to new backend
5. Monitor metrics (errors, latency, success rate)
6. Gradually increase traffic (25%, 50%, 75%, 100%)
7. Monitor for 24 hours at 100%
8. Decommission old backend

### 9.3 Rollback Triggers
- Error rate > 1%
- Average latency > 2x old backend
- Any authentication failures
- Data corruption or loss
- Critical bug discovered

### 9.4 Rollback Procedure
1. Route 100% traffic back to old backend
2. Investigate issues in new backend
3. Fix issues in separate branch
4. Re-test thoroughly
5. Attempt deployment again

---

## 10. Success Metrics

### 10.1 Code Quality Metrics
- [ ] Test coverage > 90%
- [ ] Zero critical security vulnerabilities
- [ ] All linting rules passing
- [ ] Type hints on all functions
- [ ] Docstrings on all public methods

### 10.2 Performance Metrics
- [ ] API response time < 500ms (p95)
- [ ] File upload speed equivalent to old backend
- [ ] Video analysis time < 30 seconds
- [ ] Composition generation time < 15 seconds

### 10.3 Maintainability Metrics
- [ ] All endpoints documented in OpenAPI
- [ ] README with setup instructions
- [ ] Architecture diagram created
- [ ] Contributing guidelines updated
- [ ] Clear error messages for all failures

---

## 11. Next Steps

1. **Review this document** - Ensure all naming conventions and architecture decisions are correct
2. **Get approval** - Confirm this is the desired approach
3. **Create directory structure** - Set up the foundation
4. **Start Phase 1** - Begin implementing service layer

Ready to proceed when you give the green light!
