"""
Offline test to verify agent initialization and configuration
Does not make live API calls
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_agent_imports():
    """Test that agent modules can be imported"""
    print("Testing agent imports...")
    
    try:
        from agent.agent import ProcurementAgent
        print("✅ ProcurementAgent import successful")
    except Exception as e:
        print(f"❌ Failed to import ProcurementAgent: {e}")
        return False
    
    try:
        from agent.google_genai_adapter import GoogleGenAIChatModel
        print("✅ GoogleGenAIChatModel import successful")
    except Exception as e:
        print(f"❌ Failed to import GoogleGenAIChatModel: {e}")
        return False
    
    return True

def test_adapter_structure():
    """Test that adapter has required methods"""
    print("\nTesting adapter structure...")
    
    try:
        from agent.google_genai_adapter import GoogleGenAIChatModel
        
        # Check required methods exist
        required_methods = ['_generate', 'bind_tools', '_langchain_tool_to_python_function']
        for method in required_methods:
            if not hasattr(GoogleGenAIChatModel, method):
                print(f"❌ Missing method: {method}")
                return False
            print(f"✅ Method exists: {method}")
        
        return True
    except Exception as e:
        print(f"❌ Error checking adapter structure: {e}")
        return False

def test_config():
    """Test that configuration can be loaded"""
    print("\nTesting configuration...")
    
    try:
        from agent.config import config
        print(f"✅ Config loaded")
        print(f"   LLM Provider: {config.LLM_PROVIDER}")
        print(f"   LLM Model: {config.LLM_MODEL}")
        print(f"   API Key loaded: {bool(config.LLM_API_KEY)}")
        print(f"   Temperature: {config.LLM_TEMPERATURE}")
        print(f"   Max Tokens: {config.LLM_MAX_TOKENS}")
        return True
    except Exception as e:
        print(f"❌ Failed to load config: {e}")
        return False

def test_tools_available():
    """Test that tool modules are available"""
    print("\nTesting tool availability...")
    
    try:
        from agent.tools import database_tools, ml_tools, rag_tools
        print("✅ Database tools module loaded")
        print("✅ ML tools module loaded")
        print("✅ RAG tools module loaded")
        return True
    except Exception as e:
        print(f"❌ Failed to load tools: {e}")
        return False

def main():
    print("=" * 60)
    print("PROCUREMENT AGENT OFFLINE VERIFICATION")
    print("=" * 60)
    
    results = []
    
    results.append(("Imports", test_agent_imports()))
    results.append(("Adapter Structure", test_adapter_structure()))
    results.append(("Configuration", test_config()))
    results.append(("Tools", test_tools_available()))
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{name:20} {status}")
    
    all_passed = all(r[1] for r in results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ALL OFFLINE TESTS PASSED")
        print("Agent is properly configured for Gemini API integration")
    else:
        print("❌ SOME TESTS FAILED")
        print("Review errors above")
    print("=" * 60)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
