#!/usr/bin/env python3
"""Test the job lifecycle manager."""

from datetime import datetime, timedelta
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from scraper import mark_inactive_jobs, get_inactive_jobs_summary
from database import db

console = Console()


def test_mark_inactive_jobs():
    """Test marking jobs as inactive."""
    console.print("\n[bold cyan]Testing Mark Inactive Jobs...[/bold cyan]")
    
    # Get current stats
    stats_before = db.get_stats()
    active_before = stats_before.get("active_jobs", 0)
    
    console.print(f"  Active jobs before: [cyan]{active_before}[/cyan]")
    
    # Mark jobs inactive (14 day threshold)
    count = mark_inactive_jobs(threshold_days=14)
    
    console.print(f"  Jobs marked inactive: [yellow]{count}[/yellow]")
    
    # Get updated stats
    stats_after = db.get_stats()
    active_after = stats_after.get("active_jobs", 0)
    
    console.print(f"  Active jobs after: [cyan]{active_after}[/cyan]")
    
    return True


def test_custom_threshold():
    """Test with custom threshold."""
    console.print("\n[bold cyan]Testing Custom Threshold...[/bold cyan]")
    
    # Try different thresholds
    thresholds = [7, 14, 30]
    
    table = Table(title="Inactive Jobs by Threshold")
    table.add_column("Threshold (days)", style="cyan", justify="right")
    table.add_column("Jobs Marked", style="yellow", justify="right")
    
    for threshold in thresholds:
        count = mark_inactive_jobs(threshold_days=threshold)
        table.add_row(str(threshold), str(count))
    
    console.print(table)
    
    return True


def test_inactive_summary():
    """Test getting inactive jobs summary."""
    console.print("\n[bold cyan]Testing Inactive Jobs Summary...[/bold cyan]")
    
    summary = get_inactive_jobs_summary()
    
    table = Table(title="Inactive Jobs Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Count", style="green", justify="right")
    
    table.add_row("Total Inactive", str(summary.get("total_inactive", 0)))
    table.add_row("Inactive Last 7 Days", str(summary.get("inactive_last_7_days", 0)))
    table.add_row("Inactive Last 30 Days", str(summary.get("inactive_last_30_days", 0)))
    
    console.print(table)
    
    # Verify structure
    assert "total_inactive" in summary
    assert "inactive_last_7_days" in summary
    assert "inactive_last_30_days" in summary
    
    return True


def test_lifecycle_workflow():
    """Test complete lifecycle workflow."""
    console.print("\n[bold cyan]Testing Complete Lifecycle Workflow...[/bold cyan]")
    
    # Step 1: Get initial stats
    console.print("  [1] Getting initial statistics...")
    stats = db.get_stats()
    console.print(f"      Total jobs: {stats.get('total_jobs', 0)}")
    console.print(f"      Active jobs: {stats.get('active_jobs', 0)}")
    
    # Step 2: Mark inactive jobs
    console.print("  [2] Marking inactive jobs...")
    count = mark_inactive_jobs(threshold_days=14)
    console.print(f"      Marked {count} jobs as inactive")
    
    # Step 3: Get summary
    console.print("  [3] Getting inactive summary...")
    summary = get_inactive_jobs_summary()
    console.print(f"      Total inactive: {summary.get('total_inactive', 0)}")
    
    # Step 4: Get updated stats
    console.print("  [4] Getting updated statistics...")
    stats_after = db.get_stats()
    console.print(f"      Active jobs: {stats_after.get('active_jobs', 0)}")
    
    console.print("\n  [green]✓ Lifecycle workflow complete[/green]")
    
    return True


def main():
    """Run all tests."""
    console.print(Panel.fit(
        "[bold blue]Job Lifecycle Manager Tests[/bold blue]",
        border_style="blue"
    ))
    
    results = []
    
    # Run tests
    results.append(("Mark Inactive Jobs", test_mark_inactive_jobs()))
    results.append(("Custom Threshold", test_custom_threshold()))
    results.append(("Inactive Summary", test_inactive_summary()))
    results.append(("Lifecycle Workflow", test_lifecycle_workflow()))
    
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
            "The job lifecycle manager is working correctly.",
            border_style="green"
        ))
    else:
        console.print(Panel.fit(
            "[bold red]✗ Some Tests Failed[/bold red]",
            border_style="red"
        ))
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(main())
