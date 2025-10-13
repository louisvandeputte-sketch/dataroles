#!/usr/bin/env python3
"""Test LinkedIn Pydantic models with sample data."""

import json
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from models.linkedin import (
    LinkedInJobPosting,
    LinkedInBaseSalary,
    LinkedInLocation,
    LinkedInCompany
)
from uuid import uuid4

console = Console()


def test_salary_parsing():
    """Test salary parsing from different formats."""
    console.print("\n[bold cyan]Testing Salary Parsing...[/bold cyan]")
    
    test_cases = [
        ("$120,000.00/yr - $150,000.00/yr", "$", 120000.0, 150000.0, "yr"),
        ("$70,000.00/yr - $90,000.00/yr", "$", 70000.0, 90000.0, "yr"),
        ("$15.50/hr - $18.00/hr", "$", 15.5, 18.0, "hr"),
        ("€50,000/yr - €60,000/yr", "€", 50000.0, 60000.0, "yr"),
    ]
    
    table = Table(title="Salary Parsing Results")
    table.add_column("Input", style="cyan")
    table.add_column("Currency", style="white")
    table.add_column("Min", style="green")
    table.add_column("Max", style="green")
    table.add_column("Period", style="yellow")
    table.add_column("Status", style="green")
    
    all_passed = True
    for salary_str, expected_currency, expected_min, expected_max, expected_period in test_cases:
        salary = LinkedInBaseSalary.from_string(salary_str)
        
        if salary:
            passed = (
                salary.currency == expected_currency and
                salary.min_amount == expected_min and
                salary.max_amount == expected_max and
                salary.payment_period == expected_period
            )
            status = "✓" if passed else "✗"
            all_passed = all_passed and passed
            
            table.add_row(
                salary_str[:30] + "...",
                salary.currency or "N/A",
                f"{salary.min_amount:,.2f}",
                f"{salary.max_amount:,.2f}",
                salary.payment_period or "N/A",
                status
            )
        else:
            table.add_row(salary_str, "N/A", "N/A", "N/A", "N/A", "✗")
            all_passed = False
    
    console.print(table)
    return all_passed


def test_location_parsing():
    """Test location parsing from different formats."""
    console.print("\n[bold cyan]Testing Location Parsing...[/bold cyan]")
    
    test_cases = [
        ("Amsterdam, North Holland, Netherlands", "Amsterdam", "North Holland", None),
        ("New York, NY", "New York", "NY", "NY"),
        ("San Francisco, CA", "San Francisco", "CA", "CA"),
        ("London, England, United Kingdom", "London", "England", None),
        ("Chicago, IL", "Chicago", "IL", "IL"),
    ]
    
    table = Table(title="Location Parsing Results")
    table.add_column("Input", style="cyan")
    table.add_column("City", style="white")
    table.add_column("Region", style="white")
    table.add_column("Country Code", style="white")
    table.add_column("Status", style="green")
    
    all_passed = True
    for loc_str, expected_city, expected_region, expected_country in test_cases:
        location = LinkedInLocation.from_string(loc_str)
        
        passed = (
            location.city == expected_city and
            location.region == expected_region and
            location.country_code == expected_country
        )
        status = "✓" if passed else "✗"
        all_passed = all_passed and passed
        
        table.add_row(
            loc_str,
            location.city or "N/A",
            location.region or "N/A",
            location.country_code or "N/A",
            status
        )
    
    console.print(table)
    return all_passed


def test_job_parsing():
    """Test parsing of sample LinkedIn jobs."""
    console.print("\n[bold cyan]Testing Job Parsing...[/bold cyan]")
    
    # Load sample data
    sample_file = Path("tests/fixtures/linkedin_jobs_sample.json")
    if not sample_file.exists():
        console.print("[red]✗ Sample file not found![/red]")
        return False
    
    with open(sample_file) as f:
        jobs_data = json.load(f)
    
    table = Table(title="Job Parsing Results")
    table.add_column("Job ID", style="cyan")
    table.add_column("Title", style="white")
    table.add_column("Company", style="white")
    table.add_column("Location", style="white")
    table.add_column("Salary", style="green")
    table.add_column("Status", style="green")
    
    all_passed = True
    parsed_jobs = []
    
    for job_data in jobs_data:
        try:
            job = LinkedInJobPosting(**job_data)
            parsed_jobs.append(job)
            
            # Test extraction methods
            company = job.get_company()
            location = job.get_location()
            salary = job.get_salary()
            
            salary_str = "N/A"
            if salary:
                salary_str = f"{salary.currency}{salary.min_amount:,.0f}-{salary.max_amount:,.0f}/{salary.payment_period}"
            
            table.add_row(
                job.job_posting_id,
                job.job_title[:30] + "...",
                company.name[:20] + "...",
                location.city or location.full_location_string[:20],
                salary_str,
                "✓"
            )
        except Exception as e:
            table.add_row(
                job_data.get("job_posting_id", "unknown"),
                "ERROR",
                "ERROR",
                "ERROR",
                "ERROR",
                f"✗ {str(e)[:20]}"
            )
            all_passed = False
    
    console.print(table)
    console.print(f"\n[bold]Parsed {len(parsed_jobs)}/{len(jobs_data)} jobs successfully[/bold]")
    
    return all_passed, parsed_jobs


def test_db_dict_conversion(jobs):
    """Test conversion to database format."""
    console.print("\n[bold cyan]Testing Database Dict Conversion...[/bold cyan]")
    
    if not jobs:
        console.print("[yellow]No jobs to test[/yellow]")
        return False
    
    job = jobs[0]  # Test first job
    
    # Generate dummy UUIDs
    company_id = uuid4()
    location_id = uuid4()
    job_id = uuid4()
    
    try:
        # Test job posting dict
        job_dict = job.to_db_dict(company_id, location_id)
        console.print("[green]✓ Job posting dict created[/green]")
        console.print(f"  Fields: {len(job_dict)}")
        
        # Test company dict
        company = job.get_company()
        company_dict = company.to_db_dict()
        console.print("[green]✓ Company dict created[/green]")
        console.print(f"  Fields: {len(company_dict)}")
        
        # Test location dict
        location = job.get_location()
        location_dict = location.to_db_dict()
        console.print("[green]✓ Location dict created[/green]")
        console.print(f"  Fields: {len(location_dict)}")
        
        # Test description dict
        desc_dict = job.get_description_dict(job_id)
        console.print("[green]✓ Description dict created[/green]")
        console.print(f"  Fields: {len(desc_dict)}")
        
        # Test poster dict if available
        poster = job.get_poster()
        if poster:
            poster_dict = poster.to_db_dict(job_id)
            console.print("[green]✓ Poster dict created[/green]")
            console.print(f"  Fields: {len(poster_dict)}")
        
        # Validate required fields
        required_job_fields = ["linkedin_job_id", "company_id", "location_id", "title", "job_url"]
        missing = [f for f in required_job_fields if f not in job_dict]
        
        if missing:
            console.print(f"[red]✗ Missing required fields: {missing}[/red]")
            return False
        
        console.print("[green]✓ All required fields present[/green]")
        return True
        
    except Exception as e:
        console.print(f"[red]✗ Conversion failed: {e}[/red]")
        return False


def main():
    """Run all tests."""
    console.print(Panel.fit(
        "[bold blue]LinkedIn Pydantic Models Test[/bold blue]",
        border_style="blue"
    ))
    
    results = []
    
    # Test salary parsing
    results.append(("Salary Parsing", test_salary_parsing()))
    
    # Test location parsing
    results.append(("Location Parsing", test_location_parsing()))
    
    # Test job parsing
    job_result, jobs = test_job_parsing()
    results.append(("Job Parsing", job_result))
    
    # Test DB dict conversion
    results.append(("DB Dict Conversion", test_db_dict_conversion(jobs)))
    
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
            "[bold green]✓ All Tests Passed![/bold green]",
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
