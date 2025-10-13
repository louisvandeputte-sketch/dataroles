#!/usr/bin/env python3
"""Test the scrape orchestrator."""

import asyncio
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from scraper import execute_scrape_run
from database import db

console = Console()


async def test_complete_scrape_run():
    """Test a complete end-to-end scrape run."""
    console.print("\n[bold cyan]Testing Complete Scrape Run...[/bold cyan]")
    
    # Execute scrape run
    result = await execute_scrape_run(
        query="Data Engineer",
        location="Netherlands"
    )
    
    # Display results
    table = Table(title="Scrape Run Results")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Run ID", str(result.run_id))
    table.add_row("Query", result.query)
    table.add_row("Location", result.location)
    table.add_row("Status", result.status)
    table.add_row("Jobs Found", str(result.jobs_found))
    table.add_row("New Jobs", str(result.jobs_new))
    table.add_row("Updated Jobs", str(result.jobs_updated))
    table.add_row("Duration", f"{result.duration_seconds:.1f}s")
    
    if result.snapshot_id:
        table.add_row("Snapshot ID", result.snapshot_id)
    
    if result.error:
        table.add_row("Error", result.error)
    
    console.print(table)
    
    # Print summary
    console.print(f"\n[bold]{result.summary()}[/bold]")
    
    return result.status == 'completed'


async def test_manual_lookback():
    """Test scrape run with manual lookback override."""
    console.print("\n[bold cyan]Testing Manual Lookback Override...[/bold cyan]")
    
    # Execute with manual lookback
    result = await execute_scrape_run(
        query="Data Scientist",
        location="Belgium",
        lookback_days=3  # Force 3 days
    )
    
    console.print(f"  Status: [green]{result.status}[/green]")
    console.print(f"  Jobs found: [cyan]{result.jobs_found}[/cyan]")
    console.print(f"  Duration: [yellow]{result.duration_seconds:.1f}s[/yellow]")
    
    return result.status == 'completed'


async def test_multiple_runs():
    """Test multiple scrape runs in sequence."""
    console.print("\n[bold cyan]Testing Multiple Runs...[/bold cyan]")
    
    queries = [
        ("Machine Learning Engineer", "Netherlands"),
        ("Data Analyst", "Belgium")
    ]
    
    results = []
    for query, location in queries:
        console.print(f"\n  Running: {query} in {location}")
        result = await execute_scrape_run(query, location)
        results.append(result)
        console.print(f"  → {result.status}: {result.jobs_found} jobs")
    
    # Summary
    total_jobs = sum(r.jobs_found for r in results)
    total_new = sum(r.jobs_new for r in results)
    
    console.print(f"\n  Total jobs: [green]{total_jobs}[/green]")
    console.print(f"  Total new: [green]{total_new}[/green]")
    
    return all(r.status == 'completed' for r in results)


async def test_scrape_run_history():
    """Test that scrape runs are recorded in database."""
    console.print("\n[bold cyan]Testing Scrape Run History...[/bold cyan]")
    
    # Get recent runs
    runs = db.get_scrape_runs(limit=5)
    
    table = Table(title="Recent Scrape Runs")
    table.add_column("Query", style="cyan")
    table.add_column("Location", style="white")
    table.add_column("Status", style="green")
    table.add_column("Jobs", style="yellow", justify="right")
    
    for run in runs:
        table.add_row(
            run.get("search_query", "N/A"),
            run.get("location_query", "N/A"),
            run.get("status", "N/A"),
            str(run.get("jobs_found", 0))
        )
    
    console.print(table)
    console.print(f"\n  Found {len(runs)} scrape runs in history")
    
    return len(runs) > 0


async def main():
    """Run all tests."""
    console.print(Panel.fit(
        "[bold blue]Scrape Orchestrator Tests[/bold blue]",
        border_style="blue"
    ))
    
    results = []
    
    # Run tests
    results.append(("Complete Scrape Run", await test_complete_scrape_run()))
    results.append(("Manual Lookback", await test_manual_lookback()))
    results.append(("Multiple Runs", await test_multiple_runs()))
    results.append(("Scrape Run History", await test_scrape_run_history()))
    
    # Summary
    console.print("\n" + "="*60)
    
    summary_table = Table(title="Test Summary")
    summary_table.add_column("Test", style="cyan")
    summary_table.add_column("Result", style="white")
    
    all_passed = True
    for test_name, passed in results:
        summary_table.add_row(
            test_name,
            "[green]✓ PASSED[/green]" if passed else "[red]✗ FAILED[/red]"
        )
        all_passed = all_passed and passed
    
    console.print(summary_table)
    
    if all_passed:
        console.print(Panel.fit(
            "[bold green]✓ All Tests Passed![/bold green]\n\n"
            "The scrape orchestrator is working correctly.\n"
            "Complete end-to-end workflow functional.",
            border_style="green"
        ))
    else:
        console.print(Panel.fit(
            "[bold red]✗ Some Tests Failed[/bold red]",
            border_style="red"
        ))
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(asyncio.run(main()))
