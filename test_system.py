#!/usr/bin/env python3
"""
Quick Test Script for Multi-Level Summarization System
Run this to verify your system is working correctly
"""

import asyncio
import httpx
import json
import time


async def test_system():
    """Test the multi-level summarization system"""
    
    print("🧪 Testing Multi-Level Summarization System")
    print("=" * 50)
    
    # Test endpoints
    endpoints = [
        ("http://localhost:8000", "Orchestrator"),
        ("http://localhost:8001", "Server 1 (L1 Summary)"),
        ("http://localhost:8002", "Server 2 (L2 Summary)"),
        ("http://localhost:8003", "Server 3 (L3 Summary)")
    ]
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Test health endpoints
        print("\n🏥 Health Checks:")
        for url, name in endpoints:
            try:
                response = await client.get(f"{url}/health")
                if response.status_code == 200:
                    print(f"✅ {name}: Healthy")
                else:
                    print(f"❌ {name}: HTTP {response.status_code}")
            except Exception as e:
                print(f"❌ {name}: {str(e)}")
        
        # Test intelligent query routing
        print("\n🧠 Testing Intelligent Query Routing:")
        test_queries = [
            "What are the key points?",
            "Give me a summary of the policies",
            "What are the specific requirements?"
        ]
        
        for query in test_queries:
            try:
                response = await client.post(
                    "http://localhost:8000/query",
                    json={"question": query}
                )
                if response.status_code == 200:
                    data = response.json()
                    routing_info = data.get('routing_info', {})
                    server = routing_info.get('primary_server', 'unknown')
                    complexity = routing_info.get('complexity', 'unknown')
                    print(f"✅ Query: '{query}' → {server} ({complexity})")
                else:
                    print(f"❌ Query failed: HTTP {response.status_code}")
            except Exception as e:
                print(f"❌ Query error: {str(e)}")
    
    print("\n🎉 Test completed!")


if __name__ == "__main__":
    asyncio.run(test_system())
