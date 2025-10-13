#!/usr/bin/env python3
"""Test all database CRUD operations."""

from database import db
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from datetime import datetime
from uuid import UUID

console = Console()

def test_companies():
    """Test company operations."""
    console.print("\n[bold cyan]Testing Companies...[/bold cyan]")
    
    # Test insert
    company_data = {
        "linkedin_company_id": "test-company-123",
        "name": "Test Tech Corp",
        "industry": "Information Technology",
        "company_url": "https://linkedin.com/company/test-tech",
        "employee_count_range": "51-200"
    }
    
    try:
        # Test upsert (insert)
        company_id = db.upsert_company(company_data)
        console.print(f"✓ Company inserted: {company_id}")
        
        # Test get by linkedin_id
        company = db.get_company_by_linkedin_id("test-company-123")
        if company:
            console.print(f"✓ Company retrieved: {company['name']}")
        
        # Test upsert (update)
        company_data["name"] = "Test Tech Corp Updated"
        company_id_2 = db.upsert_company(company_data)
        console.print(f"✓ Company upserted: {company_id_2}")
        
        return company_id
    except Exception as e:
        console.print(f"[red]✗ Company test failed: {e}[/red]")
        return None


def test_locations():
    """Test location operations."""
    console.print("\n[bold cyan]Testing Locations...[/bold cyan]")
    
    location_data = {
        "full_location_string": "Amsterdam, North Holland, Netherlands",
        "city": "Amsterdam",
        "region": "North Holland",
        "country_code": "NL"
    }
    
    try:
        # Test insert
        location_id = db.insert_location(location_data)
        console.print(f"✓ Location inserted: {location_id}")
        
        # Test get by string
        location = db.get_location_by_string("Amsterdam, North Holland, Netherlands")
        if location:
            console.print(f"✓ Location retrieved: {location['city']}")
        
        return location_id
    except Exception as e:
        console.print(f"[red]✗ Location test failed: {e}[/red]")
        return None


def test_job_postings(company_id: UUID, location_id: UUID):
    """Test job posting operations."""
    console.print("\n[bold cyan]Testing Job Postings...[/bold cyan]")
    
    job_data = {
        "linkedin_job_id": "test-job-456",
        "company_id": str(company_id),
        "location_id": str(location_id),
        "title": "Senior Data Engineer",
        "seniority_level": "Mid-Senior level",
        "employment_type": "Full-time",
        "industries": ["Information Technology"],
        "function_areas": ["Engineering"],
        "posted_date": datetime.utcnow().isoformat(),
        "num_applicants": 42,
        "job_url": "https://linkedin.com/jobs/view/test-job-456",
        "is_active": True
    }
    
    try:
        # Test insert
        job_id = db.insert_job_posting(job_data)
        console.print(f"✓ Job posting inserted: {job_id}")
        
        # Test get by linkedin_id
        job = db.get_job_by_linkedin_id("test-job-456")
        if job:
            console.print(f"✓ Job retrieved: {job['title']}")
        
        # Test update
        db.update_job_posting(job_id, {"num_applicants": 100})
        console.print(f"✓ Job updated")
        
        return job_id
    except Exception as e:
        console.print(f"[red]✗ Job posting test failed: {e}[/red]")
        return None


def test_job_description(job_id: UUID):
    """Test job description operations."""
    console.print("\n[bold cyan]Testing Job Descriptions...[/bold cyan]")
    
    desc_data = {
        "job_posting_id": str(job_id),
        "summary": "We are looking for a Senior Data Engineer...",
        "full_description_text": "Full description here...",
        "full_description_html": "<div>Full description here...</div>"
    }
    
    try:
        desc_id = db.insert_job_description(desc_data)
        console.print(f"✓ Job description inserted: {desc_id}")
        return desc_id
    except Exception as e:
        console.print(f"[red]✗ Job description test failed: {e}[/red]")
        return None


def test_scrape_runs():
    """Test scrape run operations."""
    console.print("\n[bold cyan]Testing Scrape Runs...[/bold cyan]")
    
    run_data = {
        "search_query": "data engineer",
        "location_query": "Netherlands",
        "platform": "linkedin_brightdata",
        "status": "running",
        "metadata": {"test": True}
    }
    
    try:
        # Create run
        run_id = db.create_scrape_run(run_data)
        console.print(f"✓ Scrape run created: {run_id}")
        
        # Update run
        db.update_scrape_run(run_id, {
            "status": "completed",
            "completed_at": datetime.utcnow().isoformat(),
            "jobs_found": 10,
            "jobs_new": 5
        })
        console.print(f"✓ Scrape run updated")
        
        # Get runs
        runs = db.get_scrape_runs(limit=5)
        console.print(f"✓ Retrieved {len(runs)} scrape runs")
        
        return run_id
    except Exception as e:
        console.print(f"[red]✗ Scrape run test failed: {e}[/red]")
        return None


def test_scrape_history(job_id: UUID, run_id: UUID):
    """Test scrape history operations."""
    console.print("\n[bold cyan]Testing Scrape History...[/bold cyan]")
    
    try:
        db.insert_scrape_history(job_id, run_id)
        console.print(f"✓ Scrape history inserted")
    except Exception as e:
        console.print(f"[red]✗ Scrape history test failed: {e}[/red]")


def test_statistics():
    """Test statistics operations."""
    console.print("\n[bold cyan]Testing Statistics...[/bold cyan]")
    
    try:
        stats = db.get_stats()
        
        table = Table(title="Database Statistics")
        table.add_column("Metric", style="cyan")
        table.add_column("Count", style="green")
        
        for key, value in stats.items():
            table.add_row(key.replace("_", " ").title(), str(value))
        
        console.print(table)
        console.print(f"✓ Statistics retrieved")
    except Exception as e:
        console.print(f"[red]✗ Statistics test failed: {e}[/red]")


def test_search_jobs():
    """Test job search operations."""
    console.print("\n[bold cyan]Testing Job Search...[/bold cyan]")
    
    try:
        jobs, total = db.search_jobs(
            search_query="engineer",
            active_only=True,
            limit=10
        )
        console.print(f"✓ Found {total} jobs, retrieved {len(jobs)}")
    except Exception as e:
        console.print(f"[red]✗ Job search test failed: {e}[/red]")


def main():
    """Run all tests."""
    console.print(Panel.fit(
        "[bold blue]Database CRUD Operations Test[/bold blue]",
        border_style="blue"
    ))
    
    # Test connection
    if not db.test_connection():
        console.print("[red]✗ Database connection failed![/red]")
        return
    
    console.print("[green]✓ Database connection successful[/green]")
    
    # Run tests
    company_id = test_companies()
    location_id = test_locations()
    
    if company_id and location_id:
        job_id = test_job_postings(company_id, location_id)
        
        if job_id:
            test_job_description(job_id)
            run_id = test_scrape_runs()
            
            if run_id:
                test_scrape_history(job_id, run_id)
    
    test_statistics()
    test_search_jobs()
    
    console.print("\n" + "="*60)
    console.print(Panel.fit(
        "[bold green]✓ All CRUD Operations Tested![/bold green]",
        border_style="green"
    ))


if __name__ == "__main__":
    main()
