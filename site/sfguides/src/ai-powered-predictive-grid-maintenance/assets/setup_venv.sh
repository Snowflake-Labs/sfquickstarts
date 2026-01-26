#!/bin/bash
# Copyright 2026 Snowflake Inc.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


##############################################################################
# Virtual Environment Setup Script
##############################################################################
# This script creates a Python virtual environment and installs dependencies
# Run this before deploying to avoid package conflicts
##############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║      Python Virtual Environment Setup                         ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 is not installed${NC}"
    echo -e "${YELLOW}Please install Python 3.11 or higher${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo -e "${GREEN}✓ Found Python ${PYTHON_VERSION}${NC}"
echo ""

# Check if venv already exists
if [ -d "venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment 'venv' already exists${NC}"
    read -p "Do you want to recreate it? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Removing existing venv...${NC}"
        rm -rf venv
    else
        echo -e "${YELLOW}Using existing venv${NC}"
        echo ""
        echo -e "${GREEN}To activate the virtual environment, run:${NC}"
        echo -e "${YELLOW}  source venv/bin/activate${NC}"
        echo ""
        echo -e "${GREEN}Then install/update dependencies with:${NC}"
        echo -e "${YELLOW}  pip install -r requirements.txt${NC}"
        exit 0
    fi
fi

# Create virtual environment
echo -e "${YELLOW}▶ Creating virtual environment...${NC}"
python3 -m venv venv

if [ $? -eq 0 ]; then
    echo -e "${GREEN}  ✓ Virtual environment created${NC}"
else
    echo -e "${RED}  ✗ Failed to create virtual environment${NC}"
    exit 1
fi
echo ""

# Activate virtual environment
echo -e "${YELLOW}▶ Activating virtual environment...${NC}"
source venv/bin/activate

if [ $? -eq 0 ]; then
    echo -e "${GREEN}  ✓ Virtual environment activated${NC}"
else
    echo -e "${RED}  ✗ Failed to activate virtual environment${NC}"
    exit 1
fi
echo ""

# Upgrade pip
echo -e "${YELLOW}▶ Upgrading pip...${NC}"
pip install --upgrade pip > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}  ✓ pip upgraded to $(pip --version | cut -d' ' -f2)${NC}"
else
    echo -e "${YELLOW}  ⚠ Warning: Failed to upgrade pip${NC}"
fi
echo ""

# Install dependencies
if [ -f "requirements.txt" ]; then
    echo -e "${YELLOW}▶ Installing dependencies from requirements.txt...${NC}"
    pip install -r requirements.txt
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}  ✓ Dependencies installed successfully${NC}"
    else
        echo -e "${RED}  ✗ Failed to install dependencies${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠️  requirements.txt not found${NC}"
    echo -e "${YELLOW}Skipping dependency installation${NC}"
fi
echo ""

# Display success message
echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✓ Virtual Environment Setup Complete!                        ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}To activate the virtual environment in future sessions:${NC}"
echo -e "${YELLOW}  source venv/bin/activate${NC}"
echo ""
echo -e "${BLUE}To deactivate when done:${NC}"
echo -e "${YELLOW}  deactivate${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo -e "${YELLOW}  1. Configure Snowflake connection: snow connection add default${NC}"
echo -e "${YELLOW}  2. Run deployment: ./deploy.sh${NC}"
echo ""
