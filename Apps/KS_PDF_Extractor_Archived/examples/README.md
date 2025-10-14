# KS PDF Extractor - Examples

This directory contains example PDFs and usage scenarios for testing the KS PDF Extractor tool.

## Sample Files

Since we can't include actual PDF files in this repository, here are suggestions for testing:

### Test Files to Try

1. **Simple Text PDF**: Any basic document with plain text
2. **Complex Layout PDF**: Documents with tables, columns, images
3. **Multi-language PDF**: Documents with special characters
4. **Large PDF**: Documents with many pages (50+)
5. **Scanned PDF**: Image-based PDFs (will extract poorly - this is expected)

### Testing Commands

```bash
# Test single file extraction to markdown
python ks_pdf_extract.py --input sample.pdf --format md

# Test single file extraction to text
python ks_pdf_extract.py --input sample.pdf --format txt

# Test batch processing
mkdir test_pdfs
# Copy some PDF files to test_pdfs/
python ks_pdf_extract.py --input test_pdfs/ --format md --batch

# Test with custom output
python ks_pdf_extract.py --input sample.pdf --output custom_name.md --format md

# Interactive mode
python ks_pdf_extract.py --interactive

# Show configuration
python ks_pdf_extract.py --show-config
```

### Expected Results

- **Text files (.txt)**: Plain text with basic formatting preserved
- **Markdown files (.md)**: Formatted with headers, metadata, and statistics
- **Batch processing**: Creates `extracted/` directory with all processed files

### Performance Expectations

- Small PDFs (< 10 pages): Near instant
- Medium PDFs (10-100 pages): Few seconds
- Large PDFs (100+ pages): May take 10-30 seconds
- Very large PDFs (1000+ pages): May take several minutes

### Known Limitations

- Scanned PDFs (images) will have poor text extraction
- Complex layouts may lose formatting
- Password-protected PDFs are not supported
- Some PDF encodings may cause issues

## Creating Test PDFs

If you need to create test PDFs for development:

1. **From web pages**: Print any webpage to PDF
2. **From documents**: Export Word/Google Docs to PDF
3. **Generate programmatically**: Use libraries like ReportLab
4. **Online generators**: Use online PDF creation tools

## Troubleshooting Test Cases

### Common Issues to Test

1. **File not found**: Test with non-existent file paths
2. **Invalid PDFs**: Test with corrupted or non-PDF files
3. **Empty PDFs**: Test with blank or image-only PDFs
4. **Permission errors**: Test with read-only directories
5. **Large files**: Test with very large PDFs
6. **Special characters**: Test with international characters

### Error Scenarios

The tool should handle these gracefully:

```bash
# Non-existent file
python ks_pdf_extract.py --input nonexistent.pdf --format md

# Not a PDF
python ks_pdf_extract.py --input textfile.txt --format md

# Directory without PDFs
mkdir empty_dir
python ks_pdf_extract.py --input empty_dir/ --batch --format md
```

All these should show clear error messages without crashing.