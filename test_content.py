#!/usr/bin/env python3
"""
Simple test script to validate content generation functions
"""

import sys
import os
from datetime import datetime

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def test_academic_content():
    """Test academic content generation"""
    try:
        # Import the function directly
        from app import generate_contextual_mock
        
        prompt = "Generate a comprehensive research paper on machine learning applications in climate change prediction"
        result = generate_contextual_mock(prompt, "gpt-4", 3)
        
        print("=== ACADEMIC CONTENT TEST ===")
        print(f"Prompt: {prompt}")
        print(f"Result length: {len(result)} characters")
        print(f"Contains 'Abstract': {'Abstract' in result}")
        print(f"Contains 'Literature Review': {'Literature Review' in result}")
        print(f"Contains 'Methodology': {'Methodology' in result}")
        print("First 200 characters:")
        print(result[:200])
        print("\n")
        
        return "Abstract" in result and "Literature Review" in result
        
    except Exception as e:
        print(f"Academic content test failed: {e}")
        return False

def test_presentation_content():
    """Test presentation content generation"""
    try:
        from app import generate_contextual_mock
        
        prompt = "Create a comprehensive Q4 product launch presentation for AI project management tool"
        result = generate_contextual_mock(prompt, "gpt-4", 3)
        
        print("=== PRESENTATION CONTENT TEST ===")
        print(f"Prompt: {prompt}")
        print(f"Result length: {len(result)} characters")
        print(f"Contains 'Slide': {'Slide' in result}")
        print(f"Contains 'Executive Summary': {'Executive Summary' in result}")
        print("First 200 characters:")
        print(result[:200])
        print("\n")
        
        return "Slide" in result and "Executive Summary" in result
        
    except Exception as e:
        print(f"Presentation content test failed: {e}")
        return False

def test_documentation_content():
    """Test documentation content generation"""
    try:
        from app import generate_contextual_mock
        
        prompt = "Create API integration guide for payment processing with code examples"
        result = generate_contextual_mock(prompt, "gpt-4", 3)
        
        print("=== DOCUMENTATION CONTENT TEST ===")
        print(f"Prompt: {prompt}")
        print(f"Result length: {len(result)} characters")
        print(f"Contains 'API': {'API' in result}")
        print(f"Contains code blocks: {'```' in result}")
        print("First 200 characters:")
        print(result[:200])
        print("\n")
        
        return "API" in result and "```" in result
        
    except Exception as e:
        print(f"Documentation content test failed: {e}")
        return False

def main():
    """Run all content generation tests"""
    print("🧪 CONTENT GENERATION TESTING")
    print("=" * 50)
    
    tests = [
        ("Academic Papers", test_academic_content),
        ("Presentations", test_presentation_content),
        ("Documentation", test_documentation_content)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n🔍 Testing {test_name}...")
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results[test_name] = False
    
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED!")
        return True
    else:
        print("⚠️  SOME TESTS FAILED - SYSTEM NOT READY")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
