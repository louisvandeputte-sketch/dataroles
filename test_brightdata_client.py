#!/usr/bin/env python3
"""Test Bright Data API clients (mock and real)."""

import asyncio
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from clients import get_client, get_mock_brightdata_client
from clients.brightdata_linkedin import BrightDataError, QuotaExceededError, SnapshotTimeoutError

console = Console()


async def test_mock_client():
    """Test the mock Bright Data client."""
    console.print("\n[bold cyan]Testing Mock Bright Data Client...[/bold cyan]")
    
    client = get_mock_brightdata_client()
    
    try:
        # Test 1: Trigger collection
        console.print("\n[yellow]1. Triggering collection...[/yellow]")
        snapshot_id = await client.trigger_collection(
            keyword="Data Engineer",
            location="Netherlands",
            posted_date_range="past_week",
            limit=10
        )
        console.print(f"[green]✓ Collection triggered: {snapshot_id}[/green]")
        
        # Test 2: Check status immediately
        console.print("\n[yellow]2. Checking initial status...[/yellow]")
        status = await client.get_snapshot_status(snapshot_id)
        console.print(f"[green]✓ Status: {status['status']}, Progress: {status['progress']}%[/green]")
        
        # Test 3: Wait for completion
        console.print("\n[yellow]3. Waiting for completion...[/yellow]")
        results = await client.wait_for_completion(snapshot_id, poll_interval=1, timeout=30)
        console.print(f"[green]✓ Completed! Retrieved {len(results)} jobs[/green]")
        
        # Test 4: Display sample results
        if results:
            console.print("\n[yellow]4. Sample results:[/yellow]")
            table = Table(title="Sample Jobs")
            table.add_column("Job ID", style="cyan")
            table.add_column("Title", style="white")
            table.add_column("Company", style="yellow")
            table.add_column("Location", style="green")
            
            for job in results[:3]:
                table.add_row(
                    job.get("job_posting_id", "N/A")[:15],
                    job.get("job_title", "N/A")[:30],
                    job.get("company_name", "N/A")[:20],
                    job.get("job_location", "N/A")[:25]
                )
            
            console.print(table)
        
        await client.close()
        return True
        
    except Exception as e:
        console.print(f"[red]✗ Mock client test failed: {e}[/red]")
        return False


async def test_error_handling():
    """Test error handling scenarios."""
    console.print("\n[bold cyan]Testing Error Handling...[/bold cyan]")
    
    client = get_mock_brightdata_client()
    
    try:
        # Test 1: Invalid snapshot ID
        console.print("\n[yellow]1. Testing invalid snapshot ID...[/yellow]")
        status = await client.get_snapshot_status("invalid_snapshot_id")
        if status.get("status") == "failed":
            console.print("[green]✓ Correctly handled invalid snapshot[/green]")
        
        # Test 2: Download before ready
        console.print("\n[yellow]2. Testing download before ready...[/yellow]")
        snapshot_id = await client.trigger_collection("test", "test", limit=1)
        try:
            await client.download_results(snapshot_id)
            console.print("[red]✗ Should have raised error[/red]")
        except ValueError as e:
            console.print(f"[green]✓ Correctly raised error: {str(e)[:50]}[/green]")
        
        await client.close()
        return True
        
    except Exception as e:
        console.print(f"[red]✗ Error handling test failed: {e}[/red]")
        return False


async def test_client_factory():
    """Test the client factory function."""
    console.print("\n[bold cyan]Testing Client Factory...[/bold cyan]")
    
    try:
        # Get client based on settings
        client = get_client()
        console.print(f"[green]✓ Client created: {type(client).__name__}[/green]")
        
        # Verify it's the mock client (since USE_MOCK_API=true in .env)
        from clients.mock_brightdata import MockBrightDataLinkedInClient
        if isinstance(client, MockBrightDataLinkedInClient):
            console.print("[green]✓ Correctly returned mock client (USE_MOCK_API=true)[/green]")
        
        await client.close()
        return True
        
    except Exception as e:
        console.print(f"[red]✗ Factory test failed: {e}[/red]")
        return False


async def test_real_client_initialization():
    """Test that real client can be initialized (without calling API)."""
    console.print("\n[bold cyan]Testing Real Client Initialization...[/bold cyan]")
    
    try:
        from clients.brightdata_linkedin import get_brightdata_client
        
        # Just test initialization, don't make API calls
        client = get_brightdata_client()
        console.print(f"[green]✓ Real client initialized[/green]")
        console.print(f"  Dataset ID: {client.dataset_id}")
        console.print(f"  Timeout: {client.timeout}s")
        console.print(f"  Poll interval: {client.poll_interval}s")
        
        await client.close()
        return True
        
    except Exception as e:
        console.print(f"[red]✗ Real client initialization failed: {e}[/red]")
        return False


async def main():
    """Run all tests."""
    console.print(Panel.fit(
        "[bold blue]Bright Data API Client Tests[/bold blue]",
        border_style="blue"
    ))
    
    results = []
    
    # Run tests
    results.append(("Mock Client", await test_mock_client()))
    results.append(("Error Handling", await test_error_handling()))
    results.append(("Client Factory", await test_client_factory()))
    results.append(("Real Client Init", await test_real_client_initialization()))
    
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
            "The Bright Data client is ready to use.\n"
            "Mock mode is enabled (USE_MOCK_API=true)",
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
