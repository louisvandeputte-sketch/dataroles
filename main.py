"""CLI entrypoint for DataRoles - will be implemented in later phases."""

import click
from rich.console import Console

console = Console()


@click.group()
def cli():
    """DataRoles - Job Aggregation Platform CLI"""
    pass


@cli.command()
def version():
    """Show version information."""
    console.print("[bold blue]DataRoles[/bold blue] v0.1.0")
    console.print("Job Aggregation Platform")


if __name__ == "__main__":
    cli()
