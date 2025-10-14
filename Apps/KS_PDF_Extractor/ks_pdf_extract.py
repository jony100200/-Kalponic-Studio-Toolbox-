#!/usr/bin/env python3
"""
KS PDF Extractor - Main CLI Interface
=====================================

Command-line interface for extracting text from PDF files.
Supports output to text or markdown format with configurable options.

Following KS Development Strategy Guide v4.0:
- Build smart, stay real, enjoy the process
- User-first design
- Modular architecture
- Clear feedback

Usage:
    python ks_pdf_extract.py --input document.pdf --format md
    python ks_pdf_extract.py --input ./pdfs/ --format txt --batch
"""

import argparse
import sys
import os
from pathlib import Path
from typing import Optional, List

# Add the current directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent))

try:
    from core.pdf_processor import PDFExtractor
    from config.config_manager import ConfigManager
    from utils.file_utils import FileUtils, TextUtils, MarkdownUtils
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("💡 Make sure you're running from the KS_PDF_Extractor directory")
    sys.exit(1)

import logging

class KSPDFExtractorCLI:
    """
    Command-line interface for KS PDF Extractor
    """
    
    def __init__(self):
        """Initialize the CLI application"""
        self.config_manager = ConfigManager()
        self.extractor = None
        self.setup_logging()
        
        # Banner
        print("🔧 KS PDF Extractor v1.0")
        print("📄 Extract PDF content to Text or Markdown")
        print("🌟 Built with KS Standards\n")
    
    def setup_logging(self):
        """Setup logging based on configuration"""
        log_level = self.config_manager.get('logging.level', 'INFO')
        
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Setup file logging if enabled
        if self.config_manager.get('logging.file_logging', False):
            log_file = self.config_manager.get('logging.log_file', 'ks_pdf_extractor.log')
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
            logging.getLogger().addHandler(file_handler)
    
    def create_extractor(self) -> PDFExtractor:
        """Create PDF extractor with current configuration"""
        if not self.extractor:
            extraction_config = self.config_manager.get_extraction_config()
            self.extractor = PDFExtractor(extraction_config)
        return self.extractor
    
    def extract_single_file(self, input_path: str, output_path: Optional[str], format_type: str) -> bool:
        """
        Extract text from a single PDF file
        
        Args:
            input_path: Path to input PDF
            output_path: Optional output path
            format_type: Output format ('txt' or 'md')
            
        Returns:
            True if successful, False otherwise
        """
        try:
            input_file = Path(input_path)
            if not input_file.exists():
                print(f"❌ Input file not found: {input_file}")
                return False
            
            if not input_file.suffix.lower() == '.pdf':
                print(f"❌ File is not a PDF: {input_file}")
                return False
            
            print(f"🔍 Processing: {input_file.name}")
            
            # Extract text
            extractor = self.create_extractor()
            result = extractor.extract_text(str(input_file))
            
            if not result['success']:
                print(f"❌ Extraction failed: {result.get('error', 'Unknown error')}")
                return False
            
            # Determine output path
            if not output_path:
                base_name = input_file.stem
                safe_name = FileUtils.get_safe_filename(base_name)
                output_file = input_file.parent / f"{safe_name}.{format_type}"
            else:
                output_file = Path(output_path)
                # Ensure output directory exists
                output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Format content based on output type
            if format_type.lower() == 'md':
                title = TextUtils.extract_title(result['text']) or input_file.stem
                content = extractor.format_as_markdown(result, title)
                
                # Add table of contents if enabled
                if self.config_manager.get('markdown.add_toc', False):
                    toc = MarkdownUtils.create_toc(content)
                    if toc:
                        content = content.replace('## Content\n', f"{toc}## Content\n")
            else:
                content = result['text']
            
            # Add statistics if enabled
            if self.config_manager.get('output.add_stats', True):
                stats = TextUtils.get_text_stats(result['text'])
                if format_type.lower() == 'md':
                    stats_md = f"\n\n---\n\n**Document Statistics:**\n"
                    stats_md += f"- **Pages:** {result['page_count']}\n"
                    stats_md += f"- **Characters:** {stats['characters']:,}\n"
                    stats_md += f"- **Words:** {stats['words']:,}\n"
                    stats_md += f"- **Lines:** {stats['lines']:,}\n"
                    stats_md += f"- **Paragraphs:** {stats['paragraphs']:,}\n"
                    content += stats_md
                else:
                    content += f"\n\n--- Document Statistics ---\n"
                    content += f"Pages: {result['page_count']}\n"
                    content += f"Characters: {stats['characters']:,}\n"
                    content += f"Words: {stats['words']:,}\n"
                    content += f"Lines: {stats['lines']:,}\n"
                    content += f"Paragraphs: {stats['paragraphs']:,}\n"
            
            # Save to file
            encoding = self.config_manager.get('output.encoding', 'utf-8')
            
            with open(output_file, 'w', encoding=encoding) as f:
                f.write(content)
            
            # Print success message
            file_size = FileUtils.format_file_size(output_file.stat().st_size)
            print(f"✅ Extracted to: {output_file}")
            print(f"📊 Output: {len(result['text']):,} chars, {result['page_count']} pages, {file_size}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error processing file: {e}")
            return False
    
    def extract_batch(self, input_dir: str, output_dir: Optional[str], format_type: str) -> bool:
        """
        Extract text from all PDFs in a directory
        
        Args:
            input_dir: Input directory containing PDFs
            output_dir: Output directory (defaults to input_dir/extracted)
            format_type: Output format ('txt' or 'md')
            
        Returns:
            True if successful, False otherwise
        """
        try:
            input_path = Path(input_dir)
            if not input_path.exists():
                print(f"❌ Input directory not found: {input_path}")
                return False
            
            # Determine output directory
            if not output_dir:
                output_path = input_path / "extracted"
            else:
                output_path = Path(output_dir)
            
            output_path.mkdir(parents=True, exist_ok=True)
            
            print(f"🔄 Batch processing: {input_path}")
            print(f"📁 Output directory: {output_path}")
            
            # Use extractor's batch processing
            extractor = self.create_extractor()
            results = extractor.batch_extract(str(input_path), str(output_path), format_type)
            
            if not results:
                print("⚠️  No PDF files found to process")
                return False
            
            # Summary
            successful = sum(1 for r in results if r['success'])
            failed = len(results) - successful
            
            print(f"\n📊 Batch Processing Summary:")
            print(f"✅ Successful: {successful}")
            print(f"❌ Failed: {failed}")
            print(f"📁 Output: {output_path}")
            
            # Show failed files if any
            if failed > 0:
                print(f"\n❌ Failed files:")
                for result in results:
                    if not result['success']:
                        error = result.get('error', 'Unknown error')
                        print(f"   • {Path(result['pdf_file']).name}: {error}")
            
            return successful > 0
            
        except Exception as e:
            print(f"❌ Error in batch processing: {e}")
            return False
    
    def show_config(self):
        """Display current configuration"""
        print("⚙️  Current Configuration:")
        print("=" * 50)
        
        config_sections = [
            ('Extraction', self.config_manager.get_extraction_config()),
            ('Output', self.config_manager.get_output_config()),
            ('Markdown', self.config_manager.get_markdown_config()),
            ('Batch', self.config_manager.get_batch_config()),
        ]
        
        for section_name, section_config in config_sections:
            print(f"\n{section_name}:")
            for key, value in section_config.items():
                print(f"  {key}: {value}")
        
        print(f"\nConfig file: {self.config_manager.config_path}")
    
    def run_interactive_mode(self):
        """Run in interactive mode"""
        print("🎯 Interactive Mode")
        print("Enter 'quit' or 'exit' to stop\n")
        
        while True:
            try:
                # Get input file
                input_path = input("📄 PDF file or directory path: ").strip()
                
                if input_path.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                
                if not input_path:
                    continue
                
                path = Path(input_path)
                if not path.exists():
                    print(f"❌ Path not found: {path}")
                    continue
                
                # Get format
                format_choice = input("📝 Output format (txt/md) [md]: ").strip().lower()
                if not format_choice:
                    format_choice = 'md'
                
                if format_choice not in ['txt', 'md']:
                    print("❌ Invalid format. Use 'txt' or 'md'")
                    continue
                
                # Process
                if path.is_file():
                    self.extract_single_file(str(path), None, format_choice)
                elif path.is_dir():
                    self.extract_batch(str(path), None, format_choice)
                
                print()  # Empty line for readability
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    def main(self):
        """Main CLI entry point"""
        parser = argparse.ArgumentParser(
            description='KS PDF Extractor - Extract text from PDF files to text or markdown',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog='''
Examples:
  # Extract single PDF to markdown
  python ks_pdf_extract.py --input document.pdf --format md
  
  # Extract to specific output file
  python ks_pdf_extract.py --input document.pdf --output extracted.txt --format txt
  
  # Batch process all PDFs in directory
  python ks_pdf_extract.py --input ./pdfs/ --format md --batch
  
  # Run in interactive mode
  python ks_pdf_extract.py --interactive
  
  # Show current configuration
  python ks_pdf_extract.py --show-config
            '''
        )
        
        parser.add_argument('--input', '-i', 
                          help='Input PDF file or directory')
        
        parser.add_argument('--output', '-o', 
                          help='Output file path (optional)')
        
        parser.add_argument('--format', '-f', 
                          choices=['txt', 'md'], 
                          default='md',
                          help='Output format (default: md)')
        
        parser.add_argument('--batch', '-b', 
                          action='store_true',
                          help='Batch process directory')
        
        parser.add_argument('--interactive', 
                          action='store_true',
                          help='Run in interactive mode')
        
        parser.add_argument('--show-config', 
                          action='store_true',
                          help='Show current configuration')
        
        parser.add_argument('--verbose', '-v', 
                          action='store_true',
                          help='Verbose output')
        
        args = parser.parse_args()
        
        # Set verbose logging if requested
        if args.verbose:
            logging.getLogger().setLevel(logging.DEBUG)
        
        # Handle different modes
        if args.show_config:
            self.show_config()
            return
        
        if args.interactive:
            self.run_interactive_mode()
            return
        
        if not args.input:
            print("❌ No input specified. Use --input or --interactive mode")
            parser.print_help()
            return
        
        # Check if input is file or directory
        input_path = Path(args.input)
        
        if input_path.is_file():
            success = self.extract_single_file(args.input, args.output, args.format)
        elif input_path.is_dir():
            if not args.batch:
                print("❌ Input is a directory. Use --batch flag for batch processing")
                return
            success = self.extract_batch(args.input, args.output, args.format)
        else:
            print(f"❌ Input path not found: {input_path}")
            return
        
        if not success:
            sys.exit(1)

if __name__ == '__main__':
    try:
        cli = KSPDFExtractorCLI()
        cli.main()
    except KeyboardInterrupt:
        print("\n👋 Operation cancelled by user")
        sys.exit(130)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)