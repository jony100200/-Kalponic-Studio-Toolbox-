"""
Command-line interface for KS SnapStudio.
"""

import typer
from pathlib import Path
from typing import Optional, List
import logging
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

# Import core modules
from ks_snapstudio.core.capture import ScreenCapture
from ks_snapstudio.core.mask import CircleMask
from ks_snapstudio.core.watermark import WatermarkEngine
from ks_snapstudio.core.composer import BackgroundComposer
from ks_snapstudio.core.exporter import PreviewExporter
from ks_snapstudio.presets.manager import PresetManager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Rich console for better output
console = Console()

# Create Typer app
app = typer.Typer(
    name="ks-snapstudio",
    help="Professional circular preview capture and export tool for 3D materials",
    add_completion=False,
)


@app.command()
def capture(
    output: Path = typer.Option("preview.png", "--output", "-o", help="Output file path"),
    area: Optional[str] = typer.Option(None, "--area", "-a", help="Capture area as x,y,width,height"),
    monitor: int = typer.Option(1, "--monitor", "-m", help="Monitor number to capture from"),
    preset: Optional[str] = typer.Option(None, "--preset", "-p", help="Use preset for processing"),
    background: str = typer.Option("random", "--bg", help="Background type (solid, gradient, noise, pattern, random)"),
    palette: str = typer.Option("random", "--palette", help="Color palette (neutral, warm, cool, dark, random)"),
    watermark: bool = typer.Option(True, "--watermark/--no-watermark", help="Add watermark"),
    brand_ring: bool = typer.Option(True, "--ring/--no-ring", help="Add brand ring"),
    quality: int = typer.Option(95, "--quality", "-q", help="Export quality (1-100)"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
):
    """
    Capture screen and create circular preview.

    Examples:
        ks-snapstudio capture
        ks-snapstudio capture -a 100,100,800,600 -p artstation_2048_dark
        ks-snapstudio capture -o my_preview.png --bg gradient --palette warm
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            # Initialize components
            task = progress.add_task("Initializing...", total=5)
            capture_tool = ScreenCapture()
            mask_tool = CircleMask()
            watermark_tool = WatermarkEngine()
            composer = BackgroundComposer()
            exporter = PreviewExporter()
            preset_mgr = PresetManager()

            progress.update(task, advance=1, description="Capturing screen...")

            # Capture screen
            if area:
                # Parse area coordinates
                try:
                    x, y, w, h = map(int, area.split(','))
                    image = capture_tool.capture_area(x, y, w, h, monitor)
                except ValueError:
                    console.print("[red]Error: Invalid area format. Use x,y,width,height[/red]")
                    raise typer.Exit(1)
            else:
                image = capture_tool.capture_fullscreen(monitor)

            progress.update(task, advance=1, description="Detecting circle...")

            # Detect circle
            circle_info = mask_tool.detect_circle(image)

            if circle_info is None:
                console.print("[yellow]Warning: No circle detected, using center crop[/yellow]")
                # Fallback: crop center square
                height, width = image.shape[:2]
                size = min(width, height)
                x = (width - size) // 2
                y = (height - size) // 2
                cropped = image[y:y+size, x:x+size]
                circle_info = {'center': (size//2, size//2), 'radius': size//2, 'confidence': 0.0}
            else:
                # Crop to circle
                cropped, circle_info = mask_tool.auto_crop_circle(image, circle_info)

            progress.update(task, advance=1, description="Creating mask...")

            # Create circular mask
            mask = mask_tool.create_circular_mask(cropped, circle_info['center'], circle_info['radius'])

            # Apply mask
            masked = mask_tool.apply_mask(cropped, mask)

            progress.update(task, advance=1, description="Adding branding...")

            # Apply preset settings or defaults
            if preset:
                preset_config = preset_mgr.get_preset(preset)
                if preset_config:
                    background = preset_config.get('background', background)
                    palette = preset_config.get('palette', palette)
                    watermark_flag = preset_config.get('watermark', watermark)
                    brand_ring_flag = preset_config.get('brand_ring', brand_ring)
                    quality = preset_config.get('quality', quality)
                else:
                    console.print(f"[yellow]Warning: Preset '{preset}' not found, using defaults[/yellow]")
                    watermark_flag = watermark
                    brand_ring_flag = brand_ring
            else:
                watermark_flag = watermark
                brand_ring_flag = brand_ring

            # Add brand ring
            if brand_ring_flag:
                masked = watermark_tool.add_brand_ring(masked, circle_info)

            # Add watermark
            if watermark_flag:
                masked = watermark_tool.add_watermark_text(masked, "KS SnapStudio")

            progress.update(task, advance=1, description="Composing background...")

            # Compose background
            final = composer.compose_background(masked, background, palette)

            progress.update(task, advance=1, description="Exporting...")

            # Export
            success = exporter.export_preview(final, output, quality=quality)

            if success:
                console.print(f"[green]✓ Preview exported to {output}[/green]")
                console.print(f"   Size: {final.shape[1]}x{final.shape[0]}")
                console.print(f"   Format: {output.suffix[1:].upper()}")
                if circle_info['confidence'] > 0:
                    console.print(".2f"                else:
                    console.print("   Circle detection: Manual crop used")
            else:
                console.print("[red]✗ Export failed[/red]")
                raise typer.Exit(1)

    except KeyboardInterrupt:
        console.print("[yellow]Operation cancelled[/yellow]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        raise typer.Exit(1)


@app.command()
def batch(
    input_dir: Path = typer.Argument(..., help="Input directory containing images"),
    output_dir: Path = typer.Option(None, "--output", "-o", help="Output directory"),
    preset: str = typer.Option("dev_small", "--preset", "-p", help="Preset to use"),
    recursive: bool = typer.Option(False, "--recursive", "-r", help="Process subdirectories"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
):
    """
    Batch process images in a directory.

    Examples:
        ks-snapstudio batch ./raw_images
        ks-snapstudio batch ./materials -o ./previews -p artstation_2048_dark -r
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if output_dir is None:
        output_dir = input_dir / "previews"

    try:
        # Initialize components
        mask_tool = CircleMask()
        watermark_tool = WatermarkEngine()
        composer = BackgroundComposer()
        exporter = PreviewExporter()
        preset_mgr = PresetManager()

        # Get preset
        preset_config = preset_mgr.get_preset(preset)
        if not preset_config:
            console.print(f"[red]Error: Preset '{preset}' not found[/red]")
            raise typer.Exit(1)

        # Find images
        if recursive:
            image_files = list(input_dir.rglob("*.{png,jpg,jpeg,bmp,tiff,webp}"))
        else:
            image_files = list(input_dir.glob("*.{png,jpg,jpeg,bmp,tiff,webp}"))

        if not image_files:
            console.print(f"[yellow]No image files found in {input_dir}[/yellow]")
            return

        console.print(f"Found {len(image_files)} images to process")

        # Process images
        processed = 0
        output_dir.mkdir(parents=True, exist_ok=True)

        with Progress(console=console) as progress:
            task = progress.add_task("Processing images...", total=len(image_files))

            for img_path in image_files:
                try:
                    # Load image
                    import cv2
                    image = cv2.imread(str(img_path))
                    if image is None:
                        continue

                    # Convert BGR to RGB
                    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

                    # Detect and mask circle
                    circle_info = mask_tool.detect_circle(image)
                    if circle_info:
                        cropped, circle_info = mask_tool.auto_crop_circle(image, circle_info)
                        mask = mask_tool.create_circular_mask(cropped, circle_info['center'], circle_info['radius'])
                        masked = mask_tool.apply_mask(cropped, mask)
                    else:
                        # Fallback to center crop
                        height, width = image.shape[:2]
                        size = min(width, height)
                        x = (width - size) // 2
                        y = (height - size) // 2
                        masked = image[y:y+size, x:x+size]
                        circle_info = {'center': (size//2, size//2), 'radius': size//2}

                    # Apply branding
                    if preset_config.get('brand_ring', True):
                        masked = watermark_tool.add_brand_ring(masked, circle_info)

                    if preset_config.get('watermark', True):
                        masked = watermark_tool.add_watermark_text(masked, "KS SnapStudio")

                    # Compose background
                    final = composer.compose_background(
                        masked,
                        preset_config.get('background', 'solid'),
                        preset_config.get('palette', 'neutral')
                    )

                    # Export
                    output_path = output_dir / f"{img_path.stem}_preview{preset_config['format']}"
                    exporter.export_preview(
                        final,
                        output_path,
                        preset_config['format'],
                        preset_config.get('quality', 95)
                    )

                    processed += 1

                except Exception as e:
                    logger.warning(f"Failed to process {img_path}: {e}")

                progress.update(task, advance=1)

        console.print(f"[green]✓ Processed {processed}/{len(image_files)} images[/green]")
        console.print(f"   Output directory: {output_dir}")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def presets(
    platform: Optional[str] = typer.Option(None, "--platform", "-p", help="Filter by platform"),
    use: Optional[str] = typer.Option(None, "--use", "-u", help="Filter by use case"),
):
    """
    List available presets.

    Examples:
        ks-snapstudio presets
        ks-snapstudio presets --platform discord
        ks-snapstudio presets --use development
    """
    preset_mgr = PresetManager()

    if platform:
        presets_list = preset_mgr.get_presets_by_platform(platform)
        title = f"Presets for {platform.title()}"
    elif use:
        presets_list = preset_mgr.get_presets_by_use(use)
        title = f"Presets for {use.title()}"
    else:
        presets_list = list(preset_mgr.get_all_presets().values())
        title = "All Presets"

    if not presets_list:
        console.print(f"[yellow]No presets found for {platform or use or 'criteria'}[/yellow]")
        return

    table = Table(title=title)
    table.add_column("Name", style="cyan")
    table.add_column("Description", style="white")
    table.add_column("Size", style="green")
    table.add_column("Format", style="yellow")
    table.add_column("Platform", style="magenta")

    for preset in presets_list:
        metadata = preset.get('metadata', {})
        table.add_row(
            preset.get('name', 'Unknown'),
            preset.get('description', ''),
            str(preset.get('size', 'N/A')),
            preset.get('format', 'N/A'),
            metadata.get('platform', 'general')
        )

    console.print(table)


@app.command()
def watch(
    app_name: str = typer.Argument(..., help="Application name to watch (e.g., 'Substance Designer')"),
    preset: str = typer.Option("discord_1024_light", "--preset", "-p", help="Preset to use"),
    interval: float = typer.Option(2.0, "--interval", "-i", help="Check interval in seconds"),
    output_dir: Optional[Path] = typer.Option(None, "--output", "-o", help="Output directory"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
):
    """
    Watch mode - automatically capture when target app is active.

    Examples:
        ks-snapstudio watch "Substance Designer"
        ks-snapstudio watch "Blender" -p artstation_2048_dark -i 1.0
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    console.print(f"[blue]Starting watch mode for '{app_name}'[/blue]")
    console.print(f"[blue]Preset: {preset} | Interval: {interval}s[/blue]")
    console.print("[yellow]Press Ctrl+C to stop[/yellow]")

    try:
        # This would implement window watching logic
        # For now, just show it's a planned feature
        console.print("[red]Watch mode not yet implemented[/red]")
        console.print("[blue]This feature will monitor active windows and auto-capture when target app is focused[/blue]")

    except KeyboardInterrupt:
        console.print("[yellow]Watch mode stopped[/yellow]")


@app.callback()
def main(
    version: bool = typer.Option(False, "--version", "-V", help="Show version"),
):
    """KS SnapStudio - Professional circular preview capture and export tool."""
    if version:
        from ks_snapstudio import __version__
        console.print(f"KS SnapStudio v{__version__}")
        raise typer.Exit()


if __name__ == "__main__":
    app()</content>
<parameter name="filePath">E:\__Kalponic Studio Repositories\-Kalponic-Studio-Toolbox-\Apps\KS SnapStudio\src\ks_snapstudio\cli\main.py