#!/usr/bin/env python3
"""Development environment setup script."""

import os
import shutil
import stat
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent))

def setup_environment() -> None:
    """Set up the development environment."""
    print("🚀 Setting up development environment...")
    
    # Create .env file if it doesn't exist
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists() and env_example.exists():
        print("📄 Creating .env file from .env.example")
        shutil.copy(env_example, env_file)
        print("✅ Created .env file")
    
    # Create data directory if it doesn't exist
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    # Create models directory if it doesn't exist
    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)
    
    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Make scripts executable
    scripts_dir = Path("scripts")
    for script in scripts_dir.glob("*.py"):
        if script.name != "__init__.py":
            script.chmod(script.stat().st_mode | stat.S_IEXEC)
    
    print("✨ Development environment setup complete!")

if __name__ == "__main__":
    setup_environment()
