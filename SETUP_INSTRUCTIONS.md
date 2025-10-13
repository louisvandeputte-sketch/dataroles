# Phase 1 Setup Instructions

## ✅ Completed

The following has been created:

1. **Project Structure** - All directories and files
2. **Database Schema** - Complete SQL schema in `database/schema.sql`
3. **Configuration** - Settings management with Pydantic
4. **Dependencies** - All required packages in `requirements.txt`

## 🚀 Next Steps

### Step 1: Create Virtual Environment

```bash
cd /Users/louisvandeputte/datarole
python3 -m venv venv
source venv/bin/activate
```

### Step 2: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 3: Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your credentials
# You need:
# - SUPABASE_URL (from your Supabase project settings)
# - SUPABASE_KEY (anon/public key from Supabase)
# - BRIGHTDATA_API_TOKEN (from Bright Data dashboard)
```

### Step 4: Setup Database

1. Go to your Supabase project dashboard
2. Navigate to SQL Editor
3. Copy the contents of `database/schema.sql`
4. Execute the SQL to create all tables and indexes

### Step 5: Verify Setup

```bash
# Run the validation script
python setup_check.py

# Test configuration import
python -c "from config.settings import settings; print('✓ Config loaded successfully')"

# Test database connection (after .env is configured)
python -c "from database.client import get_supabase_client; client = get_supabase_client(); print('✓ Database connected')"
```

## 📋 Success Criteria Checklist

- [x] Project structure created
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] `.env` file configured with credentials
- [ ] `schema.sql` executed in Supabase
- [ ] `config.settings` imports without errors
- [ ] Database connection successful

## 🔍 Troubleshooting

### Import Errors

If you get import errors, ensure:
1. Virtual environment is activated
2. All dependencies are installed
3. You're running Python 3.11+

### Database Connection Errors

If database connection fails:
1. Verify SUPABASE_URL and SUPABASE_KEY in `.env`
2. Check that schema.sql was executed successfully
3. Ensure your Supabase project is active

### Configuration Validation Errors

If settings validation fails:
1. Ensure all required variables are in `.env`
2. Check for typos in variable names
3. Verify `.env` file encoding is UTF-8

## 📚 What's Next?

Once Phase 1 is complete, you'll be ready for:
- **Phase 2**: Bright Data API Client implementation
- **Phase 3**: Data Processing & Normalization
- **Phase 4**: Core Backend Services
- **Phase 5**: Web Interface (FastAPI + Frontend)
