"""
PE Agentic System - Quick Test Script

Verifies core functionality across all platforms.
Run this after installation to ensure everything works.
"""

import sys
import os
from decimal import Decimal


def test_imports():
    """Test that all required packages are installed"""
    print("Testing imports...")
    
    try:
        import pandas as pd
        import numpy as np
        print("✅ pandas, numpy")
    except ImportError as e:
        print(f"❌ pandas/numpy: {e}")
        return False
    
    try:
        import snowflake.connector
        from snowflake.snowpark import Session
        print("✅ snowflake")
    except ImportError as e:
        print(f"⚠️  snowflake (optional): {e}")
    
    try:
        import openai
        print("✅ openai")
    except ImportError as e:
        print(f"⚠️  openai (optional): {e}")
    
    try:
        import boto3
        print("✅ boto3 (Bedrock)")
    except ImportError as e:
        print(f"⚠️  boto3 (optional): {e}")
    
    return True


def test_decimal_precision():
    """Test that Decimal works correctly for financial calculations"""
    print("\nTesting financial precision...")
    
    # This would fail with floats
    a = Decimal('0.1')
    b = Decimal('0.2')
    c = a + b
    
    assert c == Decimal('0.3'), "Decimal precision test failed"
    print("✅ Decimal precision working correctly")
    
    # Float comparison (wrong)
    float_sum = 0.1 + 0.2
    if float_sum != 0.3:
        print("✅ Confirmed: floats are imprecise (this is expected)")
        print(f"   0.1 + 0.2 = {float_sum} (should be 0.3)")
    
    return True


def test_dcf_calculation():
    """Test basic DCF calculation"""
    print("\nTesting DCF calculation...")
    
    # Simple DCF
    fcf = Decimal('10000000')  # $10M
    wacc = Decimal('0.12')
    years = 5
    
    pv_fcf = Decimal('0')
    for year in range(1, years + 1):
        discount_factor = (Decimal('1') + wacc) ** year
        pv_fcf += fcf / discount_factor
    
    expected = Decimal('36047762.34')  # Pre-calculated
    
    # Allow small rounding difference
    diff = abs(pv_fcf - expected)
    assert diff < Decimal('1'), f"DCF test failed: {pv_fcf} vs {expected}"
    
    print(f"✅ DCF calculation: PV of $10M FCF over 5y @ 12% WACC = ${pv_fcf:,.2f}")
    return True


def test_client_initialization():
    """Test that clients can be imported"""
    print("\nTesting client initialization...")
    
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'integrations/python'))
        from openai_compatible_client import PEAgentClient, Provider, PEAgentConfig
        print("✅ Client classes imported successfully")
        
        # Test config creation
        config = PEAgentConfig(
            provider=Provider.OPENAI,
            default_model="gpt-4"
        )
        assert config.provider == Provider.OPENAI
        print("✅ Config creation working")
        
        return True
        
    except Exception as e:
        print(f"❌ Client test failed: {e}")
        return False


def test_cortex_client():
    """Test Cortex client (if Snowflake is available)"""
    print("\nTesting Cortex client...")
    
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'integrations/cortex'))
        from cortex_client import CortexRESTClient, CortexConfig, AuthMode
        
        # Test config creation (don't actually connect)
        config = CortexConfig(
            account="test_account",
            host="test.snowflakecomputing.com",
            token="test_token",
            auth_mode=AuthMode.SESSION
        )
        
        assert config.account == "test_account"
        print("✅ Cortex client classes loaded")
        
        return True
        
    except ImportError as e:
        print(f"⚠️  Cortex client (requires Snowflake): {e}")
        return True  # Not a failure
    except Exception as e:
        print(f"❌ Cortex client test failed: {e}")
        return False


def test_model_recommendations():
    """Test that model recommendations are accessible"""
    print("\nTesting model recommendations...")
    
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'integrations/python'))
        from openai_compatible_client import PEAgentClient, Provider
        
        # Renamed to _LEGACY_MODEL_RECOMMENDATIONS when config/models.yaml became
        # the source of truth for routing. This test referenced the old name and
        # raised AttributeError, which the broad `except` below silently reported
        # as a test failure rather than a bug in the test.
        recs = PEAgentClient._LEGACY_MODEL_RECOMMENDATIONS
        
        assert Provider.OPENAI in recs
        assert Provider.CORTEX in recs
        assert "reasoning" in recs[Provider.OPENAI]
        
        print("✅ Model recommendations accessible")
        print(f"   OpenAI reasoning model: {recs[Provider.OPENAI]['reasoning']}")
        print(f"   Cortex reasoning model: {recs[Provider.CORTEX]['reasoning']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Model recommendations test failed: {e}")
        return False


def run_all_tests():
    """Run all tests"""
    print("="*60)
    print("PE Agentic System - Test Suite")
    print("="*60)
    
    tests = [
        ("Imports", test_imports),
        ("Decimal Precision", test_decimal_precision),
        ("DCF Calculation", test_dcf_calculation),
        ("Client Initialization", test_client_initialization),
        ("Cortex Client", test_cortex_client),
        ("Model Recommendations", test_model_recommendations),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name} crashed: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print("="*60)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! System is ready to use.")
        print("\nNext steps:")
        print("1. Review QUICKSTART.md for usage examples")
        print("2. Check examples/complete_deal_workflow.ipynb")
        print("3. Configure your platform (Snowflake/OpenAI/Bedrock)")
    else:
        print("\n⚠️  Some tests failed. Check errors above.")
        print("   Most failures are due to optional dependencies.")
        print("   Core functionality should still work.")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
