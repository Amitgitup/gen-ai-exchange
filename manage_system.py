#!/usr/bin/env python3
"""
Multi-Level Summarization System Manager

This script provides comprehensive management capabilities for the hierarchical
summarization system including startup, monitoring, and maintenance.

# Check system status
python manage_system.py status

# Monitor system health
python manage_system.py monitor

# Stop all servers
python manage_system.py stop

# Restart system
python manage_system.py restart

# Test the system
python test_system.py
"""

import asyncio
import json
import logging
import os
import signal
import subprocess
import sys
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

import httpx
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ServerConfig:
    """Configuration for a summarization server"""
    name: str
    port: int
    script_path: str
    description: str
    dependencies: List[str] = None


class SystemManager:
    """Manages the multi-server summarization system"""
    
    def __init__(self):
        # Load environment variables from .env file
        backend_dir = os.path.join(os.path.dirname(__file__), "backend")
        env_path = os.path.join(backend_dir, ".env")
        if os.path.exists(env_path):
            load_dotenv(env_path)
            logger.info(f"Loaded environment variables from {env_path}")
        else:
            logger.warning(f"No .env file found at {env_path}")
        
        self.servers = {
            "server1": ServerConfig(
                name="server1",
                port=8001,
                script_path="backend/servers/server1.py",
                description="Ingestion + L1 Summary",
                dependencies=[]
            ),
            "server2": ServerConfig(
                name="server2", 
                port=8002,
                script_path="backend/servers/server2.py",
                description="L2 Summary",
                dependencies=["server1"]
            ),
            "server3": ServerConfig(
                name="server3",
                port=8003,
                script_path="backend/servers/server3.py", 
                description="L3 Ultra-Summary",
                dependencies=["server2"]
            ),
            "orchestrator": ServerConfig(
                name="orchestrator",
                port=8000,
                script_path="backend/orchestrator.py",
                description="Intelligent Query Router",
                dependencies=["server1", "server2", "server3"]
            )
        }
        
        self.processes: Dict[str, subprocess.Popen] = {}
        self.running = False
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.stop_all_servers()
        sys.exit(0)
    
    def check_dependencies(self) -> bool:
        """Check if all required dependencies are available"""
        logger.info("Checking system dependencies...")
        
        # Check Python packages
        required_packages = [
            ("fastapi", "fastapi"),
            ("uvicorn", "uvicorn"), 
            ("httpx", "httpx"),
            ("pydantic", "pydantic"),
            ("google-generativeai", "google.generativeai"),
            ("faiss-cpu", "faiss"),
            ("pypdf", "pypdf"),
            ("numpy", "numpy")
        ]
        
        missing_packages = []
        for package_name, import_name in required_packages:
            try:
                __import__(import_name)
            except ImportError:
                missing_packages.append(package_name)
        
        if missing_packages:
            logger.error(f"Missing required packages: {missing_packages}")
            logger.error("Please install them with: pip install " + " ".join(missing_packages))
            return False
        
        # Check API key
        if not os.getenv("GOOGLE_API_KEY"):
            logger.error("GOOGLE_API_KEY environment variable not set")
            return False
        
        # Check directories
        required_dirs = ["backend/pdfs/raw", "backend/pdfs/summaries"]
        for dir_path in required_dirs:
            if not os.path.exists(dir_path):
                logger.warning(f"Directory {dir_path} does not exist, creating...")
                os.makedirs(dir_path, exist_ok=True)
        
        logger.info("All dependencies satisfied")
        return True
    
    def start_server(self, server_name: str) -> bool:
        """Start a specific server"""
        if server_name not in self.servers:
            logger.error(f"Unknown server: {server_name}")
            return False
        
        if server_name in self.processes:
            logger.warning(f"Server {server_name} is already running")
            return True
        
        config = self.servers[server_name]
        
        # Check dependencies
        for dep in config.dependencies:
            if dep not in self.processes:
                logger.error(f"Cannot start {server_name}: dependency {dep} is not running")
                return False
        
        try:
            logger.info(f"Starting {server_name} on port {config.port}...")
            
            # Start the server process
            process = subprocess.Popen([
                sys.executable, "-m", "uvicorn", 
                config.script_path.replace(".py", "").replace("/", ".") + ":app",
                "--host", "0.0.0.0",
                "--port", str(config.port),
                "--log-level", "info"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            self.processes[server_name] = process
            
            # Wait a moment and check if it started successfully
            time.sleep(2)
            if process.poll() is not None:
                stdout, stderr = process.communicate()
                logger.error(f"Server {server_name} failed to start:")
                logger.error(f"STDOUT: {stdout.decode()}")
                logger.error(f"STDERR: {stderr.decode()}")
                return False
            
            logger.info(f"Server {server_name} started successfully on port {config.port}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start {server_name}: {e}")
            return False
    
    def stop_server(self, server_name: str) -> bool:
        """Stop a specific server"""
        if server_name not in self.processes:
            logger.warning(f"Server {server_name} is not running")
            return True
        
        try:
            logger.info(f"Stopping {server_name}...")
            process = self.processes[server_name]
            process.terminate()
            
            # Wait for graceful shutdown
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                logger.warning(f"Server {server_name} did not stop gracefully, forcing...")
                process.kill()
                process.wait()
            
            del self.processes[server_name]
            logger.info(f"Server {server_name} stopped")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop {server_name}: {e}")
            return False
    
    def start_all_servers(self) -> bool:
        """Start all servers in dependency order"""
        logger.info("Starting all servers...")
        
        if not self.check_dependencies():
            return False
        
        # Start servers in dependency order
        started = []
        failed = []
        
        for server_name in ["server1", "server2", "server3", "orchestrator"]:
            if self.start_server(server_name):
                started.append(server_name)
                # Wait a bit between server starts
                time.sleep(3)
            else:
                failed.append(server_name)
                # Stop dependent servers if this one failed
                break
        
        if failed:
            logger.error(f"Failed to start servers: {failed}")
            logger.info("Stopping started servers...")
            for server_name in reversed(started):
                self.stop_server(server_name)
            return False
        
        self.running = True
        logger.info("All servers started successfully!")
        logger.info("System is ready for queries")
        return True
    
    def stop_all_servers(self):
        """Stop all running servers"""
        logger.info("Stopping all servers...")
        
        # Stop in reverse order
        for server_name in reversed(list(self.processes.keys())):
            self.stop_server(server_name)
        
        self.running = False
        logger.info("All servers stopped")
    
    async def check_server_health(self, server_name: str) -> Dict:
        """Check health of a specific server"""
        if server_name not in self.servers:
            return {"error": f"Unknown server: {server_name}"}
        
        config = self.servers[server_name]
        url = f"http://localhost:{config.port}"
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{url}/health")
                if response.status_code == 200:
                    return response.json()
                else:
                    return {"error": f"HTTP {response.status_code}: {response.text}"}
        except Exception as e:
            return {"error": str(e)}
    
    async def get_system_status(self) -> Dict:
        """Get comprehensive system status"""
        status = {
            "timestamp": time.time(),
            "servers": {},
            "overall_health": "unknown"
        }
        
        healthy_count = 0
        total_count = len(self.servers)
        
        for server_name in self.servers:
            config = self.servers[server_name]
            server_status = {
                "name": server_name,
                "port": config.port,
                "description": config.description,
                "running": server_name in self.processes,
                "health": await self.check_server_health(server_name)
            }
            
            if server_status["running"] and "error" not in server_status["health"]:
                healthy_count += 1
            
            status["servers"][server_name] = server_status
        
        # Determine overall health
        if healthy_count == total_count:
            status["overall_health"] = "healthy"
        elif healthy_count > 0:
            status["overall_health"] = "degraded"
        else:
            status["overall_health"] = "unhealthy"
        
        status["healthy_count"] = healthy_count
        status["total_count"] = total_count
        
        return status
    
    def run_monitoring_loop(self):
        """Run continuous monitoring of the system"""
        logger.info("Starting system monitoring...")
        
        try:
            while self.running:
                # Check system status
                status = asyncio.run(self.get_system_status())
                
                # Log status
                logger.info(f"System health: {status['overall_health']} "
                          f"({status['healthy_count']}/{status['total_count']} servers)")
                
                # Check for crashed servers
                for server_name, server_status in status["servers"].items():
                    if server_status["running"] and "error" in server_status["health"]:
                        logger.warning(f"Server {server_name} appears unhealthy: "
                                    f"{server_status['health']['error']}")
                
                # Wait before next check
                time.sleep(30)
                
        except KeyboardInterrupt:
            logger.info("Monitoring stopped by user")
        except Exception as e:
            logger.error(f"Monitoring error: {e}")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Multi-Level Summarization System Manager")
    parser.add_argument("command", choices=["start", "stop", "status", "monitor", "restart"],
                       help="Command to execute")
    parser.add_argument("--server", help="Specific server to operate on")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    manager = SystemManager()
    
    if args.command == "start":
        if args.server:
            success = manager.start_server(args.server)
        else:
            success = manager.start_all_servers()
        
        if success and not args.server:
            # Start monitoring if all servers started
            manager.run_monitoring_loop()
        sys.exit(0 if success else 1)
    
    elif args.command == "stop":
        if args.server:
            success = manager.stop_server(args.server)
        else:
            manager.stop_all_servers()
            success = True
        sys.exit(0 if success else 1)
    
    elif args.command == "status":
        status = asyncio.run(manager.get_system_status())
        print(json.dumps(status, indent=2))
        sys.exit(0)
    
    elif args.command == "monitor":
        if not manager.running:
            logger.error("No servers are running. Start them first with 'start' command.")
            sys.exit(1)
        manager.run_monitoring_loop()
    
    elif args.command == "restart":
        manager.stop_all_servers()
        time.sleep(2)
        success = manager.start_all_servers()
        if success:
            manager.run_monitoring_loop()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
