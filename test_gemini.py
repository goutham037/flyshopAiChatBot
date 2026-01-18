"""
Test script for Gemini 2.5-flash direct API connection.
"""
import asyncio
import google.generativeai as genai
from app.config import get_settings

settings = get_settings()

print(f"Using API Key: {settings.GEMINI_API_KEY[:20]}...")

genai.configure(api_key=settings.GEMINI_API_KEY)

async def test_gemini():
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Test 1: Basic English
        print("\n--- Test 1: English ---")
        response = await model.generate_content_async("Hello! Can you help me with my travel booking?")
        print(f"Response: {response.text[:200]}...")
        
        # Test 2: Hindi
        print("\n--- Test 2: Hindi ---")
        response = await model.generate_content_async("नमस्ते! मेरी बुकिंग के बारे में बताओ")
        print(f"Response: {response.text[:200]}...")
        
        # Test 3: Hinglish
        print("\n--- Test 3: Hinglish ---")
        response = await model.generate_content_async("Meri booking ka status kya hai?")
        print(f"Response: {response.text[:200]}...")
        
        print("\n✅ All tests passed! Gemini 2.5-flash is working.")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_gemini())
