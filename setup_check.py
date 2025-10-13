"""Setup validation script for Phase 1."""

import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


def check_project_structure():
    """Verify all required directories and files exist."""
    required_paths = [
        "config/__init__.py",
        "config/settings.py",
        "config/scrape_configs.yaml",
        "database/__init__.py",
        "database/client.py",
        "database/schema.sql",
        "models/__init__.py",
        "clients/__init__.py",
        "ingestion/__init__.py",
        "scraper/__init__.py",
        "web/__init__.py",
        "web/routes/__init__.py",
        "web/static/css/styles.css",
        "web/static/js/app.js",
        "utils/__init__.py",
        "utils/logging.py",
        "tests/__init__.py",
        "tests/conftest.py",
        "tests/fixtures/linkedin_sample.json",
        "requirements.txt",
        ".env.example",
        ".gitignore",
        "README.md",
        "main.py"
    ]
    
    missing = []
    for path in required_paths:
        if not Path(path).exists():
            missing.append(path)
    
    return missing


def check_dependencies():
    """Check if dependencies can be imported."""
    imports = {
        "pydantic": "pydantic",
        "pydantic_settings": "pydantic-settings",
        "supabase": "supabase",
        "fastapi": "fastapi",
        "loguru": "loguru",
        "httpx": "httpx",
        "click": "click",
        "rich": "rich",
        "pytest": "pytest",
        "yaml": "pyyaml"
    }
    
    missing = []
    for module, package in imports.items():
        try:
            __import__(module)
        except ImportError:
            missing.append(package)
    
    return missing


def check_env_file():
    """Check if .env file exists."""
    return Path(".env").exists()


def check_config_import():
    """Try to import config.settings."""
    try:
        from config.settings import settings
        return True, None
    except Exception as e:
        return False, str(e)


def main():
    """Run all setup checks."""
    console.print(Panel.fit(
        "[bold blue]DataRoles Phase 1 Setup Validation[/bold blue]",
        border_style="blue"
    ))
    
    # Check 1: Project Structure
    console.print("\n[bold]1. Checking Project Structure...[/bold]")
    missing_files = check_project_structure()
    if missing_files:
        console.print(f"[red]✗ Missing {len(missing_files)} files:[/red]")
        for f in missing_files:
            console.print(f"  - {f}")
    else:
        console.print("[green]✓ All required files present[/green]")
    
    # Check 2: Dependencies
    console.print("\n[bold]2. Checking Dependencies...[/bold]")
    missing_deps = check_dependencies()
    if missing_deps:
        console.print(f"[red]✗ Missing {len(missing_deps)} packages:[/red]")
        for dep in missing_deps:
            console.print(f"  - {dep}")
        console.print("\n[yellow]Run: pip install -r requirements.txt[/yellow]")
    else:
        console.print("[green]✓ All dependencies installed[/green]")
    
    # Check 3: Environment File
    console.print("\n[bold]3. Checking Environment Configuration...[/bold]")
    if check_env_file():
        console.print("[green]✓ .env file exists[/green]")
    else:
        console.print("[red]✗ .env file not found[/red]")
        console.print("[yellow]Run: cp .env.example .env[/yellow]")
        console.print("[yellow]Then edit .env with your credentials[/yellow]")
    
    # Check 4: Config Import
    console.print("\n[bold]4. Checking Configuration Import...[/bold]")
    config_ok, error = check_config_import()
    if config_ok:
        console.print("[green]✓ Configuration loads successfully[/green]")
    else:
        console.print(f"[red]✗ Configuration failed to load:[/red]")
        console.print(f"  {error}")
    
    # Summary
    console.print("\n" + "="*60)
    all_checks = [
        not missing_files,
        not missing_deps,
        check_env_file(),
        config_ok
    ]
    
    if all(all_checks):
        console.print("[bold green]✓ Phase 1 Setup Complete![/bold green]")
        console.print("\n[bold]Next Steps:[/bold]")
        console.print("1. Execute database/schema.sql in your Supabase SQL Editor")
        console.print("2. Update .env with your Supabase and Bright Data credentials")
        console.print("3. Ready to proceed to Phase 2!")
        return 0
    else:
        console.print("[bold red]✗ Setup Incomplete[/bold red]")
        console.print("Please fix the issues above before proceeding.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
