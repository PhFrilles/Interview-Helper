#!/usr/bin/env python
"""
Test Gemini API connection independently of Django
"""
import os
import sys
import requests
import google.generativeai as genai
from google import genai as new_genai

print("=" * 60)
print("GEMINI API TEST SCRIPT")
print("=" * 60)

# Your API key - REPLACE WITH YOURS!
API_KEY = "AIzaSyAHXYkFv4HP2Detzi6Yobc0W30_CyRXeEU"

# Option 1: Test with a NEW key (recommended)
NEW_API_KEY = input("Enter your API key (press Enter to use existing): ").strip()
if NEW_API_KEY:
    API_KEY = NEW_API_KEY

print(f"\n🔑 Using API Key: {API_KEY[:15]}...")

def test_rest_api():
    """Test REST API directly"""
    print("\n1. 🔗 Testing REST API...")
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={API_KEY}"
    
    try:
        response = requests.get(url, timeout=10)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            models = data.get('models', [])
            print(f"   ✅ SUCCESS! Found {len(models)} models")
            print(f"   📋 First 3 models:")
            for i, model in enumerate(models[:3], 1):
                print(f"      {i}. {model['name']}")
                print(f"         Methods: {model.get('supportedGenerationMethods', [])}")
            return True
        else:
            print(f"   ❌ FAILED: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_old_package():
    """Test old google-generativeai package"""
    print("\n2. 📦 Testing 'google-generativeai' package...")
    try:
        genai.configure(api_key=API_KEY)
        models = genai.list_models()
        model_list = list(models)
        print(f"   ✅ SUCCESS! Found {len(model_list)} models")
        print(f"   📋 First 3 models:")
        for i, model in enumerate(model_list[:3], 1):
            print(f"      {i}. {model.name}")
            print(f"         Methods: {model.supported_generation_methods}")
        
        # Test generating content
        print("\n   🧪 Testing content generation...")
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content("Say 'Hello World' in 2 words")
        print(f"   ✅ Generation works: {response.text}")
        return True
    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        return False

def test_new_package():
    """Test new google.genai package"""
    print("\n3. 🆕 Testing 'google.genai' package...")
    try:
        client = new_genai.Client(api_key=API_KEY)
        models = client.models.list()
        model_list = list(models)
        print(f"   ✅ SUCCESS! Found {len(model_list)} models")
        print(f"   📋 First 3 models:")
        for i, model in enumerate(model_list[:3], 1):
            print(f"      {i}. {model.name}")
            print(f"         Methods: {getattr(model, 'supported_generation_methods', 'N/A')}")
        return True
    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        return False

def check_api_enabled():
    """Check if API is enabled in Google Cloud"""
    print("\n4. ☁️  Checking Google Cloud Console status...")
    print("   🔗 Please check manually:")
    print("     1. Go to: https://console.cloud.google.com/apis/dashboard")
    print("     2. Make sure 'Generative Language API' is ENABLED")
    print("     3. Check billing is set up")
    print("     4. Ensure you're in the correct project")

def get_new_api_key():
    """Instructions to get new API key"""
    print("\n5. 🔑 Getting a new API key:")
    print("   Steps:")
    print("     1. Go to: https://makersuite.google.com/app/apikey")
    print("     2. Click 'Create API key'")
    print("     3. Select 'Create API key in new project'")
    print("     4. Copy the key and paste it above")

# Run tests
print("\n" + "=" * 60)
print("RUNNING TESTS...")
print("=" * 60)

rest_success = test_rest_api()
old_success = test_old_package()
new_success = test_new_package()

print("\n" + "=" * 60)
print("TEST RESULTS")
print("=" * 60)

if rest_success:
    print("✅ REST API: Working!")
else:
    print("❌ REST API: Failed")
    check_api_enabled()
    get_new_api_key()

if old_success:
    print("✅ Old package: Working!")
else:
    print("❌ Old package: Failed")

if new_success:
    print("✅ New package: Working!")
else:
    print("❌ New package: Failed")

print("\n" + "=" * 60)
print("NEXT STEPS")
print("=" * 60)

if not (rest_success or old_success or new_success):
    print("🚨 All tests failed! Your API key is invalid or API not enabled.")
    print("\nDO THIS NOW:")
    print("1. Get NEW API key: https://makersuite.google.com/app/apikey")
    print("2. Create NEW project when prompted")
    print("3. Enable billing if asked (free tier available)")
    print("4. Run this test again with the NEW key")
else:
    print("🎉 Some tests passed! You can use the working method.")
    if old_success:
        print("\n   Use 'google-generativeai' package in your Django app")
    elif new_success:
        print("\n   Use 'google.genai' package in your Django app")