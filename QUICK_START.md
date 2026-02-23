# Quick Start Guide

Get up and running with AstraDB Quality Check Tool in 5 minutes!

## Step 1: Install Dependencies

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install the package
pip install -e .
```

## Step 2: Configure AstraDB

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` with your AstraDB credentials:

```env
ASTRA_DB_ENDPOINT=https://your-database-id.apps.astra.datastax.com
ASTRA_DB_TOKEN=AstraCS:your-token-here
ASTRA_DB_KEYSPACE=default_keyspace
ASTRA_DB_COLLECTION=qa_collection
```

### Where to Find Your Credentials:

1. **Endpoint**: In AstraDB Console → Your Database → Connect → API Endpoint
2. **Token**: In AstraDB Console → Your Database → Settings → Application Tokens
3. **Keyspace**: The keyspace name you created (default: `default_keyspace`)
4. **Collection**: Your vector collection name

## Step 3: Test Connection

```bash
astra-clean test-connection
```

You should see:
```
✓ Successfully connected to AstraDB!

Collection: qa_collection
Keyspace: default_keyspace
Approximate Documents: 1234
```

## Step 4: View Your Data

```bash
# Get collection statistics
astra-clean stats

# View detailed stats
astra-clean stats --detailed

# Show a specific document
astra-clean show <document_id>
```

## Step 5: Start Cleaning!

### Update a Document

```bash
astra-clean update <doc_id> --question "Updated question" --answer "Updated answer"
```

### Delete a Document

```bash
astra-clean delete <doc_id>
```

## Common Issues

### "Configuration incomplete" Error

Make sure your `.env` file exists and has valid credentials:
```bash
cat .env  # Check if file exists and has content
```

### "Connection failed" Error

1. Verify your token hasn't expired
2. Check your endpoint URL is correct
3. Ensure your IP is whitelisted (if applicable)

### Import Errors

Reinstall the package:
```bash
pip install -e . --force-reinstall
```

## Next Steps

- Read the full [README.md](README.md) for all features
- Check [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) for upcoming features
- Run `astra-clean --help` to see all available commands

## Getting Help

```bash
# General help
astra-clean --help

# Command-specific help
astra-clean stats --help
astra-clean update --help
```

## What's Working Now (Phase 1)

✅ Connection to AstraDB
✅ View collection statistics
✅ Show document details
✅ Update documents
✅ Delete documents
✅ Beautiful CLI output with Rich
✅ Configuration management
✅ Logging

## Coming Soon (Phase 2+)

🔜 Similarity search
🔜 Keyword search
🔜 Duplicate detection
🔜 Quality scoring
🔜 Export/Import
🔜 Audit logging
🔜 Batch operations

---

**Ready to contribute?** Check out the [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) to see what's next!
