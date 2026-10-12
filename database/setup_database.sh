#!/bin/bash
# ============================================================================
# Database Setup Script
# Automated script to set up PostgreSQL database for Procurement Intelligence
# ============================================================================

set -e  # Exit on error

echo "============================================================================"
echo "Procurement Intelligence System - Database Setup"
echo "============================================================================"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if PostgreSQL is installed
echo -e "\n${YELLOW}Checking PostgreSQL installation...${NC}"
if command -v psql &> /dev/null; then
    echo -e "${GREEN}✓ PostgreSQL is installed${NC}"
    psql --version
else
    echo -e "${RED}✗ PostgreSQL is not installed${NC}"
    echo "Please install PostgreSQL first:"
    echo "  macOS:   brew install postgresql@14"
    echo "  Ubuntu:  sudo apt-get install postgresql postgresql-contrib"
    echo "  Windows: Download from https://www.postgresql.org/download/"
    exit 1
fi

# Check if .env file exists
echo -e "\n${YELLOW}Checking environment configuration...${NC}"
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠ .env file not found. Creating from template...${NC}"
    cp .env.example .env
    echo -e "${RED}✗ Please edit .env file with your database credentials${NC}"
    echo "  Then run this script again."
    exit 1
else
    echo -e "${GREEN}✓ .env file exists${NC}"
fi

# Load environment variables
source .env

# Validate required environment variables
echo -e "\n${YELLOW}Validating environment variables...${NC}"
if [ -z "$DB_USER" ] || [ -z "$DB_NAME" ]; then
    echo -e "${RED}✗ Missing required environment variables${NC}"
    echo "  Please set DB_USER and DB_NAME in .env"
    exit 1
fi
# DB_PASSWORD is optional (supports passwordless local authentication)
if [ -z "$DB_PASSWORD" ]; then
    echo -e "${YELLOW}⚠ DB_PASSWORD is empty - using passwordless authentication${NC}"
fi
echo -e "${GREEN}✓ Environment variables configured${NC}"

# Test database connection
echo -e "\n${YELLOW}Testing database connection...${NC}"
if PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d postgres -c "SELECT 1" &> /dev/null; then
    echo -e "${GREEN}✓ Database connection successful${NC}"
else
    echo -e "${RED}✗ Database connection failed${NC}"
    echo "  Please check your credentials in .env"
    exit 1
fi

# Create database if it doesn't exist
echo -e "\n${YELLOW}Creating database...${NC}"
if PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d postgres -lqt | cut -d \| -f 1 | grep -qw $DB_NAME; then
    echo -e "${YELLOW}⚠ Database '$DB_NAME' already exists${NC}"
else
    PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d postgres -c "CREATE DATABASE $DB_NAME;"
    echo -e "${GREEN}✓ Database '$DB_NAME' created${NC}"
fi

# Create schema
echo -e "\n${YELLOW}Creating database schema...${NC}"
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f database/schema.sql
echo -e "${GREEN}✓ Database schema created${NC}"

# Verify tables
echo -e "\n${YELLOW}Verifying tables...${NC}"
TABLE_COUNT=$(PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE';")
echo -e "${GREEN}✓ Created $TABLE_COUNT tables${NC}"

# Load data
echo -e "\n${YELLOW}Loading data into database...${NC}"
python -m database.load_data
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Data loaded successfully${NC}"
else
    echo -e "${RED}✗ Data loading failed${NC}"
    exit 1
fi

# Validate data
echo -e "\n${YELLOW}Validating loaded data...${NC}"
python -m database.validate_data
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Data validation passed${NC}"
else
    echo -e "${RED}✗ Data validation failed${NC}"
    exit 1
fi

echo -e "\n${GREEN}============================================================================${NC}"
echo -e "${GREEN}Database setup completed successfully!${NC}"
echo -e "${GREEN}============================================================================${NC}"
echo -e "\nYou can now connect to the database:"
echo -e "  psql -U $DB_USER -d $DB_NAME"
echo -e "\nOr query the data:"
echo -e "  SELECT COUNT(*) FROM purchase_orders;"
echo -e "  SELECT * FROM vw_supplier_performance;"
echo ""
