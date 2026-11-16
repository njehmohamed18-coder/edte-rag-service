import typer
import httpx
from pathlib import Path
from rich.console import Console

app = typer.Typer(help="EDTE Semantic GraphRAG Command Line Interface")
console = Console()
API_BASE = "http://127.0.0.1:8000/api/v1/rag"


@app.command()
def ingest(file_path: Path) -> None:
    """Upload a Markdown or PDF document to the GraphRAG engine."""
    if not file_path.exists():
        console.print(f"[red]Error: File {file_path} does not exist.[/red]")
        raise typer.Exit(code=1)

    with open(file_path, "rb") as f:
        files = {"file": (file_path.name, f)}
        with console.status(f"Ingesting {file_path.name}..."):
            response = httpx.post(f"{API_BASE}/ingest/file", files=files, timeout=60.0)
    
    if response.status_code == 200:
        console.print("[green]Ingestion successful![/green]")
        console.print(response.json())
    else:
        console.print(f"[red]Failed: {response.text}[/red]")


@app.command()
def query(question: str, top_k: int = 3, hops: int = 1) -> None:
    """Ask a question against the ingested graph context."""
    payload = {"question": question, "top_k": top_k, "expand_graph_hops": hops}
    
    with console.status("Querying GraphRAG Engine..."):
        response = httpx.post(f"{API_BASE}/query", json=payload, timeout=60.0)
        
    if response.status_code == 200:
        data = response.json()
        console.print("\n[bold cyan]Answer:[/bold cyan]")
        console.print(data.get("answer"))
        console.print("\n[bold yellow]Graph Context Retrieved:[/bold yellow]")
        for item in data.get("graph_context", []):
            console.print(f"- {item['entity_urn']} ({item['connection_type']})")
    else:
        console.print(f"[red]Failed: {response.text}[/red]")


if __name__ == "__main__":
    app()
