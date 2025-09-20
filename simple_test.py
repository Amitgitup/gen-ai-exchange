#!/usr/bin/env python3
"""
Simple Test Script for Multi-Level Summarization System
This script helps test the system step by step
"""

import requests
import json
import time


def test_system():
    """Test the multi-level summarization system step by step"""
    
    print("🧪 Testing Multi-Level Summarization System")
    print("=" * 60)
    
    # Test endpoints
    endpoints = [
        ("http://localhost:8000", "Orchestrator"),
        ("http://localhost:8001", "Server 1 (L1 Summary)"),
        ("http://localhost:8002", "Server 2 (L2 Summary)"),
        ("http://localhost:8003", "Server 3 (L3 Summary)")
    ]
    
    print("\n🏥 Step 1: Health Checks")
    print("-" * 30)
    
    healthy_servers = []
    for url, name in endpoints:
        try:
            response = requests.get(f"{url}/health", timeout=5)
            if response.status_code == 200:
                print(f"✅ {name}: Healthy")
                healthy_servers.append((url, name))
            else:
                print(f"❌ {name}: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ {name}: {str(e)}")
    
    if not healthy_servers:
        print("\n❌ No servers are running. Please start the system first:")
        print("   python manage_system.py start")
        return
    
    print(f"\n✅ {len(healthy_servers)} servers are healthy")
    
    # Test ingestion on Server 1
    print("\n📚 Step 2: Document Ingestion")
    print("-" * 30)
    
    try:
        print("Triggering PDF ingestion on Server 1...")
        response = requests.post("http://localhost:8001/ingest", timeout=60)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Ingestion successful!")
            print(f"   - Chunks processed: {data.get('chunks', 'N/A')}")
            print(f"   - Vectors added: {data.get('vectors_added', 'N/A')}")
            print(f"   - Processing time: {data.get('processing_time', 'N/A'):.2f}s")
        else:
            print(f"❌ Ingestion failed: HTTP {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Ingestion error: {str(e)}")
    
    # Test L2 summarization
    print("\n📝 Step 3: L2 Summarization")
    print("-" * 30)
    
    try:
        print("Creating L2 summary from L1...")
        response = requests.post("http://localhost:8002/summarize_l1", timeout=60)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ L2 summarization successful!")
            print(f"   - L1 length: {data.get('l1_length', 'N/A')} chars")
            print(f"   - L2 length: {data.get('l2_length', 'N/A')} chars")
            print(f"   - Compression ratio: {data.get('compression_ratio', 'N/A'):.2f}")
        else:
            print(f"❌ L2 summarization failed: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ L2 summarization error: {str(e)}")
    
    # Test L3 summarization
    print("\n📄 Step 4: L3 Summarization")
    print("-" * 30)
    
    try:
        print("Creating L3 summary from L2...")
        response = requests.post("http://localhost:8003/summarize_l2", timeout=60)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ L3 summarization successful!")
            print(f"   - L2 length: {data.get('l2_length', 'N/A')} chars")
            print(f"   - L3 length: {data.get('l3_length', 'N/A')} chars")
            print(f"   - Compression ratio: {data.get('compression_ratio', 'N/A'):.2f}")
        else:
            print(f"❌ L3 summarization failed: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ L3 summarization error: {str(e)}")
    
    # Test intelligent query routing
    print("\n🧠 Step 5: Intelligent Query Routing")
    print("-" * 30)
    
    test_queries = [
        "What are the key points about Jharkhand policies?",
        "Give me a summary of the MSME promotion policy",
        "What are the specific requirements in the industrial policy?"
    ]
    
    for i, query in enumerate(test_queries, 1):
        try:
            print(f"\nQuery {i}: {query}")
            response = requests.post(
                "http://localhost:8000/query",
                json={"question": query},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                routing_info = data.get('routing_info', {})
                server = routing_info.get('primary_server', 'unknown')
                complexity = routing_info.get('complexity', 'unknown')
                
                print(f"✅ Routed to: {server} ({complexity})")
                
                # Show answer preview
                answer = data.get('answer', '')
                preview = answer[:150] + "..." if len(answer) > 150 else answer
                print(f"💬 Answer: {preview}")
                
                # Show citations
                citations = data.get('citations', [])
                print(f"📚 Citations: {len(citations)} sources")
            else:
                print(f"❌ Query failed: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ Query error: {str(e)}")
    
    print("\n🎉 Testing completed!")
    print("\n💡 System is ready for use!")


if __name__ == "__main__":
    test_system()
