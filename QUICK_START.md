# DataRoles Quick Start

## 🚀 Get Started in 5 Minutes

### 1. Setup Environment (2 min)

```bash
cd /Users/louisvandeputte/datarole

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Credentials (2 min)

```bash
# Copy template
cp .env.example .env

# Edit with your credentials
nano .env  # or use your preferred editor
```

Required credentials:
- `SUPABASE_URL` - From Supabase project settings
- `SUPABASE_KEY` - Anon/public key from Supabase
- `BRIGHTDATA_API_TOKEN` - From Bright Data dashboard

### 3. Setup Database (1 min)

1. Open Supabase Dashboard
2. Go to SQL Editor
3. Copy & paste `database/schema.sql`
4. Click "Run"

### 4. Verify Setup

```bash
python setup_check.py
```

## ✅ You're Ready!

Once setup is complete, you can:
- Proceed to Phase 2 (Bright Data API Client)
- Start the web interface (Phase 5)
- Run tests: `pytest`

## 📚 Documentation

- **README.md** - Full project overview
- **SETUP_INSTRUCTIONS.md** - Detailed setup guide
- **PHASE1_COMPLETE.md** - Phase 1 summary
- **database/schema.sql** - Database schema with comments

## 🆘 Need Help?

Common issues:
- **Import errors**: Activate venv and install requirements
- **Config errors**: Check .env file has all required variables
- **DB errors**: Verify schema.sql was executed in Supabase

## 🎯 Current Status

- ✅ Phase 1: Foundation Layer - COMPLETE
- ⏳ Phase 2: Bright Data API Client - PENDING
- ⏳ Phase 3: Data Processing - PENDING
- ⏳ Phase 4: Backend Services - PENDING
- ⏳ Phase 5: Web Interface - PENDING
- ⏳ Phase 6: Monitoring - PENDING
- ⏳ Phase 7: Testing - PENDING
