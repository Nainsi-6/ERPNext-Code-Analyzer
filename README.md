# ERPNext DocType Analyzer

A tool to analyze ERPNext's DocType structure and relationships.

## What It Does

1. **Extracts DocType Info**: Reads all DocType JSON files
   - Number of fields
   - Field types distribution
   - Link relationships

2. **Analyzes Relationships**: Maps which DocTypes reference which
   - Sales Invoice → Customer
   - Purchase Order → Supplier
   - etc.

3. **Generates Reports**: Creates JSON exports and terminal summaries

## How to Use

```bash
# Analyze ERPNext core
python analyze.py /path/to/erpnext

# View results
cat erpnext_analysis/doctypes.json
cat erpnext_analysis/relationships.json
```

## Output Files

- `doctypes.json`: All DocType information
- `relationships.json`: All DocType relationships
- Terminal summary with statistics

## Example Output

```
Entity: Sales Invoice
Total Fields: 224
Field Types: Link(8), Data(12), Check(5), Table(3), ...

Relationships:
- Sales Invoice → Customer (field: customer)
- Sales Invoice → Company (field: company)
- Sales Invoice → Project (field: project)
```

## Learning Outcomes

- Understanding DocType structure
- Analyzing JSON schemas programmatically
- Mapping entity relationships
- Data processing and summarization
