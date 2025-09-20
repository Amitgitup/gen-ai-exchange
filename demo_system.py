#!/usr/bin/env python3
"""
Multi-Level Summarization System Demo

This script demonstrates the capabilities of the enhanced hierarchical
summarization system with intelligent query routing.
"""

import asyncio
import json
import time
from typing import Dict, List

import httpx


class SystemDemo:
    """Demonstrates the multi-level summarization system"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.timeout = httpx.Timeout(30.0)
    
    async def check_system_health(self) -> bool:
        """Check if the system is running and healthy"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/health")
                if response.status_code == 200:
                    health_data = response.json()
                    print(f"✅ System Health: {health_data['status']}")
                    return True
                else:
                    print(f"❌ System Health Check Failed: {response.status_code}")
                    return False
        except Exception as e:
            print(f"❌ System Not Available: {e}")
            return False
    
    async def get_system_stats(self) -> Dict:
        """Get comprehensive system statistics"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/stats")
                if response.status_code == 200:
                    return response.json()
                else:
                    return {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}
    
    async def query_system(self, question: str, server: str = None) -> Dict:
        """Query the system with intelligent routing"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                if server:
                    # Direct query to specific server
                    url = f"{self.base_url}/query/{server}"
                else:
                    # Intelligent routing
                    url = f"{self.base_url}/query"
                
                response = await client.post(
                    url,
                    json={"question": question}
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    return {"error": f"HTTP {response.status_code}: {response.text}"}
        except Exception as e:
            return {"error": str(e)}
    
    async def demonstrate_query_routing(self):
        """Demonstrate intelligent query routing"""
        print("\n🧠 Intelligent Query Routing Demo")
        print("=" * 50)
        
        # Test queries of different complexities
        test_queries = [
            {
                "question": "What are the key points about Jharkhand policies?",
                "expected_server": "server3",
                "description": "Simple query - should route to ultra-compressed summary"
            },
            {
                "question": "Give me a summary of the MSME promotion policy",
                "expected_server": "server2", 
                "description": "Moderate query - should route to moderate summary"
            },
            {
                "question": "What are the specific requirements in section 4.2 of the industrial policy?",
                "expected_server": "server1",
                "description": "Detailed query - should route to full document"
            },
            {
                "question": "Provide a comprehensive analysis of all Jharkhand policies",
                "expected_server": "server1",
                "description": "Comprehensive query - should route to full document"
            }
        ]
        
        for i, test in enumerate(test_queries, 1):
            print(f"\n📝 Test {i}: {test['description']}")
            print(f"Question: {test['question']}")
            
            # Query with intelligent routing
            result = await self.query_system(test['question'])
            
            if 'error' in result:
                print(f"❌ Error: {result['error']}")
            else:
                # Extract routing information
                routing_info = result.get('routing_info', {})
                actual_server = routing_info.get('primary_server', 'unknown')
                complexity = routing_info.get('complexity', 'unknown')
                confidence = routing_info.get('confidence', 0)
                fallback_used = routing_info.get('fallback_used', False)
                
                print(f"🎯 Routed to: {actual_server}")
                print(f"📊 Complexity: {complexity} (confidence: {confidence:.2f})")
                if fallback_used:
                    print(f"🔄 Fallback used: {routing_info.get('fallback_server', 'unknown')}")
                
                # Show answer preview
                answer = result.get('answer', '')
                preview = answer[:200] + "..." if len(answer) > 200 else answer
                print(f"💬 Answer Preview: {preview}")
                
                # Show citations
                citations = result.get('citations', [])
                print(f"📚 Citations: {len(citations)} sources")
    
    async def demonstrate_server_comparison(self):
        """Demonstrate differences between server levels"""
        print("\n🔍 Server Level Comparison Demo")
        print("=" * 50)
        
        question = "What are the main policies in Jharkhand?"
        
        print(f"Question: {question}")
        print("\nComparing responses from different server levels:")
        
        servers = ["server1", "server2", "server3"]
        
        for server in servers:
            print(f"\n📡 Querying {server}...")
            result = await self.query_system(question, server)
            
            if 'error' in result:
                print(f"❌ Error: {result['error']}")
            else:
                answer = result.get('answer', '')
                citations = result.get('citations', [])
                
                print(f"📝 Answer Length: {len(answer)} characters")
                print(f"📚 Citations: {len(citations)} sources")
                
                # Show answer preview
                preview = answer[:150] + "..." if len(answer) > 150 else answer
                print(f"💬 Preview: {preview}")
    
    async def demonstrate_system_capabilities(self):
        """Demonstrate overall system capabilities"""
        print("\n🚀 System Capabilities Demo")
        print("=" * 50)
        
        # Check system health
        if not await self.check_system_health():
            print("❌ System is not healthy. Please start the system first.")
            return
        
        # Get system statistics
        print("\n📊 System Statistics:")
        stats = await self.get_system_stats()
        if 'error' not in stats:
            print(json.dumps(stats, indent=2))
        else:
            print(f"❌ Error getting stats: {stats['error']}")
        
        # Demonstrate query routing
        await self.demonstrate_query_routing()
        
        # Demonstrate server comparison
        await self.demonstrate_server_comparison()
        
        print("\n✅ Demo completed successfully!")
        print("\n💡 Key Features Demonstrated:")
        print("   • Intelligent query routing based on complexity")
        print("   • Automatic fallback when servers fail")
        print("   • Multi-level summarization with different compression ratios")
        print("   • Comprehensive error handling and logging")
        print("   • Health monitoring and system statistics")


async def main():
    """Main demo function"""
    print("🎯 Multi-Level Summarization System Demo")
    print("=" * 60)
    
    demo = SystemDemo()
    
    try:
        await demo.demonstrate_system_capabilities()
    except KeyboardInterrupt:
        print("\n\n⏹️ Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
