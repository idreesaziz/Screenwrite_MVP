"""
Comprehensive test suite for composition generation endpoint.
Tests various scenarios to ensure implicit root system and composition editing work correctly.
"""

import asyncio
import httpx
import json
from typing import List, Dict, Any

# Backend URL
BACKEND_URL = "http://localhost:8001"
GENERATE_ENDPOINT = f"{BACKEND_URL}/ai/generate-composition"

# Test scenarios
TEST_SCENARIOS = [
    {
        "name": "Simple text composition from scratch",
        "request": {
            "user_request": "Create a simple title that says 'Hello World' in white text",
            "preview_settings": {"width": 1920, "height": 1080, "fps": 30},
            "media_library": [],
            "current_composition": None,
            "conversation_history": [],
            "model_type": "gemini"
        },
        "checks": [
            ("has_elements", "Should have elements array"),
            ("no_explicit_root", "Should not have explicit AbsoluteFill"),
            ("uses_parent_root", "Should use parent:root for top-level elements"),
            ("has_text_content", "Should have text content")
        ]
    },
    {
        "name": "Update existing composition - add element",
        "request": {
            "user_request": "Add a subtitle that says 'Welcome' below the title",
            "preview_settings": {"width": 1920, "height": 1080, "fps": 30},
            "media_library": [],
            "current_composition": [
                {
                    "id": "clip1",
                    "start": 0,
                    "duration": 5,
                    "elements": [
                        "h1;id:title;parent:root;text:Hello World;fontSize:48px;color:white;top:20%"
                    ]
                }
            ],
            "conversation_history": [],
            "model_type": "gemini"
        },
        "checks": [
            ("has_elements", "Should have elements array"),
            ("has_multiple_elements", "Should have multiple elements"),
            ("no_explicit_root", "Should not have explicit AbsoluteFill"),
            ("returns_full_composition", "Should return full composition with changes")
        ]
    },
    {
        "name": "Composition with animation",
        "request": {
            "user_request": "Create a title that fades in from opacity 0 to 1 over 30 frames",
            "preview_settings": {"width": 1920, "height": 1080, "fps": 30},
            "media_library": [],
            "current_composition": None,
            "conversation_history": [],
            "model_type": "gemini"
        },
        "checks": [
            ("has_elements", "Should have elements array"),
            ("has_animation", "Should have @animate syntax"),
            ("no_explicit_root", "Should not have explicit AbsoluteFill")
        ]
    },
    {
        "name": "Composition with nested elements",
        "request": {
            "user_request": "Create a container div with two text elements inside it",
            "preview_settings": {"width": 1920, "height": 1080, "fps": 30},
            "media_library": [],
            "current_composition": None,
            "conversation_history": [],
            "model_type": "gemini"
        },
        "checks": [
            ("has_elements", "Should have elements array"),
            ("has_nested_structure", "Should have parent-child relationships"),
            ("no_explicit_root", "Should not have explicit AbsoluteFill")
        ]
    },
    {
        "name": "Composition with media",
        "request": {
            "user_request": "Add the video from media library as background",
            "preview_settings": {"width": 1920, "height": 1080, "fps": 30},
            "media_library": [
                {"id": "video1", "type": "video", "src": "https://example.com/video.mp4", "duration": 10}
            ],
            "current_composition": None,
            "conversation_history": [],
            "model_type": "gemini"
        },
        "checks": [
            ("has_elements", "Should have elements array"),
            ("has_video_element", "Should have Video component"),
            ("no_explicit_root", "Should not have explicit AbsoluteFill")
        ]
    },
    {
        "name": "Update with deletion",
        "request": {
            "user_request": "Remove the subtitle",
            "preview_settings": {"width": 1920, "height": 1080, "fps": 30},
            "media_library": [],
            "current_composition": [
                {
                    "id": "clip1",
                    "start": 0,
                    "duration": 5,
                    "elements": [
                        "h1;id:title;parent:root;text:Hello World;fontSize:48px;color:white;top:20%",
                        "p;id:subtitle;parent:root;text:Welcome;fontSize:24px;color:gray;top:30%"
                    ]
                }
            ],
            "conversation_history": [],
            "model_type": "gemini"
        },
        "checks": [
            ("has_elements", "Should have elements array"),
            ("returns_full_composition", "Should return full composition"),
            ("no_explicit_root", "Should not have explicit AbsoluteFill")
        ]
    },
    {
        "name": "Complex multi-track composition",
        "request": {
            "user_request": "Create two clips: first with title 'Scene 1', second with title 'Scene 2'",
            "preview_settings": {"width": 1920, "height": 1080, "fps": 30},
            "media_library": [],
            "current_composition": None,
            "conversation_history": [],
            "model_type": "gemini"
        },
        "checks": [
            ("has_multiple_tracks", "Should have multiple tracks"),
            ("each_track_has_elements", "Each track should have elements"),
            ("no_explicit_root", "Should not have explicit AbsoluteFill in any track")
        ]
    }
]

# Validation functions
def check_has_elements(response_data: Dict[str, Any]) -> bool:
    """Check if response has composition with elements."""
    try:
        composition = json.loads(response_data["composition_code"])
        if "tracks" in composition:
            return any("elements" in track for track in composition["tracks"])
        return False
    except:
        return False

def check_no_explicit_root(response_data: Dict[str, Any]) -> bool:
    """Check that no track has explicit AbsoluteFill elements."""
    try:
        composition = json.loads(response_data["composition_code"])
        if "tracks" in composition:
            for track in composition["tracks"]:
                if "elements" in track:
                    for element in track["elements"]:
                        if element.startswith("AbsoluteFill;"):
                            return False
        return True
    except:
        return False

def check_uses_parent_root(response_data: Dict[str, Any]) -> bool:
    """Check that elements use parent:root (not parent:null)."""
    try:
        composition = json.loads(response_data["composition_code"])
        if "tracks" in composition:
            for track in composition["tracks"]:
                if "elements" in track:
                    for element in track["elements"]:
                        # Check for parent:root in at least one element
                        if "parent:root" in element:
                            return True
                        # Fail if we see parent:null
                        if "parent:null" in element:
                            return False
        return True  # No parent:null found
    except:
        return False

def check_has_text_content(response_data: Dict[str, Any]) -> bool:
    """Check that response has text content."""
    try:
        composition = json.loads(response_data["composition_code"])
        if "tracks" in composition:
            for track in composition["tracks"]:
                if "elements" in track:
                    for element in track["elements"]:
                        if "text:" in element:
                            return True
        return False
    except:
        return False

def check_has_multiple_elements(response_data: Dict[str, Any]) -> bool:
    """Check that response has multiple elements."""
    try:
        composition = json.loads(response_data["composition_code"])
        if "tracks" in composition:
            for track in composition["tracks"]:
                if "elements" in track and len(track["elements"]) > 1:
                    return True
        return False
    except:
        return False

def check_returns_full_composition(response_data: Dict[str, Any]) -> bool:
    """Check that response returns complete composition structure."""
    try:
        composition = json.loads(response_data["composition_code"])
        return "tracks" in composition and len(composition["tracks"]) > 0
    except:
        return False

def check_has_animation(response_data: Dict[str, Any]) -> bool:
    """Check that response has animation syntax."""
    try:
        composition = json.loads(response_data["composition_code"])
        if "tracks" in composition:
            for track in composition["tracks"]:
                if "elements" in track:
                    for element in track["elements"]:
                        if "@animate" in element:
                            return True
        return False
    except:
        return False

def check_has_nested_structure(response_data: Dict[str, Any]) -> bool:
    """Check that response has nested parent-child relationships."""
    try:
        composition = json.loads(response_data["composition_code"])
        if "tracks" in composition:
            for track in composition["tracks"]:
                if "elements" in track:
                    # Look for elements that reference other elements as parent (not root)
                    element_ids = set()
                    for element in track["elements"]:
                        # Extract id
                        if "id:" in element:
                            id_part = element.split("id:")[1].split(";")[0]
                            element_ids.add(id_part)
                    
                    # Check if any element references another element as parent
                    for element in track["elements"]:
                        if "parent:" in element:
                            parent = element.split("parent:")[1].split(";")[0]
                            if parent != "root" and parent in element_ids:
                                return True
        return False
    except:
        return False

def check_has_video_element(response_data: Dict[str, Any]) -> bool:
    """Check that response has Video component."""
    try:
        composition = json.loads(response_data["composition_code"])
        if "tracks" in composition:
            for track in composition["tracks"]:
                if "elements" in track:
                    for element in track["elements"]:
                        if element.startswith("Video;") or element.startswith("OffthreadVideo;"):
                            return True
        return False
    except:
        return False

def check_has_multiple_tracks(response_data: Dict[str, Any]) -> bool:
    """Check that response has multiple tracks."""
    try:
        composition = json.loads(response_data["composition_code"])
        return "tracks" in composition and len(composition["tracks"]) > 1
    except:
        return False

def check_each_track_has_elements(response_data: Dict[str, Any]) -> bool:
    """Check that each track has elements."""
    try:
        composition = json.loads(response_data["composition_code"])
        if "tracks" in composition:
            return all("elements" in track and len(track["elements"]) > 0 
                      for track in composition["tracks"])
        return False
    except:
        return False

# Map check names to functions
CHECK_FUNCTIONS = {
    "has_elements": check_has_elements,
    "no_explicit_root": check_no_explicit_root,
    "uses_parent_root": check_uses_parent_root,
    "has_text_content": check_has_text_content,
    "has_multiple_elements": check_has_multiple_elements,
    "returns_full_composition": check_returns_full_composition,
    "has_animation": check_has_animation,
    "has_nested_structure": check_has_nested_structure,
    "has_video_element": check_has_video_element,
    "has_multiple_tracks": check_has_multiple_tracks,
    "each_track_has_elements": check_each_track_has_elements
}

async def run_test(client: httpx.AsyncClient, scenario: Dict[str, Any]) -> Dict[str, Any]:
    """Run a single test scenario."""
    print(f"\n{'='*80}")
    print(f"TEST: {scenario['name']}")
    print(f"{'='*80}")
    
    result = {
        "name": scenario["name"],
        "success": False,
        "response": None,
        "checks": [],
        "error": None
    }
    
    try:
        # Make request
        print(f"📤 Sending request...")
        response = await client.post(
            GENERATE_ENDPOINT,
            json=scenario["request"],
            timeout=60.0  # 60 second timeout for AI generation
        )
        
        if response.status_code != 200:
            result["error"] = f"HTTP {response.status_code}: {response.text}"
            print(f"❌ Request failed: {result['error']}")
            return result
        
        response_data = response.json()
        result["response"] = response_data
        
        # Check if generation was successful
        if not response_data.get("success", False):
            result["error"] = response_data.get("error_message", "Generation failed")
            print(f"❌ Generation failed: {result['error']}")
            return result
        
        print(f"✅ Response received")
        print(f"📝 Explanation: {response_data.get('explanation', 'N/A')[:100]}...")
        
        # Run validation checks
        print(f"\n🔍 Running validation checks:")
        all_checks_passed = True
        
        for check_name, check_description in scenario["checks"]:
            check_fn = CHECK_FUNCTIONS.get(check_name)
            if not check_fn:
                print(f"⚠️  Unknown check: {check_name}")
                continue
            
            passed = check_fn(response_data)
            result["checks"].append({
                "name": check_name,
                "description": check_description,
                "passed": passed
            })
            
            status = "✅" if passed else "❌"
            print(f"  {status} {check_description}")
            
            if not passed:
                all_checks_passed = False
        
        result["success"] = all_checks_passed
        
        if all_checks_passed:
            print(f"\n🎉 All checks passed!")
        else:
            print(f"\n⚠️  Some checks failed")
            
    except Exception as e:
        result["error"] = str(e)
        print(f"❌ Exception: {e}")
    
    return result

async def main():
    """Run all test scenarios."""
    print(f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                COMPOSITION GENERATION TEST SUITE                             ║
║                                                                              ║
║  Testing implicit root system and composition editing functionality         ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")
    
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Total scenarios: {len(TEST_SCENARIOS)}")
    
    # Check if backend is running
    async with httpx.AsyncClient() as client:
        try:
            # Try to access root endpoint as health check
            health_response = await client.get(f"{BACKEND_URL}/", timeout=5.0)
            print(f"✅ Backend is running\n")
        except Exception as e:
            print(f"\n❌ Cannot connect to backend at {BACKEND_URL}")
            print(f"   Error: {e}")
            print(f"\n💡 Please start the backend with: cd backend && uv run python main.py")
            return
    
    # Run all tests
    results = []
    async with httpx.AsyncClient() as client:
        for scenario in TEST_SCENARIOS:
            result = await run_test(client, scenario)
            results.append(result)
            
            # Small delay between tests
            await asyncio.sleep(2)
    
    # Summary
    print(f"\n\n{'='*80}")
    print(f"TEST SUMMARY")
    print(f"{'='*80}\n")
    
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r["success"])
    failed_tests = total_tests - passed_tests
    
    print(f"Total tests: {total_tests}")
    print(f"Passed: {passed_tests} ✅")
    print(f"Failed: {failed_tests} ❌")
    print(f"Success rate: {(passed_tests/total_tests*100):.1f}%\n")
    
    # Detailed results
    for result in results:
        status = "✅ PASS" if result["success"] else "❌ FAIL"
        print(f"{status} - {result['name']}")
        
        if not result["success"]:
            if result["error"]:
                print(f"        Error: {result['error']}")
            
            # Show failed checks
            failed_checks = [c for c in result["checks"] if not c["passed"]]
            for check in failed_checks:
                print(f"        ❌ {check['description']}")
    
    print(f"\n{'='*80}\n")
    
    # Final verdict
    if failed_tests == 0:
        print(f"🎉 ALL TESTS PASSED! The implicit root system is working correctly.")
        print(f"✅ Safe to merge with parent branch.")
    else:
        print(f"⚠️  {failed_tests} test(s) failed. Please review the issues before merging.")
        print(f"❌ NOT safe to merge yet.")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
