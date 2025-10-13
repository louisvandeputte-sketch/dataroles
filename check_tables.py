#!/usr/bin/env python3
"""Check if all database tables exist."""

from database.client import get_supabase_client
from rich.console import Console
from rich.table import Table

console = Console()
client = get_supabase_client()

# Test each table
tables = [
    'companies',
    'locations', 
    'job_postings',
    'job_descriptions',
    'job_posters',
    'llm_enrichment',
    'scrape_runs',
    'job_scrape_history'
]

console.print('[bold cyan]Checking Database Tables...[/bold cyan]\n')

status_table = Table(title='Database Schema Status')
status_table.add_column('Table Name', style='cyan')
status_table.add_column('Status', style='green')

all_ok = True
for table_name in tables:
    try:
        result = client.table(table_name).select('*').limit(1).execute()
        status_table.add_row(table_name, '✓ Exists')
    except Exception as e:
        status_table.add_row(table_name, f'✗ Error')
        all_ok = False

console.print(status_table)

if all_ok:
    console.print('\n[bold green]✓ All 8 tables are ready![/bold green]')
    console.print('\n[bold yellow]Phase 1 is 100% complete![/bold yellow]')
    console.print('Ready to proceed to [bold]Phase 2: Bright Data API Client[/bold]')
else:
    console.print('\n[bold red]Some tables are missing![/bold red]')
