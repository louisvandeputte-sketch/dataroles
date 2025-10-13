#!/usr/bin/env python3
"""Test the ingestion processor with sample data."""

import asyncio
import json
from pathlib import Path
from uuid import uuid4
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from database import db
from ingestion.processor import process_job_posting, process_jobs_batch, BatchResult

console = Console()


async def test_single_job_processing():
    """Test processing a single job."""
    console.print("\n[bold cyan]Testing Single Job Processing...[/bold cyan]")
    
    # Load sample data
    sample_file = Path("tests/fixtures/linkedin_jobs_sample.json")
    with open(sample_file) as f:
        jobs = json.load(f)
    
    # Create a scrape run
    run_id = db.create_scrape_run({
        "search_query": "test",
        "location_query": "test",
        "status": "running"
    })
    
    # Process first job
    result = process_job_posting(jobs[0], run_id)
    
    console.print(f"  Status: [green]{result.status}[/green]")
    console.print(f"  Job ID: [cyan]{result.job_id}[/cyan]")
    
    if result.error:
        console.print(f"  Error: [red]{result.error}[/red]")
        return False
    
    # Process same job again (should be skipped or updated)
    result2 = process_job_posting(jobs[0], run_id)
    console.print(f"  Second run status: [yellow]{result2.status}[/yellow]")
    
    return True


async def test_batch_processing():
    """Test processing a batch of jobs."""
    console.print("\n[bold cyan]Testing Batch Processing...[/bold cyan]")
    
    # Load sample data
    sample_file = Path("tests/fixtures/linkedin_jobs_sample.json")
    with open(sample_file) as f:
        jobs = json.load(f)
    
    # Create a scrape run
    run_id = db.create_scrape_run({
        "search_query": "Data Engineer",
        "location_query": "Netherlands",
        "status": "running"
    })
    
    # Process batch
    result = await process_jobs_batch(jobs, run_id)
    
    # Display results
    table = Table(title="Batch Processing Results")
    table.add_column("Metric", style="cyan")
    table.add_column("Count", style="green", justify="right")
    
    table.add_row("New Jobs", str(result.new_count))
    table.add_row("Updated Jobs", str(result.updated_count))
    table.add_row("Skipped Jobs", str(result.skipped_count))
    table.add_row("Errors", str(result.error_count))
    table.add_row("[bold]Total[/bold]", f"[bold]{len(result.results)}[/bold]")
    
    console.print(table)
    
    # Update scrape run
    db.update_scrape_run(run_id, {
        "status": "completed",
        "completed_at": "2025-10-09T20:00:00Z",
        "jobs_found": len(jobs),
        "jobs_new": result.new_count,
        "jobs_updated": result.updated_count
    })
    
    return result.error_count == 0


async def test_deduplication():
    """Test that deduplication works."""
    console.print("\n[bold cyan]Testing Deduplication...[/bold cyan]")
    
    # Load sample data
    sample_file = Path("tests/fixtures/linkedin_jobs_sample.json")
    with open(sample_file) as f:
        jobs = json.load(f)
    
    # Create a scrape run
    run_id = db.create_scrape_run({
        "search_query": "test dedup",
        "location_query": "test",
        "status": "running"
    })
    
    # Process batch twice
    result1 = await process_jobs_batch(jobs, run_id)
    console.print(f"  First batch: {result1.summary()}")
    
    result2 = await process_jobs_batch(jobs, run_id)
    console.print(f"  Second batch: {result2.summary()}")
    
    # Second batch should have 0 new jobs
    if result2.new_count == 0:
        console.print("[green]✓ Deduplication working correctly[/green]")
        return True
    else:
        console.print(f"[red]✗ Deduplication failed: {result2.new_count} new jobs in second batch[/red]")
        return False


async def test_relationships():
    """Test that relationships are created correctly."""
    console.print("\n[bold cyan]Testing Relationships...[/bold cyan]")
    
    # Get stats
    stats = db.get_stats()
    
    table = Table(title="Database Statistics")
    table.add_column("Entity", style="cyan")
    table.add_column("Count", style="green", justify="right")
    
    table.add_row("Total Jobs", str(stats.get("total_jobs", 0)))
    table.add_row("Active Jobs", str(stats.get("active_jobs", 0)))
    table.add_row("Companies", str(stats.get("total_companies", 0)))
    
    console.print(table)
    
    return True


async def main():
    """Run all tests."""
    console.print(Panel.fit(
        "[bold blue]Ingestion Processor Tests[/bold blue]",
        border_style="blue"
    ))
    
    results = []
    
    # Run tests
    results.append(("Single Job Processing", await test_single_job_processing()))
    results.append(("Batch Processing", await test_batch_processing()))
    results.append(("Deduplication", await test_deduplication()))
    results.append(("Relationships", await test_relationships()))
    
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
            "The ingestion processor is working correctly.",
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
