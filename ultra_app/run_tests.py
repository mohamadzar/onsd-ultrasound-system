#!/usr/bin/env python3
"""
Test runner for ULTRA Eye Scan application
"""
import sys
import subprocess
import argparse
import os


def run_unit_tests():
    """Run unit tests with coverage"""
    print("Running unit tests...")
    result = subprocess.run([
        sys.executable, '-m', 'pytest',
        '-p', 'pytest_cov',
        'ultra_app/tests/unit/',
        '-v', 
        '--cov=ultra_app',
        '--cov-report=term-missing',
        '--cov-report=html'
    ])
    return result.returncode


def run_integration_tests():
    """Run integration tests"""
    print("Running integration tests...")
    result = subprocess.run([
        sys.executable, '-m', 'pytest',
        '-p', 'pytest_cov',
        'ultra_app/tests/integration/',  # Fixed path
        '-v'
    ])
    return result.returncode


def run_all_tests():
    """Run all tests"""
    print("Running all tests...")
    result = subprocess.run([
        sys.executable, '-m', 'pytest',
        '-p', 'pytest_cov',
        'ultra_app/tests/',  # Fixed path
        '-v',
        '--cov=ultra_app',
        '--cov-report=term-missing',
        '--cov-report=html'
    ])
    return result.returncode


def main():
    parser = argparse.ArgumentParser(description='Run tests for ULTRA Eye Scan application')
    parser.add_argument('--unit', action='store_true', help='Run only unit tests')
    parser.add_argument('--integration', action='store_true', help='Run only integration tests')
    parser.add_argument('--all', action='store_true', help='Run all tests (default)')
    
    args = parser.parse_args()
    
    if args.unit:
        return run_unit_tests()
    elif args.integration:
        return run_integration_tests()
    else:
        return run_all_tests()


if __name__ == '__main__':
    sys.exit(main())