#!/usr/bin/env python3
"""
Test LLM7.io Integration
Verify that the LLM7Client integrates correctly with the system
"""

from llm7_client import LLM7Client
from llm_analyzer import CryptoMarketAnalyzer

def test_llm7_client_initialization():
    """Test that LLM7Client can be initialized"""
    print("Testing LLM7Client initialization...")
    client = LLM7Client('test_token')
    assert client is not None
    assert client.api_token == 'test_token'
    assert client.base_url == 'https://llm7.io/v1/chat/completions'
    print("✅ LLM7Client initialization successful")

def test_analyzer_with_llm7():
    """Test that CryptoMarketAnalyzer works with LLM7Client"""
    print("\nTesting CryptoMarketAnalyzer with LLM7Client...")
    client = LLM7Client('test_token')
    analyzer = CryptoMarketAnalyzer(client)
    
    assert analyzer.llm_client is not None
    assert isinstance(analyzer.llm_client, LLM7Client)
    print("✅ CryptoMarketAnalyzer integration successful")

def test_chat_method_signature():
    """Test that the chat method has the correct signature"""
    print("\nTesting chat method signature...")
    client = LLM7Client('test_token')
    
    # Test that the method exists and accepts the right parameters
    import inspect
    sig = inspect.signature(client.chat)
    params = list(sig.parameters.keys())
    
    assert 'model_name' in params
    assert 'prompt' in params
    assert 'temperature' in params
    assert 'num_predict' in params
    print("✅ Chat method signature is correct")

def test_header_construction():
    """Test that headers are constructed correctly"""
    print("\nTesting header construction...")
    client = LLM7Client('my_secret_token')
    
    assert 'Authorization' in client.headers
    assert client.headers['Authorization'] == 'Bearer my_secret_token'
    assert client.headers['Content-Type'] == 'application/json'
    print("✅ Headers constructed correctly")

if __name__ == '__main__':
    print("=" * 70)
    print("LLM7.IO INTEGRATION TESTS")
    print("=" * 70)
    print()
    
    try:
        test_llm7_client_initialization()
        test_analyzer_with_llm7()
        test_chat_method_signature()
        test_header_construction()
        
        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED")
        print("=" * 70)
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
