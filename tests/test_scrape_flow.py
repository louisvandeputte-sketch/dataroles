#!/usr/bin/env python3
"""Test script to verify scrape flow and error handling."""

import asyncio
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from database.client import db
from scraper.orchestrator import execute_scrape_run
from clients import get_client

console = Console()


async def test_brightdata_connection():
    """Test 1: Verify Bright Data API connection."""
    console.print("\n[bold cyan]Test 1: Bright Data API Connection[/bold cyan]")
    
    try:
        client = get_client()
        console.print(f"✅ Client initialized: {type(client).__name__}")
        
        # Check if it's mock or real
        if hasattr(client, 'is_mock'):
            console.print("⚠️  Using MOCK client (USE_MOCK_API=true)")
        else:
            console.print("✅ Using REAL Bright Data client")
        
        return True
    except Exception as e:
        console.print(f"❌ Failed: {e}")
        return False


async def test_database_connection():
    """Test 2: Verify database connection."""
    console.print("\n[bold cyan]Test 2: Database Connection[/bold cyan]")
    
    try:
        # Try to query scrape_runs
        result = db.client.table("scrape_runs")\
            .select("id")\
            .limit(1)\
            .execute()
        
        console.print(f"✅ Database connected")
        console.print(f"✅ Can query scrape_runs table")
        return True
    except Exception as e:
        console.print(f"❌ Failed: {e}")
        return False


async def test_scrape_run_creation():
    """Test 3: Verify scrape run creation."""
    console.print("\n[bold cyan]Test 3: Scrape Run Creation[/bold cyan]")
    
    try:
        # Create a test run
        run_data = {
            "search_query": "TEST_QUERY",
            "location_query": "TEST_LOCATION",
            "platform": "linkedin_brightdata",
            "status": "running",
            "trigger_type": "manual",
            "metadata": {"test": True}
        }
        
        run_id = db.create_scrape_run(run_data)
        console.print(f"✅ Created test run: {run_id}")
        
        # Update it
        db.update_scrape_run(run_id, {
            "status": "completed",
            "jobs_found": 10,
            "jobs_new": 5,
            "jobs_updated": 3
        })
        console.print(f"✅ Updated test run")
        
        # Verify
        result = db.client.table("scrape_runs")\
            .select("*")\
            .eq("id", run_id)\
            .single()\
            .execute()
        
        run = result.data
        assert run['status'] == 'completed'
        assert run['jobs_found'] == 10
        console.print(f"✅ Verified test run data")
        
        # Clean up
        db.client.table("scrape_runs").delete().eq("id", run_id).execute()
        console.print(f"✅ Cleaned up test run")
        
        return True
    except Exception as e:
        console.print(f"❌ Failed: {e}")
        import traceback
        console.print(traceback.format_exc())
        return False


async def test_error_handling():
    """Test 4: Verify error handling in orchestrator."""
    console.print("\n[bold cyan]Test 4: Error Handling[/bold cyan]")
    
    try:
        # This should fail gracefully (invalid location)
        result = await execute_scrape_run(
            query="TEST_ERROR_HANDLING",
            location="INVALID_LOCATION_XYZ123",
            lookback_days=1,
            trigger_type="manual"
        )
        
        console.print(f"Status: {result.status}")
        console.print(f"Error: {result.error}")
        
        # Verify the run was created and has error message
        run = db.client.table("scrape_runs")\
            .select("*")\
            .eq("id", str(result.run_id))\
            .single()\
            .execute()
        
        if run.data:
            error_msg = run.data.get('error_message')
            if error_msg:
                console.print(f"✅ Error message saved: {error_msg[:100]}...")
            else:
                console.print(f"❌ No error message saved!")
                return False
            
            # Clean up
            db.client.table("scrape_runs").delete().eq("id", str(result.run_id)).execute()
        
        return True
    except Exception as e:
        console.print(f"❌ Unexpected exception: {e}")
        import traceback
        console.print(traceback.format_exc())
        return False


async def main():
    """Run all tests."""
    console.print(Panel.fit(
        "[bold green]Scrape Flow Test Suite[/bold green]\n"
        "Testing database, Bright Data connection, and error handling",
        border_style="green"
    ))
    
    results = []
    
    # Run tests
    results.append(("Database Connection", await test_database_connection()))
    results.append(("Bright Data Connection", await test_brightdata_connection()))
    results.append(("Scrape Run Creation", await test_scrape_run_creation()))
    results.append(("Error Handling", await test_error_handling()))
    
    # Summary
    console.print("\n" + "="*60)
    table = Table(title="Test Results", show_header=True)
    table.add_column("Test", style="cyan")
    table.add_column("Result", style="bold")
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        table.add_row(test_name, status)
        if result:
            passed += 1
    
    console.print(table)
    console.print(f"\n[bold]Total: {passed}/{len(results)} tests passed[/bold]")
    
    if passed == len(results):
        console.print("\n[bold green]✅ All tests passed! System is healthy.[/bold green]")
    else:
        console.print("\n[bold red]❌ Some tests failed. Check errors above.[/bold red]")


if __name__ == "__main__":
    asyncio.run(main())
