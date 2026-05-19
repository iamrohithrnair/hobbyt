import os
import io
import json
import zipfile
import traceback
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, UploadFile, File, HTTPException, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from gemini_service import GeminiAnalyzer, GeminiStorage
from dotenv import load_dotenv
from google import genai

# Load environment variables
load_dotenv()

app = FastAPI(title="Hobbyt – Gemini Repository Analyzer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

analyzer = GeminiAnalyzer()

# Pydantic Models for /generate endpoint
class RoboticsDescription(BaseModel):
    description: str = Field(
        ..., 
        description="Plain English description of the robotics project",
        example="Arduino Uno, 2 DC motors, IR sensor, line follower"
    )

class RoboticsProject(BaseModel):
    folder_structure: Dict[str, Any] = Field(
        ..., 
        description="Nested dictionary representing the project folder structure"
    )
    pin_wiring: Dict[str, Any] = Field(
        ..., 
        description="Component-to-pin mappings for hardware connections"
    )
    starter_code: str = Field(
        ..., 
        description="Complete starter code for the robotics project"
    )
    readme: str = Field(
        ..., 
        description="Markdown documentation for the project"
    )
    codebase_files: Dict[str, str] = Field(
        default_factory=dict,
        description="Complete generated source, config, and documentation files keyed by relative path"
    )
    architecture: Optional[Dict[str, Any]] = Field(default=None, description="Generated software architecture summary")
    hardware_mapping: Optional[Dict[str, Any]] = Field(default=None, description="Generated hardware mapping summary")
    control_flow: Optional[Dict[str, Any]] = Field(default=None, description="Generated control flow summary")
    communication: Optional[Dict[str, Any]] = Field(default=None, description="Generated communication summary")
    risks: Optional[List[str]] = Field(default=None, description="Generated hardware/software risks")
    onboarding_summary: Optional[Dict[str, Any]] = Field(default=None, description="Generated onboarding summary")

# Initialize Google Gemini client
def get_gemini_client() -> genai.Client:
    """Initialize and return the Google Gemini client."""
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="GEMINI_API_KEY must be set in .env file"
        )
    
    return genai.Client(api_key=api_key)


def get_model_id() -> str:
    """Return the configured Gemini model ID."""
    return os.getenv("GEMINI_MODEL_ID", "gemini-3.1-flash-lite")


def create_robotics_prompt(description: str) -> str:
    """Create a structured prompt for generating robotics project details"""
    return f"""You are an expert robotics engineer. Given a plain English description of a robotics project, generate a complete project structure.

Project Description: {description}

Generate a JSON response with the following structure:
{{
  "folder_structure": {{
    "project_name": {{
      "src": ["main.ino or main.py"],
      "lib": ["library files"],
      "docs": ["documentation files"],
      "examples": ["example files"]
    }}
  }},
  "pin_wiring": {{
    "component_name": {{
      "pin_type": "pin_number or pin_name",
      "description": "connection description"
    }}
  }},
  "architecture": {{
    "overview": "2-3 sentence summary of the generated project architecture",
    "patterns": ["pattern 1", "pattern 2"]
  }},
  "hardware_mapping": {{
    "resource_utilization": "description of target board resources, GPIO, power, and peripherals",
    "deployment_targets": ["target board or runtime"],
    "io_strategy": "description of the I/O strategy"
  }},
  "control_flow": {{
    "primary_pipeline": "description of setup, loop, and runtime flow",
    "error_handling": "description of expected failure handling"
  }},
  "communication": {{
    "internal": "description of internal module communication",
    "external": "description of external communication, if any",
    "protocols": ["protocol 1", "protocol 2"]
  }},
  "risks": ["risk 1", "risk 2"],
  "onboarding_summary": {{
    "tldr": "2-3 sentence quick-start guide",
    "quick_start": "short setup flow",
    "key_files": ["src/main.ino", "README.md"]
  }},
  "codebase_files": {{
    "relative/path/to/file.ext": "Complete contents for this file"
  }},
  "starter_code": "Complete working code with comments",
  "readme": "# Project Title\\n\\n## Description\\n\\n## Components\\n\\n## Wiring\\n\\n## Setup\\n\\n## Usage"
}}

Requirements:
1. Identify all components mentioned in the description
2. Create appropriate folder structure for the project type (Arduino, Raspberry Pi, etc.)
3. Generate accurate pin wiring based on standard practices
4. Generate the complete codebase in `codebase_files`, including source files, headers/modules, config, docs, examples, and README where useful
5. Set `starter_code` to the main entrypoint file content, but do not make it the only code artifact
6. Update architecture, hardware_mapping, control_flow, communication, risks, and onboarding_summary so they describe the generated codebase
7. Create a brief README with setup instructions
8. CRITICAL: Use \\n for newlines in code strings instead of actual line breaks

IMPORTANT: Ensure you close all JSON braces and quotes correctly. Generate ONLY the JSON object.
Generate ONLY valid JSON. Do not include any text before or after the JSON object."""


def parse_llm_response(response_text: str, required_fields: Optional[List[str]] = None) -> Dict[str, Any]:
    """Parse and validate the LLM response text"""
    try:
        # Strip markdown code blocks if present (e.g., ```json ... ```)
        text = response_text.strip()
        if text.startswith('```'):
            # Remove opening code fence
            lines = text.split('\n')
            if lines[0].startswith('```'):
                lines = lines[1:]
            # Remove closing code fence
            if lines and lines[-1].strip() == '```':
                lines = lines[:-1]
            text = '\n'.join(lines)
        
        # Try to find JSON in the response
        start_idx = text.find('{')
        end_idx = text.rfind('}') + 1
        
        if start_idx == -1 or end_idx == 0:
            print("=== RAW MODEL RESPONSE ===")
            print(text)
            print("==========================")
            raise ValueError("No JSON object found in response")
        
        json_str = text[start_idx:end_idx]
        # Use strict=False to allow control characters
        parsed = json.loads(json_str, strict=False)
        
        # Validate required fields
        if required_fields is None:
            required_fields = ["folder_structure", "pin_wiring", "starter_code", "readme"]
        for field in required_fields:
            if field not in parsed:
                raise ValueError(f"Missing required field: {field}")
        
        return parsed
    except json.JSONDecodeError as e:
        print("=== JSON DECODE ERROR RAW STRING ===")
        print(json_str if 'json_str' in locals() else "JSON string not extracted")
        print("=====================================")
        raise ValueError(f"Invalid JSON in response: {str(e)}")
    except Exception as e:
        raise ValueError(f"Error parsing response: {str(e)}")

TEXT_CODEBASE_EXTENSIONS = {
    ".ino", ".cpp", ".c", ".h", ".hpp", ".py", ".js", ".jsx", ".ts", ".tsx",
    ".json", ".yaml", ".yml", ".toml", ".md", ".txt", ".cfg", ".ini", ".cmake",
    ".sh", ".bat", ".html", ".css", ".scss", ".rs", ".go", ".java", ".kt",
    ".swift", ".xml", ".csv", ".dockerfile"
}
SENSITIVE_CODEBASE_NAMES = {
    ".env", ".env.local", ".env.production", ".env.development", "id_rsa",
    "id_dsa", "id_ecdsa", "id_ed25519", "credentials.json", "secrets.json"
}
MAX_CODEBASE_FILE_CHARS = 20000
MAX_CODEBASE_TOTAL_CHARS = 160000

def is_codebase_text_file(path: str) -> bool:
    name = os.path.basename(path).lower()
    if name in SENSITIVE_CODEBASE_NAMES or name.endswith((".pem", ".key", ".crt", ".p12", ".pfx")):
        return False
    _, ext = os.path.splitext(name)
    return ext in TEXT_CODEBASE_EXTENSIONS or name in {"makefile", "dockerfile", ".env.example"}

def collect_codebase_files(zf: zipfile.ZipFile, file_list: List[str]) -> Dict[str, str]:
    files = {}
    total_chars = 0
    for name in file_list:
        if name.endswith("/") or not is_codebase_text_file(name):
            continue
        try:
            info = zf.getinfo(name)
            if info.file_size > 750000:
                continue
            content = zf.read(name).decode("utf-8", errors="ignore")
        except Exception:
            continue
        if "\x00" in content[:1000]:
            continue
        remaining = MAX_CODEBASE_TOTAL_CHARS - total_chars
        if remaining <= 0:
            break
        text = content[:min(MAX_CODEBASE_FILE_CHARS, remaining)]
        if len(content) > len(text):
            text += "\n\n[truncated]"
        files[name] = text
        total_chars += len(text)
    return files

def default_code_path(folder_structure: Dict[str, Any], fallback: str = "src/main.py") -> str:
    def walk(node, prefix=""):
        if isinstance(node, dict):
            for key, value in node.items():
                result = walk(value, f"{prefix}{key}/")
                if result:
                    return result
        elif isinstance(node, list):
            for item in node:
                if isinstance(item, str):
                    item_path = f"{prefix}{item}"
                    if is_codebase_text_file(item_path) and os.path.splitext(item_path.lower())[1] in {".ino", ".cpp", ".c", ".py", ".js", ".jsx", ".ts", ".tsx"}:
                        return item_path
        return None
    return walk(folder_structure) or fallback

def ensure_codebase_files(data: Dict[str, Any]) -> Dict[str, Any]:
    codebase_files = data.get("codebase_files")
    if not isinstance(codebase_files, dict) or not codebase_files:
        folder_structure = data.get("folder_structure") if isinstance(data.get("folder_structure"), dict) else {}
        main_path = default_code_path(folder_structure)
        codebase_files = {}
        if data.get("starter_code"):
            codebase_files[main_path] = data["starter_code"]
        if data.get("readme"):
            codebase_files["README.md"] = data["readme"]
        data["codebase_files"] = codebase_files
    return data

def normalize_remap_response(data: Dict[str, Any]) -> Dict[str, Any]:
    ensure_codebase_files(data)
    if "alternative_pin_wiring" not in data and "pin_wiring" in data:
        data["alternative_pin_wiring"] = data["pin_wiring"]
    if "pin_wiring" not in data and "alternative_pin_wiring" in data:
        data["pin_wiring"] = data["alternative_pin_wiring"]
    if "alternative_starter_code" not in data and "starter_code" in data:
        data["alternative_starter_code"] = data["starter_code"]
    if "starter_code" not in data and "alternative_starter_code" in data:
        data["starter_code"] = data["alternative_starter_code"]
    if "file_tree" not in data:
        data["file_tree"] = sorted(data.get("codebase_files", {}).keys())
    return data

@app.post("/analyze")
async def analyze_repository(
    file: Optional[UploadFile] = File(None),
    github_url: Optional[str] = Form(None)
):
    """
    Reads an uploaded .zip repository or downloads a GitHub repository URL,
    and uses Google Gemini to analyze its architecture, hardware mapping,
    control flow, protocols, risks, and generate an onboarding summary.
    """
    try:
        raw = None
        if file is not None and file.filename:
            # Read the uploaded zip bytes
            raw = await file.read()
        elif github_url:
            import urllib.request
            import re
            url_str = github_url.strip()
            
            # Match standard GitHub URL formats
            match = re.match(r"(?:https?://)?(?:www\.)?github\.com/([^/]+)/([^/]+?)(?:\.git|/)?$", url_str)
            if not match:
                raise HTTPException(status_code=400, detail="Invalid GitHub URL format. Use: https://github.com/owner/repo")
            
            owner, repo = match.groups()
            zip_url = f"https://api.github.com/repos/{owner}/{repo}/zipball"
            
            try:
                req = urllib.request.Request(
                    zip_url,
                    headers={"User-Agent": "Hobbyt-App"}
                )
                with urllib.request.urlopen(req, timeout=20) as response:
                    raw = response.read()
            except Exception as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to fetch GitHub repository from {zip_url}. Ensure the repo is public. Error: {str(e)}"
                )
        else:
            raise HTTPException(status_code=400, detail="Either a .zip file or a github_url must be provided.")

        file_list = []
        codebase_files = {}
        code_sample = ""
        try:
            with zipfile.ZipFile(io.BytesIO(raw)) as zf:
                file_list = zf.namelist()
                codebase_files = collect_codebase_files(zf, file_list)
                # Grab up to 6000 chars of source code for context
                for name in file_list:
                    if any(name.endswith(ext) for ext in (".ino", ".cpp", ".c", ".h", ".py", ".js")):
                        try:
                            content = zf.read(name).decode("utf-8", errors="ignore")
                            code_sample += f"\n\n// === {name} ===\n" + content[:1500]
                            if len(code_sample) > 6000:
                                break
                        except Exception:
                            pass
        except zipfile.BadZipFile:
            raise HTTPException(status_code=400, detail="The repository content is not a valid .zip archive.")

        file_tree = "\n".join(file_list[:60])

        prompt = f"""You are an expert robotics software engineer performing a deep repository analysis.

Repository file tree:
{file_tree}

Code sample:
{code_sample[:4000] if code_sample else 'No source code found.'}

Analyze this robotics codebase and return ONLY a valid JSON object with this exact structure:
{{
  "architecture": {{
    "overview": "2-3 sentence summary of the overall architecture and design pattern",
    "patterns": ["pattern 1", "pattern 2", "pattern 3"]
  }},
  "hardware_mapping": {{
    "resource_utilization": "description of detected hardware targets and boards",
    "deployment_targets": ["target 1", "target 2"]
  }},
  "control_flow": {{
    "primary_pipeline": "description of the main execution loop or pipeline",
    "error_handling": "description of error handling strategy"
  }},
  "communication": {{
    "internal": "description of internal communication patterns",
    "protocols": ["protocol 1", "protocol 2"]
  }},
  "risks": ["risk 1", "risk 2", "risk 3"],
  "onboarding_summary": {{
    "tldr": "2-3 sentence quick-start guide for a new developer",
    "key_files": ["file1", "file2", "file3"]
  }}
}}

Generate ONLY valid JSON. No text before or after."""

        client = get_gemini_client()
        response = client.models.generate_content(
            model=get_model_id(),
            contents=prompt,
        )

        text = response.text.strip()

        # Strip markdown fences
        if text.startswith("```"):
            lines = text.split("\n")
            lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines)

        start = text.find("{")
        end = text.rfind("}") + 1
        if start == -1 or end == 0:
            raise ValueError("No JSON found in analysis response")

        parsed = json.loads(text[start:end], strict=False)
        # Inject the file tree so the frontend can display it
        parsed["file_tree"] = file_list
        parsed["codebase_files"] = codebase_files
        return parsed

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.get("/live-updates")
async def get_live_updates():
    """
    Polling endpoint for the frontend to get insights pushed by the Gemini agent.
    """
    stored = GeminiStorage.get()
    if stored:
        return stored
    return {"status": "waiting", "message": "Gemini is thinking..."}

@app.get("/status")
async def get_status():
    return {
        "status": "online",
        "engine": "Google Gemini (ADK Agent)",
        "model": get_model_id(),
        "mcp_enabled": True
    }

@app.post("/generate", response_model=RoboticsProject)
async def generate_robotics_project(request: RoboticsDescription):
    """
    Generate a complete robotics project from a plain English description.
    
    This endpoint uses Google Gemini to generate:
    - Project folder structure
    - Pin wiring diagrams
    - Starter code
    - README documentation
    
    Example request:
    {
        "description": "Arduino Uno, 2 DC motors, IR sensor, line follower"
    }
    """
    try:
        client = get_gemini_client()
        prompt = create_robotics_prompt(request.description)
        
        response = client.models.generate_content(
            model=get_model_id(),
            contents=prompt,
        )
        
        # Parse and validate the response
        parsed_response = ensure_codebase_files(parse_llm_response(response.text))
        
        # Return the structured response
        return RoboticsProject(**parsed_response)
        
    except HTTPException:
        raise
    except ValueError as e:
        print("ValueError in /generate endpoint:")
        traceback.print_exc()
        raise HTTPException(
            status_code=422,
            detail=f"Failed to parse LLM response: {str(e)}"
        )
    except Exception as e:
        print("Exception in /generate endpoint:")
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Error generating robotics project: {str(e)}"
        )

class HardwareRemapRequest(BaseModel):
    target_hardware: str = Field(..., description="Target hardware description from user prompt")
    current_context: Dict[str, Any] = Field(..., description="Existing results/analysis details")

def run_async_remap(target_hardware: str, current_context: Dict[str, Any]):
    import time
    try:
        GeminiStorage.update_remap(
            status="processing",
            message="Initializing Hobbyt Rebuild Agent...",
            logs=[
                "Initializing Hobbyt Rebuild Agent...",
                "Pulling analyzed repository code architecture..."
            ],
            data=None
        )
        time.sleep(1.0)
        
        GeminiStorage.add_remap_log("Step 1/6: Loading original codebase, pin architecture map and target specifications...")
        time.sleep(1.5)
        
        GeminiStorage.add_remap_log(f"Step 2/6: Designing hardware remapping schema to target: '{target_hardware}'...")
        time.sleep(1.5)
        
        GeminiStorage.add_remap_log("Step 3/6: Rebuilding every source, config, documentation, and example file...")
        time.sleep(1.5)
        
        GeminiStorage.add_remap_log("Step 4/6: Regenerating hardware map, control flow, communication, and risk model...")
        
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY must be set in .env file")
        client = genai.Client(api_key=api_key)
        remap_context = {k: v for k, v in current_context.items() if k != "file_tree"}
        
        prompt = f"""You are a professional robotics hardware engineer and expert software/firmware developer.
Your task is to remap, convert, and rebuild an existing robotics project based on the user's instructions.
The instructions can request HARDWARE changes (e.g., migrating from ESP32 to Raspberry Pi Pico or Raspberry Pi 4/5), SOFTWARE changes (e.g., changing APIs from Anthropic Claude SDK to Google Gemini SDK, adding logic, modifying functionality), or BOTH.

Remap & Rebuild Instructions:
{target_hardware}

Current Project Context:
{json.dumps(remap_context, indent=2)}

Please perform the rebuild and remapping across the entire project.
Rules:
1. Rebuild the complete codebase, not just the starter or main file. Return every rewritten source, header/module, config, docs, examples, and README file in `codebase_files`.
2. If the original context includes `codebase_files`, convert each relevant file while preserving the original project intent. If it only includes a starter code snippet or folder structure, synthesize a coherent complete codebase from that context.
3. If the user instructions specify a change of platform (e.g. moving from a microcontroller like ESP32 to a single-board computer like Raspberry Pi), rewrite the codebase in the appropriate language and library ecosystem (e.g., Python using RPi.GPIO or gpiozero instead of C++ Arduino code).
4. If the user instructions request converting APIs (e.g. from Claude Desktop Buddy to Gemini Desktop Buddy), update all affected files to import, configure, and call the correct SDK using valid libraries and patterns.
5. Regenerate the hardware map, physical pin wiring, control flow, communication model, risks, and onboarding guide so they describe the rebuilt codebase and target board.
6. Map the physical pin connections accurately in `pin_wiring` to the new board's header pins.
7. Output a helpful list of hardware, voltage, logic level shifters, or dependency setup warnings.

You MUST return ONLY a valid JSON object with this exact structure:
{{
  "target_board_name": "Official name of the target board, e.g. Raspberry Pi 4 / 5 or Raspberry Pi Pico",
  "architecture": {{
    "overview": "2-3 sentence summary of the rebuilt architecture and design pattern",
    "patterns": ["pattern 1", "pattern 2", "pattern 3"],
    "tech_stack": ["runtime or framework 1", "library 2"]
  }},
  "hardware_mapping": {{
    "resource_utilization": "description of target board resources, GPIO, power, and peripherals",
    "deployment_targets": ["target 1", "target 2"],
    "io_strategy": "description of pin, bus, interrupt, PWM, ADC, and timing strategy"
  }},
  "control_flow": {{
    "primary_pipeline": "description of setup/init, main loop/task flow, and shutdown behavior",
    "error_handling": "description of hardware/software failure handling"
  }},
  "communication": {{
    "internal": "description of internal module/task communication",
    "external": "description of external IO or network communication",
    "protocols": ["protocol 1", "protocol 2"]
  }},
  "risks": [
     "Specific technical or hardware risk in the rebuilt project"
  ],
  "onboarding_summary": {{
    "tldr": "2-3 sentence guide for a new developer",
    "quick_start": "short ordered setup flow",
    "key_files": ["relative/path/to/key_file.ext"]
  }},
  "folder_structure": {{
     "project_name": {{
        "src": ["main.py or main.ino"],
        "lib": ["helper files"],
        "docs": ["docs files"],
        "examples": ["example files"]
     }}
  }},
  "pin_wiring": {{
     "component_name": {{
        "pin_label": "remapped_pin_or_GPIO_details"
     }}
  }},
  "codebase_files": {{
     "relative/path/to/file.ext": "Complete remapped file contents with newline characters escaped as \\n"
  }},
  "starter_code": "The main entrypoint file content from codebase_files.",
  "readme": "# Rebuilt Project\\n\\nSetup, wiring, dependency, and usage instructions.",
  "warnings": [
     "Specific voltage differences (e.g. 3.3V vs 5V), logic level shifters, library dependencies, or setup instructions.",
     "E.g., for Raspberry Pi, mention installing python-dependencies or google-genai package."
  ]
}}

Generate ONLY valid JSON. No text before or after."""

        response = client.models.generate_content(
            model=get_model_id(),
            contents=prompt,
        )
        
        parsed_response = parse_llm_response(
            response.text,
            required_fields=[
                "target_board_name", "architecture", "hardware_mapping",
                "control_flow", "communication", "risks", "onboarding_summary",
                "folder_structure", "pin_wiring", "codebase_files",
                "starter_code", "readme", "warnings"
            ]
        )
        parsed_response = normalize_remap_response(parsed_response)
        
        GeminiStorage.add_remap_log("Step 5/6: Validated rebuilt codebase payload and compatibility aliases.")
        time.sleep(0.5)
        GeminiStorage.add_remap_log("Step 6/6: Completed! Entire codebase and analysis model successfully rebuilt.")
        
        GeminiStorage.update_remap(
            status="success",
            message="Rebuild completed successfully!",
            data=parsed_response
        )
    except Exception as e:
        traceback.print_exc()
        GeminiStorage.add_remap_log(f"Error during remapping: {str(e)}")
        GeminiStorage.update_remap(
            status="failed",
            message=f"Remapping failed: {str(e)}",
            data=None
        )

@app.post("/remap")
async def remap_hardware(request: HardwareRemapRequest, background_tasks: BackgroundTasks):
    """
    Remaps the codebase, pins, and warning guides to any alternative board target asynchronously.
    """
    GeminiStorage.update_remap(
        status="processing",
        message="Starting async remapper task...",
        logs=["Spawning background thread..."],
        data=None
    )
    background_tasks.add_task(run_async_remap, request.target_hardware, request.current_context)
    return {"status": "processing", "message": "Remapping process initialized asynchronously in background."}

@app.get("/remap-status")
async def get_remap_status():
    """
    Polls the live remapping progress logs, status and final results payload.
    """
    return GeminiStorage.get_remap()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# Powered by Google Gemini
