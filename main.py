#!/usr/bin/env python3
"""
Sumo News Digest - Main Entry Point

This is the main entry point for the Sumo News Digest application.
It can be run directly from the project root directory.
"""

import os
import sys

# Add the src directory to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

if __name__ == '__main__':
    from main import SumoNewsApp, show_help
    
    args = sys.argv[1:]
    app = SumoNewsApp()
    
    if '--test' in args:
        app.test_components()
    elif '--help' in args:
        show_help()
    else:
        app.run()