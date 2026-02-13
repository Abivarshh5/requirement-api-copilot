"""
LLM integration service with multi-step prompt pipeline and retry logic.
Supports OpenAI GPT-4o with automatic fallback to mock mode.
"""

import json
import os
import time
import logging
import random
from typing import Any, Dict, Tuple

import google.generativeai as genai
from models import (
    SpecOutput, Module, Feature, UserStory, ApiEndpoint, DbTable,
    OpenQuestion, Contradiction, Metadata
)

logger = logging.getLogger(__name__)

# ── Prompt Templates ─────────────────────────────────────────────────

STEP1_FEATURE_EXTRACTION = """You are an expert product analyst and software architect. Analyze the following raw product requirements and extract a structured breakdown.

**Requirements:**
{requirements_text}

**Your task:**
1. Identify high-level **modules** (functional areas like "User Management", "Payment Processing", etc.)
2. For each module, list specific **features** (concrete capabilities)
3. Assign priority (high/medium/low) based on explicit or implicit indicators in the requirements
4. Assign complexity (simple/moderate/complex) to each feature

**Rules:**
- Be precise — only extract what is stated or strongly implied
- Use "TBD" in descriptions when information is missing or unclear
- Do NOT invent features not mentioned or implied in the requirements
- Group related features under the most appropriate module
- Each module needs a unique module_id like "mod_001", "mod_002", etc.
- Each feature needs a unique feature_id like "feat_001", "feat_002", etc.

**Return ONLY valid JSON matching this exact schema (no markdown, no explanation):**
{{
  "modules": [
    {{
      "module_id": "mod_001",
      "name": "string",
      "description": "string",
      "priority": "high | medium | low"
    }}
  ],
  "features_by_module": {{
    "mod_001": [
      {{
        "feature_id": "feat_001",
        "name": "string",
        "description": "string",
        "priority": "high | medium | low",
        "complexity": "simple | moderate | complex"
      }}
    ]
  }}
}}"""

STEP2_USER_STORIES = """You are an expert agile product owner. Convert the following modules and features into well-formed user stories.

**Modules and Features:**
{features_json}

**Your task:**
Create user stories in standard format for every feature provided.

**Rules:**
- Every story MUST follow: "As a [specific role], I want [concrete action], so that [clear benefit]"
- Include 2-4 testable acceptance criteria per story
- Stories must be specific and testable — avoid vague language
- Do NOT add technical implementation details in the "I want" clause
- Link every story to its parent feature_id and module_id
- Each story needs a unique story_id like "us_001", "us_002", etc.
- Priority should match or derive from the parent feature's priority

**Return ONLY valid JSON matching this schema (no markdown, no explanation):**
{{
  "user_stories": [
    {{
      "story_id": "us_001",
      "module_id": "mod_001",
      "feature_id": "feat_001",
      "as_a": "string (specific user role)",
      "i_want": "string (concrete action)",
      "so_that": "string (clear benefit)",
      "acceptance_criteria": ["string", "string"],
      "priority": "high | medium | low"
    }}
  ]
}}"""

STEP3_API_DB_DESIGN = """You are a senior backend architect. Design RESTful API endpoints and a normalized database schema based on the following specification.

**Modules & Features:**
{features_json}

**User Stories:**
{stories_json}

**Rules for API endpoints:**
- Use RESTful conventions (proper HTTP methods, resource-based URLs)
- Include all necessary CRUD operations
- Specify authentication requirements (required/optional/none)
- Define request schemas (headers, query_params, body) with realistic example values
- Define response schemas (success with status_code + body, and common errors: 400, 401, 404, 500)
- Link endpoints to related story IDs
- Each endpoint needs a unique endpoint_id like "ep_001", "ep_002", etc.
- Use plural resource names in paths (e.g., /api/users, /api/orders)

**Rules for database schema:**
- Normalize to 3NF unless denormalization is justified
- Include proper indexes for query performance
- Define all foreign key relationships
- Use appropriate SQL data types (VARCHAR, INTEGER, TIMESTAMP, BOOLEAN, TEXT, UUID, etc.)
- Include created_at/updated_at timestamps on all tables
- Consider soft deletes where appropriate
- Each table should have a clear primary key

**Also generate:**
- open_questions: Things that are unclear or ambiguous in the requirements (with category, context, priority)
- contradictions: Any conflicting requirements detected (with suggested resolutions)

**Return ONLY valid JSON matching this schema (no markdown, no explanation):**
{{
  "api_endpoints": [
    {{
      "endpoint_id": "ep_001",
      "method": "GET | POST | PUT | PATCH | DELETE",
      "path": "/api/resource",
      "description": "string",
      "authentication": "required | optional | none",
      "authorization": "string or null",
      "request": {{
        "headers": {{"Authorization": "Bearer <token>"}},
        "query_params": {{"page": "integer", "limit": "integer"}},
        "body": {{}}
      }},
      "response": {{
        "success": {{
          "status_code": 200,
          "body": {{}}
        }},
        "errors": [
          {{
            "status_code": 400,
            "description": "Bad request",
            "body": {{"error": "string"}}
          }}
        ]
      }},
      "related_stories": ["us_001"]
    }}
  ],
  "db_schema": [
    {{
      "table_name": "string",
      "description": "string",
      "columns": [
        {{
          "name": "id",
          "type": "UUID",
          "nullable": false,
          "primary_key": true,
          "foreign_key": null,
          "default": "gen_random_uuid()",
          "constraints": []
        }}
      ],
      "indexes": [
        {{
          "name": "idx_table_column",
          "columns": ["column"],
          "unique": false
        }}
      ],
      "relationships": [
        {{
          "type": "one-to-many | many-to-one | many-to-many",
          "target_table": "string",
          "description": "string"
        }}
      ]
    }}
  ],
  "open_questions": [
    {{
      "question_id": "oq_001",
      "category": "authentication | business_logic | data_model | integration | other",
      "question": "string",
      "context": "string",
      "priority": "high | medium | low"
    }}
  ],
  "contradictions": [
    {{
      "description": "string",
      "conflicting_items": ["string"],
      "suggested_resolution": "string"
    }}
  ]
}}"""

REFINE_PROMPT = """You are a senior software architect. You have an existing technical specification and the user wants to refine it.

**Existing Specification:**
{existing_spec_json}

**User's Refinement Instructions:**
{refinement_instructions}

**Your task:**
1. Apply the refinement instructions to the existing specification
2. Preserve all existing IDs (module_id, feature_id, story_id, endpoint_id, etc.) unless explicitly told to remove something
3. Add new items with new IDs that follow the existing naming pattern
4. Update affected sections — if adding auth, update endpoints AND add relevant DB tables
5. Generate new open_questions if the refinement introduces ambiguities
6. Flag any new contradictions

**Return the COMPLETE updated specification as valid JSON with ALL sections:**
- modules, features_by_module, user_stories, api_endpoints, db_schema, open_questions, contradictions

**Return ONLY valid JSON, no markdown, no explanation.**"""


class LLMService:
    """Multi-step LLM pipeline for spec generation with retry logic."""

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY", "")
        self.model_name = os.getenv("LLM_MODEL", "gemini-2.5-flash-preview-09-2025")
        self.max_retries = int(os.getenv("MAX_RETRIES", "3"))
        self.mock_mode = os.getenv("MOCK_MODE", "false").lower() == "true"

        if not self.mock_mode and self.api_key:
            genai.configure(api_key=self.api_key)
            # Use a slightly more conservative config for better stability
            self.model = genai.GenerativeModel(
                model_name=self.model_name
            )
            self.generation_config = {
                "temperature": 0.1,  # Lower temperature for more consistent JSON
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 8192,
                "response_mime_type": "application/json",
            }
        else:
            self.model = None
            if not self.api_key:
                logger.warning("No GEMINI_API_KEY set — running in mock mode")
                self.mock_mode = True

    def _call_llm(self, prompt: str) -> str:
        """Call the Gemini API with the given prompt."""
        if self.mock_mode:
            raise RuntimeError("Mock mode active — should not reach _call_llm")

        try:
            response = self.model.generate_content(
                contents=[
                    {"role": "user", "parts": [prompt]}
                ],
                generation_config=self.generation_config
            )
            # Check if response is empty or blocked
            if not response or not response.candidates:
                raise ValueError("AI returned an empty response or was blocked by filters.")
            
            content = response.text.strip()
        except Exception as e:
            err_msg = str(e)
            if "429" in err_msg or "quota" in err_msg.lower():
                logger.warning(f"Quota exceeded or rate limited: {err_msg}")
            else:
                logger.error(f"Gemini API Error: {err_msg}")
            raise

        return content

    def _extract_json(self, content: str) -> str:
        """Robustly extract JSON from potentially messy LLM response."""
        cleaned = content.strip()
        
        # Strip markdown fences
        if "```" in cleaned:
            if "```json" in cleaned:
                cleaned = cleaned.split("```json")[1].split("```")[0].strip()
            else:
                cleaned = cleaned.split("```")[1].split("```")[0].strip()
        
        # Find start/end of JSON object or array
        brace_start = cleaned.find("{")
        bracket_start = cleaned.find("[")
        
        start_idx = -1
        end_char = ""
        if brace_start != -1 and (bracket_start == -1 or brace_start < bracket_start):
            start_idx = brace_start
            end_char = "}"
        elif bracket_start != -1:
            start_idx = bracket_start
            end_char = "]"
            
        if start_idx != -1:
            end_idx = cleaned.rfind(end_char)
            if end_idx != -1:
                cleaned = cleaned[start_idx:end_idx+1]
        
        return cleaned

    def _execute_step_with_retry(self, step_name: str, prompt: str) -> Dict[str, Any]:
        """Execute a pipeline step with automatic retry and exponential backoff on 429s."""
        last_error = None
        base_delay = 5  # Starting delay in seconds for quota issues
        
        for attempt in range(self.max_retries):
            try:
                logger.info(f"[{step_name}] Attempt {attempt + 1}/{self.max_retries}")
                raw = self._call_llm(prompt)
                
                json_only = self._extract_json(raw)
                
                try:
                    parsed = json.loads(json_only)
                    logger.info(f"[{step_name}] Success on attempt {attempt + 1}")
                    return parsed
                except json.JSONDecodeError as je:
                    logger.error(f"[{step_name}] JSON Decode Error: {je}")
                    logger.debug(f"[{step_name}] Raw failed response: {raw}")
                    raise ValueError(f"Invalid JSON returned by AI: {json_only[:100]}...")
                
            except Exception as e:
                err_msg = str(e)
                last_error = f"{type(e).__name__}: {err_msg[:300]}"
                
                # Special handling for Rate Limits / Quota
                if any(x in err_msg.lower() for x in ["429", "quota", "resourceexhausted"]):
                    if attempt < self.max_retries - 1:
                        sleep_time = (base_delay * (2 ** attempt)) + random.uniform(0, 2)
                        logger.warning(f"[{step_name}] Quota hit. Retrying in {sleep_time:.2f}s...")
                        time.sleep(sleep_time)
                        # We don't modify the prompt on quota hit, just wait
                        continue
                    else:
                        raise ValueError(f"AI Service Quota Exceeded. Please try again later. (Error: {last_error})")
                
                logger.warning(f"[{step_name}] Error on attempt {attempt + 1}: {last_error}")
                
                if attempt < self.max_retries - 1:
                    # Specific prompt adjustment for non-quota errors (e.g., validation/JSON)
                    prompt += f"\n\nIMPORTANT: Your previous response was NOT valid. ERROR: {last_error}. Ensure you return ONLY valid JSON."
                else:
                    raise ValueError(f"Step '{step_name}' failed after {self.max_retries} retries. Last error: {last_error}")

        raise ValueError(f"Step '{step_name}' failed after {self.max_retries} retries. Last error: {last_error}")

    def generate_spec(self, requirements_text: str) -> Tuple[Dict[str, Any], int]:
        """
        Run the full 3-step pipeline to generate a specification.
        Returns (spec_dict, total_retries).
        """
        if self.mock_mode:
            return self._generate_mock(requirements_text), 0

        start = time.time()
        total_retries = 0

        # ── Step 1: Feature Extraction ──
        step1_prompt = STEP1_FEATURE_EXTRACTION.format(requirements_text=requirements_text)
        features_result = self._execute_step_with_retry("Feature Extraction", step1_prompt)

        # ── Step 2: User Story Generation ──
        step2_prompt = STEP2_USER_STORIES.format(features_json=json.dumps(features_result, indent=2))
        stories_result = self._execute_step_with_retry("User Story Generation", step2_prompt)

        # ── Step 3: API & DB Design ──
        step3_prompt = STEP3_API_DB_DESIGN.format(
            features_json=json.dumps(features_result, indent=2),
            stories_json=json.dumps(stories_result, indent=2)
        )
        api_db_result = self._execute_step_with_retry("API & DB Design", step3_prompt)

        processing_ms = int((time.time() - start) * 1000)

        # ── Merge all results ──
        spec = {
            "modules": features_result.get("modules", []),
            "features_by_module": features_result.get("features_by_module", {}),
            "user_stories": stories_result.get("user_stories", []),
            "api_endpoints": api_db_result.get("api_endpoints", []),
            "db_schema": api_db_result.get("db_schema", []),
            "open_questions": api_db_result.get("open_questions", []),
            "contradictions": api_db_result.get("contradictions", []),
            "metadata": {
                "original_requirements_length": len(requirements_text),
                "processing_time_ms": processing_ms,
                "llm_model": self.model_name,
                "total_retries": total_retries,
            }
        }
        return spec, total_retries

    def refine_spec(self, existing_spec: dict, refinement_instructions: str) -> Dict[str, Any]:
        """Refine an existing specification with new instructions."""
        if self.mock_mode:
            return self._refine_mock(existing_spec, refinement_instructions)

        prompt = REFINE_PROMPT.format(
            existing_spec_json=json.dumps(existing_spec, indent=2),
            refinement_instructions=refinement_instructions
        )
        result = self._execute_step_with_retry("Refinement", prompt)

        # Ensure all sections exist
        for key in ["modules", "features_by_module", "user_stories",
                     "api_endpoints", "db_schema", "open_questions", "contradictions"]:
            if key not in result:
                result[key] = existing_spec.get(key, [] if key != "features_by_module" else {})

        return result

    # ── Mock Generators ──────────────────────────────────────────────

    def _generate_mock(self, requirements_text: str) -> Dict[str, Any]:
        """Generate a realistic mock specification by analyzing the input text."""
        text_lower = requirements_text.lower()

        # Dynamic module/feature extraction based on keywords
        modules = []
        features_by_module = {}
        user_stories = []
        api_endpoints = []
        db_schema = []
        open_questions = []

        mod_counter = 1
        feat_counter = 1
        story_counter = 1
        ep_counter = 1
        oq_counter = 1

        # Keyword → module mapping
        domain_keywords = {
            "auth": ("User Authentication", "Handles user registration, login, and session management"),
            "login": ("User Authentication", "Handles user registration, login, and session management"),
            "signup": ("User Authentication", "Handles user registration, login, and session management"),
            "register": ("User Authentication", "Handles user registration, login, and session management"),
            "password": ("User Authentication", "Handles user registration, login, and session management"),
            "cart": ("Shopping Cart", "Manages shopping cart operations and item management"),
            "checkout": ("Order Management", "Handles order processing, checkout, and payment"),
            "payment": ("Payment Processing", "Manages payment transactions and billing"),
            "product": ("Product Catalog", "Manages product listings, categories, and inventory"),
            "inventory": ("Inventory Management", "Tracks stock levels and product availability"),
            "post": ("Content Management", "Handles creation and management of posts and content"),
            "comment": ("Social Interaction", "Manages comments, replies, and discussions"),
            "like": ("Social Interaction", "Manages likes, reactions, and engagement"),
            "follow": ("Social Networking", "Manages user connections and following relationships"),
            "notification": ("Notifications", "Handles push notifications, email, and in-app alerts"),
            "search": ("Search & Discovery", "Provides search functionality and content discovery"),
            "dashboard": ("Analytics Dashboard", "Displays metrics, charts, and business analytics"),
            "report": ("Reporting", "Generates and manages various reports"),
            "profile": ("User Profile", "Manages user profiles and account settings"),
            "message": ("Messaging", "Handles direct messaging and communication"),
            "chat": ("Messaging", "Handles real-time chat and communication"),
            "upload": ("File Management", "Handles file uploads, storage, and retrieval"),
            "image": ("Media Management", "Manages images, thumbnails, and media assets"),
            "review": ("Reviews & Ratings", "Manages user reviews and rating system"),
            "booking": ("Booking System", "Handles reservations and appointment booking"),
            "schedule": ("Scheduling", "Manages schedules, calendars, and time slots"),
            "subscription": ("Subscription Management", "Handles subscription plans and recurring billing"),
            "admin": ("Administration", "Admin panel for system management and oversight"),
            "role": ("Role Management", "Manages user roles and permissions"),
            "permission": ("Role Management", "Manages user roles and permissions"),
            "task": ("Task Management", "Handles task creation, assignment, and tracking"),
            "project": ("Project Management", "Manages projects, milestones, and team collaboration"),
            "email": ("Email Service", "Handles email sending, templates, and delivery"),
            "webhook": ("Integration", "Manages webhook endpoints and third-party integrations"),
            "api": ("API Management", "Manages API keys, rate limiting, and access control"),
            "setting": ("Settings", "Manages application and user settings"),
            "log": ("Audit & Logging", "Tracks system events and user activities"),
        }

        seen_modules = {}
        for keyword, (mod_name, mod_desc) in domain_keywords.items():
            if keyword in text_lower and mod_name not in seen_modules:
                mod_id = f"mod_{mod_counter:03d}"
                seen_modules[mod_name] = mod_id
                modules.append({
                    "module_id": mod_id,
                    "name": mod_name,
                    "description": mod_desc,
                    "priority": "high" if mod_counter <= 2 else "medium"
                })

                # Generate features for this module
                feats = self._generate_features_for_module(mod_name, feat_counter)
                features_by_module[mod_id] = feats
                feat_counter += len(feats)

                # Generate user stories
                for feat in feats:
                    stories = self._generate_stories_for_feature(mod_id, feat, story_counter)
                    user_stories.extend(stories)
                    story_counter += len(stories)

                # Generate endpoints
                endpoints = self._generate_endpoints_for_module(mod_name, ep_counter, story_counter - len(user_stories))
                api_endpoints.extend(endpoints)
                ep_counter += len(endpoints)

                # Generate DB tables
                tables = self._generate_tables_for_module(mod_name)
                db_schema.extend(tables)

                mod_counter += 1

        # If no modules detected, create a generic one
        if not modules:
            modules = [{"module_id": "mod_001", "name": "Core System", "description": "Primary system functionality as described in requirements", "priority": "high"}]
            features_by_module = {"mod_001": [{"feature_id": "feat_001", "name": "Core Feature", "description": "Primary feature derived from requirements", "priority": "high", "complexity": "moderate"}]}
            user_stories = [{"story_id": "us_001", "module_id": "mod_001", "feature_id": "feat_001", "as_a": "user", "i_want": "to use the core functionality", "so_that": "I can accomplish my goal", "acceptance_criteria": ["Feature is accessible", "Feature works as described"], "priority": "high"}]

        # Open questions
        open_questions = [
            {"question_id": f"oq_{oq_counter:03d}", "category": "authentication", "question": "What authentication method should be used?", "context": "Requirements mention user access but don't specify auth details", "priority": "high"},
            {"question_id": f"oq_{oq_counter+1:03d}", "category": "business_logic", "question": "Are there specific rate limits or usage quotas?", "context": "No rate limiting requirements explicitly stated", "priority": "medium"},
            {"question_id": f"oq_{oq_counter+2:03d}", "category": "data_model", "question": "What is the expected data retention policy?", "context": "No information about data archival or deletion", "priority": "low"},
        ]

        return {
            "modules": modules,
            "features_by_module": features_by_module,
            "user_stories": user_stories,
            "api_endpoints": api_endpoints,
            "db_schema": db_schema,
            "open_questions": open_questions,
            "contradictions": [],
            "metadata": {
                "original_requirements_length": len(requirements_text),
                "processing_time_ms": 150,
                "llm_model": "mock",
                "total_retries": 0
            }
        }

    def _generate_features_for_module(self, mod_name: str, start_id: int):
        feature_templates = {
            "User Authentication": [
                ("User Registration", "Allow new users to create accounts", "high", "moderate"),
                ("User Login", "Authenticate users with credentials", "high", "simple"),
                ("Password Reset", "Enable password recovery via email", "high", "moderate"),
                ("Session Management", "Handle user session tokens and expiry", "medium", "moderate"),
            ],
            "Shopping Cart": [
                ("Add to Cart", "Add products to shopping cart", "high", "simple"),
                ("Update Cart Item", "Modify quantity of items in cart", "high", "simple"),
                ("Remove from Cart", "Remove items from shopping cart", "high", "simple"),
                ("Cart Summary", "View current cart with totals", "medium", "simple"),
            ],
            "Order Management": [
                ("Place Order", "Convert cart to order with shipping details", "high", "complex"),
                ("Order Tracking", "Track order status and delivery", "high", "moderate"),
                ("Order History", "View past orders and details", "medium", "simple"),
                ("Cancel Order", "Cancel pending orders", "medium", "moderate"),
            ],
            "Payment Processing": [
                ("Process Payment", "Handle secure payment transactions", "high", "complex"),
                ("Payment Methods", "Support multiple payment methods", "high", "moderate"),
                ("Refund Processing", "Handle order refunds", "medium", "moderate"),
            ],
            "Product Catalog": [
                ("Product Listing", "Display products with filtering and sorting", "high", "moderate"),
                ("Product Details", "Show detailed product information", "high", "simple"),
                ("Category Management", "Organize products by categories", "medium", "simple"),
                ("Product Search", "Search products by name, description, etc.", "high", "moderate"),
            ],
            "Content Management": [
                ("Create Post", "Create new content posts", "high", "moderate"),
                ("Edit Post", "Modify existing posts", "high", "simple"),
                ("Delete Post", "Remove posts", "medium", "simple"),
                ("Post Feed", "Display chronological feed of posts", "high", "moderate"),
            ],
            "Social Interaction": [
                ("Add Comment", "Comment on posts or content", "high", "simple"),
                ("Like Content", "Like or react to posts", "high", "simple"),
                ("Reply to Comment", "Reply to existing comments", "medium", "simple"),
            ],
            "Notifications": [
                ("Push Notifications", "Send push notifications to users", "high", "moderate"),
                ("Notification Preferences", "Manage notification settings", "medium", "simple"),
                ("Notification History", "View past notifications", "low", "simple"),
            ],
            "Analytics Dashboard": [
                ("View Metrics", "Display key performance metrics", "high", "moderate"),
                ("Generate Charts", "Create visual data representations", "high", "complex"),
                ("Export Data", "Export dashboard data as CSV/PDF", "medium", "moderate"),
            ],
            "User Profile": [
                ("View Profile", "Display user profile information", "high", "simple"),
                ("Edit Profile", "Update profile details and avatar", "high", "moderate"),
                ("Account Settings", "Manage account preferences", "medium", "simple"),
            ],
            "Messaging": [
                ("Send Message", "Send direct messages to users", "high", "moderate"),
                ("Message Inbox", "View received messages", "high", "simple"),
                ("Message Thread", "View conversation history", "medium", "moderate"),
            ],
            "Task Management": [
                ("Create Task", "Create new tasks with details", "high", "moderate"),
                ("Assign Task", "Assign tasks to team members", "high", "simple"),
                ("Update Task Status", "Change task status (todo/in-progress/done)", "high", "simple"),
                ("Task Board View", "Kanban-style task board", "medium", "complex"),
            ],
        }

        features = feature_templates.get(mod_name, [
            ("Core Feature", "Primary feature for this module", "high", "moderate"),
        ])

        return [
            {
                "feature_id": f"feat_{start_id + i:03d}",
                "name": name,
                "description": desc,
                "priority": priority,
                "complexity": complexity
            }
            for i, (name, desc, priority, complexity) in enumerate(features)
        ]

    def _generate_stories_for_feature(self, mod_id, feat, start_id):
        role_map = {
            "high": "registered user",
            "medium": "authenticated user",
            "low": "power user"
        }
        role = role_map.get(feat["priority"], "user")
        return [{
            "story_id": f"us_{start_id:03d}",
            "module_id": mod_id,
            "feature_id": feat["feature_id"],
            "as_a": role,
            "i_want": f"to {feat['name'].lower()}",
            "so_that": f"I can {feat['description'].lower()}",
            "acceptance_criteria": [
                f"{feat['name']} is accessible from the main interface",
                f"{feat['name']} validates all required inputs",
                f"System provides confirmation upon successful {feat['name'].lower()}",
            ],
            "priority": feat["priority"]
        }]

    def _generate_endpoints_for_module(self, mod_name, start_id, story_start):
        endpoint_templates = {
            "User Authentication": [
                ("POST", "/api/auth/register", "Register a new user", "none"),
                ("POST", "/api/auth/login", "Authenticate user and return token", "none"),
                ("POST", "/api/auth/logout", "Invalidate user session", "required"),
                ("POST", "/api/auth/password-reset", "Request password reset link", "none"),
            ],
            "Shopping Cart": [
                ("GET", "/api/cart", "Get current user's cart", "required"),
                ("POST", "/api/cart/items", "Add item to cart", "required"),
                ("PUT", "/api/cart/items/{item_id}", "Update item quantity", "required"),
                ("DELETE", "/api/cart/items/{item_id}", "Remove item from cart", "required"),
            ],
            "Product Catalog": [
                ("GET", "/api/products", "List products with pagination/filtering", "none"),
                ("GET", "/api/products/{id}", "Get product details", "none"),
                ("POST", "/api/products", "Create new product", "required"),
                ("PUT", "/api/products/{id}", "Update product", "required"),
                ("DELETE", "/api/products/{id}", "Delete product", "required"),
            ],
            "Content Management": [
                ("GET", "/api/posts", "Get post feed with pagination", "optional"),
                ("POST", "/api/posts", "Create a new post", "required"),
                ("GET", "/api/posts/{id}", "Get post details", "optional"),
                ("PUT", "/api/posts/{id}", "Update a post", "required"),
                ("DELETE", "/api/posts/{id}", "Delete a post", "required"),
            ],
            "Task Management": [
                ("GET", "/api/tasks", "List tasks with filtering", "required"),
                ("POST", "/api/tasks", "Create a new task", "required"),
                ("GET", "/api/tasks/{id}", "Get task details", "required"),
                ("PUT", "/api/tasks/{id}", "Update task", "required"),
                ("PATCH", "/api/tasks/{id}/status", "Update task status", "required"),
                ("DELETE", "/api/tasks/{id}", "Delete task", "required"),
            ],
        }

        templates = endpoint_templates.get(mod_name, [
            ("GET", f"/api/{mod_name.lower().replace(' ', '-')}", f"List {mod_name.lower()} resources", "required"),
            ("POST", f"/api/{mod_name.lower().replace(' ', '-')}", f"Create {mod_name.lower()} resource", "required"),
        ])

        endpoints = []
        for i, (method, path, desc, auth) in enumerate(templates):
            ep_id = f"ep_{start_id + i:03d}"
            req_body = None
            if method in ("POST", "PUT", "PATCH"):
                req_body = {"example": "value"}
            endpoints.append({
                "endpoint_id": ep_id,
                "method": method,
                "path": path,
                "description": desc,
                "authentication": auth,
                "authorization": None,
                "request": {
                    "headers": {"Authorization": "Bearer <token>"} if auth == "required" else {},
                    "query_params": {"page": "integer", "limit": "integer"} if method == "GET" else {},
                    "body": req_body
                },
                "response": {
                    "success": {"status_code": 200 if method == "GET" else 201, "body": {"id": "string", "message": "Success"}},
                    "errors": [
                        {"status_code": 400, "description": "Invalid request data", "body": {"error": "Validation error"}},
                        {"status_code": 404, "description": "Resource not found", "body": {"error": "Not found"}},
                        {"status_code": 500, "description": "Internal server error", "body": {"error": "Internal error"}}
                    ]
                },
                "related_stories": []
            })
        return endpoints

    def _generate_tables_for_module(self, mod_name):
        table_templates = {
            "User Authentication": [{
                "table_name": "users",
                "description": "Stores user account information",
                "columns": [
                    {"name": "id", "type": "UUID", "nullable": False, "primary_key": True, "foreign_key": None, "default": "gen_random_uuid()", "constraints": []},
                    {"name": "email", "type": "VARCHAR(255)", "nullable": False, "primary_key": False, "foreign_key": None, "default": None, "constraints": ["UNIQUE"]},
                    {"name": "password_hash", "type": "VARCHAR(255)", "nullable": False, "primary_key": False, "foreign_key": None, "default": None, "constraints": []},
                    {"name": "is_active", "type": "BOOLEAN", "nullable": False, "primary_key": False, "foreign_key": None, "default": "true", "constraints": []},
                    {"name": "created_at", "type": "TIMESTAMP", "nullable": False, "primary_key": False, "foreign_key": None, "default": "NOW()", "constraints": []},
                    {"name": "updated_at", "type": "TIMESTAMP", "nullable": False, "primary_key": False, "foreign_key": None, "default": "NOW()", "constraints": []},
                ],
                "indexes": [{"name": "idx_users_email", "columns": ["email"], "unique": True}],
                "relationships": []
            }],
            "Shopping Cart": [{
                "table_name": "cart_items",
                "description": "Stores items in user shopping carts",
                "columns": [
                    {"name": "id", "type": "UUID", "nullable": False, "primary_key": True, "foreign_key": None, "default": "gen_random_uuid()", "constraints": []},
                    {"name": "user_id", "type": "UUID", "nullable": False, "primary_key": False, "foreign_key": "users.id", "default": None, "constraints": []},
                    {"name": "product_id", "type": "UUID", "nullable": False, "primary_key": False, "foreign_key": "products.id", "default": None, "constraints": []},
                    {"name": "quantity", "type": "INTEGER", "nullable": False, "primary_key": False, "foreign_key": None, "default": "1", "constraints": ["CHECK (quantity > 0)"]},
                    {"name": "created_at", "type": "TIMESTAMP", "nullable": False, "primary_key": False, "foreign_key": None, "default": "NOW()", "constraints": []},
                ],
                "indexes": [{"name": "idx_cart_user", "columns": ["user_id"], "unique": False}],
                "relationships": [{"type": "many-to-one", "target_table": "users", "description": "Each cart item belongs to a user"}]
            }],
        }

        return table_templates.get(mod_name, [{
            "table_name": mod_name.lower().replace(" ", "_") + "s",
            "description": f"Stores {mod_name.lower()} data",
            "columns": [
                {"name": "id", "type": "UUID", "nullable": False, "primary_key": True, "foreign_key": None, "default": "gen_random_uuid()", "constraints": []},
                {"name": "name", "type": "VARCHAR(255)", "nullable": False, "primary_key": False, "foreign_key": None, "default": None, "constraints": []},
                {"name": "created_at", "type": "TIMESTAMP", "nullable": False, "primary_key": False, "foreign_key": None, "default": "NOW()", "constraints": []},
                {"name": "updated_at", "type": "TIMESTAMP", "nullable": False, "primary_key": False, "foreign_key": None, "default": "NOW()", "constraints": []},
            ],
            "indexes": [],
            "relationships": []
        }])

    def _refine_mock(self, existing_spec: dict, instructions: str) -> dict:
        """Mock refinement — add an open question noting the refinement."""
        spec = dict(existing_spec)
        oqs = spec.get("open_questions", [])
        oqs.append({
            "question_id": f"oq_{len(oqs)+1:03d}",
            "category": "other",
            "question": f"Refinement applied: {instructions}",
            "context": "This was processed in mock mode — full LLM refinement not available",
            "priority": "medium"
        })
        spec["open_questions"] = oqs
        return spec
