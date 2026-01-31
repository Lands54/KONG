import typer
import sys
import os
from pathlib import Path
from rich import print
from rich.table import Table
from rich.console import Console
from rich.panel import Panel
from typing import Optional

# Ensure project root is in sys.path
# We assume this script is located at server/python/prism_cli.py
current_dir = Path(__file__).parent.absolute()
project_root = current_dir.parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

# Add core directory for kgforge
core_dir = project_root / "core"
if str(core_dir) not in sys.path:
    sys.path.append(str(core_dir))

# Add server/python directory for python_service
server_python_dir = project_root / "server" / "python"
if str(server_python_dir) not in sys.path:
    sys.path.append(str(server_python_dir))

# Try to import core components
try:
    from python_service.core.engine import engine
    from kgforge import get_logger
except ImportError as e:
    print(f"[bold red]Critical Error:[/bold red] Failed to import core components. {e}")
    print(f"PYTHONPATH: {sys.path}")
    sys.exit(1)

app = typer.Typer(
    name="PRISM CLI",
    help="Platform for Reasoning, Inference, and Semantic Modeling - Developer Console",
    add_completion=False
)
console = Console()

@app.command()
def ls(category: Optional[str] = typer.Option(None, "--category", "-c", help="Filter by component category")):
    """
    List all registered components in the system.
    """
    console.print("[bold blue]Scanning PRISM Component Registry...[/bold blue]")
    try:
        specs = engine.scan_all()
    except Exception as e:
        console.print(f"[bold red]Scan Failed:[/bold red] {e}")
        return

    table = Table(show_header=True, header_style="bold magenta", expand=True)
    table.add_column("Category", style="cyan", no_wrap=True)
    table.add_column("ID", style="green", no_wrap=True)
    table.add_column("Class Path", overflow="fold")
    table.add_column("Capabilities", overflow="fold")

    count = 0
    
    # Sort categories for consistent output
    sorted_categories = sorted(specs.keys())
    
    for cat in sorted_categories:
        if category and cat != category:
            continue
            
        components = specs[cat]
        for comp in components:
            capabilities = ", ".join(comp.get("capabilities", [])) if "capabilities" in comp else ""
            if comp.get("can_preload"):
                capabilities += " [bold yellow](Preload)[/bold yellow]"
                
            table.add_row(
                cat,
                comp["id"],
                comp.get("class_path", "N/A"),
                capabilities
            )
            count += 1

    console.print(table)
    console.print(f"\n[dim]Total Components: {count}[/dim]")

@app.command()
def doctor():
    """
    Diagnose the health of the PRISM environment.
    """
    console.print(Panel("[bold white]PRISM System Doctor[/bold white]", style="blue"))
    
    checks = []
    
    # 1. Check Project Root
    checks.append(("Project Root", str(project_root), "✅"))
    
    # 2. Check Critical Directories
    core_dir = project_root / "core" / "kgforge"
    if core_dir.exists():
        checks.append(("Core Module", str(core_dir), "✅"))
    else:
        checks.append(("Core Module", str(core_dir), "❌ [red]Missing[/red]"))

    # 3. Check .env
    env_file = project_root / ".env"
    if env_file.exists():
        checks.append(("Environment Config", ".env found", "✅"))
    else:
        checks.append(("Environment Config", ".env missing", "⚠️ [yellow]Using defaults[/yellow]"))
        
    # 4. Check Engine Import
    try:
        engine.scan_all()
        checks.append(("Component Engine", "Introspection functional", "✅"))
    except Exception as e:
        checks.append(("Component Engine", f"Scan failed: {e}", "❌"))

    # Print Report
    table = Table(show_header=False, box=None)
    table.add_column("Component", style="bold")
    table.add_column("Detail")
    table.add_column("Status")
    
    for name, detail, status in checks:
        table.add_row(name, detail, status)
        
    console.print(table)
    
    # 5. Check Dependencies (Simplified)
    console.print("\n[bold]Checking Key Dependencies:[/bold]")
    deps = ["fastapi", "uvicorn", "watchdog", "typer", "rich", "pydantic", "networkx"]
    for dep in deps:
        try:
            __import__(dep)
            console.print(f"  - {dep}: [green]Installed[/green]")
        except ImportError:
            console.print(f"  - {dep}: [red]Missing[/red]")

@app.command()
def test(
    component_id: str = typer.Argument(..., help="ID of the component to test"),
    input_text: Optional[str] = typer.Option(None, "--input", "-i", help="Input text for the component"),
    input_file: Optional[Path] = typer.Option(None, "--file", "-f", help="Read input from file"),
    params: Optional[str] = typer.Option(None, "--params", "-p", help="JSON string of component parameters"),
    method_name: Optional[str] = typer.Option(None, "--method", "-m", help="Method to invoke (defaults to __call__)"),
    raw_json: bool = typer.Option(False, "--json", "-j", help="Output raw JSON (useful for piping)")
):
    """
    Atomic Component Test: Instantiate and run a single component.
    Supports input from stdin (piping).
    """
    import json
    import inspect
    from typing import Dict, Any
    from python_service.core.factory import UnifiedFactory
    
    # 1. Resolve Input (Priority: --input > --file > stdin)
    content = ""
    if input_text:
        content = input_text
    elif input_file:
        if not input_file.exists():
            console.print(f"[bold red]Error:[/bold red] File {input_file} not found.")
            raise typer.Exit(code=1)
        content = input_file.read_text()
    elif not sys.stdin.isatty():
        # Check if stdin has data (piped)
        content = sys.stdin.read().strip()
    
    if not content and not raw_json:
         console.print("[yellow]Warning: No input provided (args or stdin). Using empty string.[/yellow]")

    # 2. Parse Params
    param_dict = {}
    if params:
        try:
            param_dict = json.loads(params)
        except json.JSONDecodeError:
            console.print(f"[bold red]Error:[/bold red] Invalid JSON in parameters.")
            raise typer.Exit(code=1)

    if not raw_json:
        console.print(f"[bold blue]Testing Component:[/bold blue] {component_id}")
    
    try:
        # 3. Instantiate (Find Category First)
        specs = engine.scan_all()
        target_category = None
        for cat, components in specs.items():
            for comp in components:
                if comp["id"] == component_id:
                    target_category = cat
                    break
            if target_category: break
            
        if not target_category:
            console.print(f"[bold red]Error:[/bold red] Component ID '{component_id}' not found in registry.")
            raise typer.Exit(code=1)

        if not raw_json:
            console.print(f"[dim]Category resolved: {target_category}[/dim]")
        
        instance = UnifiedFactory.create_component(target_category, component_id, params=param_dict)
        
        # 4. Resolve Method (User Driven > Callable > Error)
        method = None
        target_method_name = method_name
        
        if target_method_name:
            if not hasattr(instance, target_method_name):
                 console.print(f"[bold red]Error:[/bold red] Component does not have method '{target_method_name}'.")
                 # List available methods for help
                 methods = [m for m in dir(instance) if not m.startswith("_") and callable(getattr(instance, m))]
                 console.print(f"[dim]Available methods: {', '.join(methods)}[/dim]")
                 raise typer.Exit(code=1)
            method = getattr(instance, target_method_name)
        elif callable(instance):
            target_method_name = "__call__"
            method = instance
        else:
            # Try to help user by finding common methods
            candidates = []
            for m in ["run", "extract", "expand", "fuse", "decide"]:
                if hasattr(instance, m):
                    candidates.append(m)
            
            console.print(f"[bold red]Error:[/bold red] No method specified and object is not callable.")
            if candidates:
                console.print(f"[yellow]Tip:[/yellow] Try using one of: {', '.join([f'--method {c}' for c in candidates])}")
            raise typer.Exit(code=1)
            
        # 5. Smart Casting (Same as before)
        final_input = content
        try:
            sig = inspect.signature(method)
            first_param = list(sig.parameters.values())[0] if sig.parameters else None
            
            if first_param and first_param.annotation != inspect.Parameter.empty:
                type_hint = first_param.annotation
                type_name = getattr(type_hint, "__name__", str(type_hint))
                
                # Check for Graph/KGGraph
                if "Graph" in type_name or "KGGraph" in type_name:
                    if not raw_json: console.print(f"[dim]Smart Casting: Detected {type_name}, attempting JSON -> Graph conversion...[/dim]")
                    try:
                        import json
                        input_json = json.loads(content)
                        from kgforge.models.graph import Graph
                        if isinstance(input_json, dict):
                            # Fallback: try mapping dict keys to init
                            final_input = Graph(**input_json) 
                    except Exception as e:
                        if not raw_json: console.print(f"[yellow]Smart Cast Warning:[/yellow] Failed to cast to Graph ({e}). Passing raw string.")
                
                # Check for Dict
                elif type_name in ["dict", "Dict"]:
                     try:
                         final_input = json.loads(content)
                     except:
                         pass 

        except Exception as e:
            if not raw_json: console.print(f"[yellow]Introspection Warning:[/yellow] {e}")

        # Execute
        result = method(final_input)

        if not raw_json:
            console.print(f"[bold green]✓ Execution Successful ({target_method_name})[/bold green]")
        
        # 5. Format Output
        output_data = str(result)
        if hasattr(result, "to_dict"):
            output_data = result.to_dict()
        elif hasattr(result, "dict") and callable(result.dict): 
            output_data = result.dict()
            
        if raw_json:
            import json
            if isinstance(output_data, (dict, list)):
                print(json.dumps(output_data))
            else:
                print(f'"{output_data}"') 
        else:
            console.print(Panel(str(result), title="Output Result"))
            if isinstance(output_data, (dict, list)):
                 console.print("\n[bold]JSON Representation:[/bold]")
                 console.print_json(data=output_data)

    except Exception as e:
        if raw_json:
            print(f'{{"error": "{str(e)}"}}')
            sys.exit(1)
        else:
            console.print(f"[bold red]Execution Failed:[/bold red]")
            console.print_exception()

# --- Shared Execution Logic ---
def _execute_pipeline(config: dict, dev_mode: bool = False):
    """
    Internal helper to instantiate and run an orchestrator from config.
    """
    from python_service.core.factory import UnifiedFactory
    
    # 1. Parse Config
    orchestrator_id = config.get("orchestrator_id")
    if not orchestrator_id:
        console.print("[bold red]Error:[/bold red] Configuration missing 'orchestrator_id'.")
        raise typer.Exit(code=1)
        
    components_config = config.get("components", {})
    global_params = config.get("parameters", {})
    
    console.print(Panel(f"[bold]Orchestrator:[/bold] {orchestrator_id}\n[bold]Components:[/bold] {list(components_config.keys())}", title="Pipeline Configuration", border_style="blue"))

    try:
        # 2. Instantiate Orchestrator
        # Orchestrators are components too, usually in 'orchestrators' category
        specs = engine.scan_all()
        orch_cat = "orchestrators" # Default assumption
        
        # Verify orchestrator exists
        found = False
        for cat, comps in specs.items():
            for c in comps:
                if c["id"] == orchestrator_id:
                    orch_cat = cat
                    found = True
                    break
        
        if not found:
             console.print(f"[bold red]Error:[/bold red] Orchestrator '{orchestrator_id}' not found.")
             raise typer.Exit(code=1)

        # 3. Build Context (Component Injection)
        # Most Orchestrators expect components to be passed in params or init
        # We use the Factory's slot resolution or pass raw config depending on Orchestrator type
        # Ideally, we pass the ENTIRE config to the orchestrator and let it build itself, 
        # OR we build components here and pass them.
        
        # Strategy: Pass 'components' dict as a parameter to Orchestrator.
        # This assumes the Orchestrator knows how to instantiate them or they are just config inputs.
        # BUT: The standard KONG Orchestrators (like DynamicHalting) likely expect instantiated objects or a factory reference.
        
        # Let's align with `DynamicHaltingOrchestratorAppliance` found in standard components.
        # It likely takes `components` dict where keys are slot names and values are IDs.
        
        # Construct parameters for factory
        # We merge global params into the orchestrator params
        start_params = global_params.copy()
        start_params["components"] = components_config
        
        if dev_mode:
            console.print("[yellow]Dev Mode:[/yellow] Persistence disabled (simulated).")
            start_params["dev_mode"] = True

        instance = UnifiedFactory.create_component(orch_cat, orchestrator_id, params=start_params)
        
        # 4. Run
        console.print("[bold green]Starting Execution...[/bold green]")
        
        result = None
        if hasattr(instance, "run"):
             # Some orchestrators take 'goal' or initial state in run()
             # We pass all remaining config keys as kwargs, excluding reserved ones
             reserved = ["orchestrator_id", "components", "parameters"]
             run_kwargs = {k: v for k, v in config.items() if k not in reserved}
             
             result = instance.run(**run_kwargs)
        elif callable(instance):
             result = instance()
        else:
             console.print("[red]Orchestrator has no run() method and is not callable.[/red]")
             raise typer.Exit(code=1)
             
        # 5. Output
        console.print(Panel(str(result), title="Execution Result", border_style="green"))
        
    except Exception as e:
        console.print("[bold red]Pipeline Execution Failed:[/bold red]")
        console.print_exception()
        raise typer.Exit(code=1)

@app.command()
def rerun(
    experiment_id: str = typer.Argument(..., help="ID of the experiment to rerun"),
    dev: bool = typer.Option(False, "--dev", help="Run in dev mode (no persistence)")
):
    """
    Rerun an existing experiment by fetching its config from the running server.
    Requires the PRISM server to be running at localhost:8000.
    """
    import urllib.request
    import json
    
    api_url = f"http://localhost:8000/api/experiments/{experiment_id}"
    console.print(f"[bold blue]Fetching configuration for:[/bold blue] {experiment_id}")
    
    try:
        with urllib.request.urlopen(api_url) as response:
            if response.status != 200:
                console.print(f"[red]Error fetching experiment:[/red] HTTP {response.status}")
                return
            data = json.loads(response.read().decode())
            
            # Extract config from response structure
            # Assume response matches Experiment schema where 'configuration' field holds the pipeline config
            if "configuration" not in data:
                 console.print("[red]Invalid response:[/red] Missing 'configuration' field.")
                 console.print(data)
                 return
                 
            config = data["configuration"]
            _execute_pipeline(config, dev_mode=dev)
            
    except Exception as e:
        console.print(f"[bold red]Connection Failed:[/bold red] Is the server running? ({e})")
        raise typer.Exit(code=1)

@app.command()
def run(
    pipeline_file: Path = typer.Argument(..., help="Path to pipeline JSON configuration"),
    dev: bool = typer.Option(False, "--dev", help="Run in dev mode (no persistence)")
):
    """
    Execute a PRISM experiment headlessly from a configuration file.
    """
    import json
    
    if not pipeline_file.exists():
        console.print(f"[bold red]Error:[/bold red] File {pipeline_file} not found.")
        raise typer.Exit(code=1)
        
    try:
        config = json.loads(pipeline_file.read_text())
        _execute_pipeline(config, dev_mode=dev)
    except json.JSONDecodeError:
        console.print(f"[bold red]Error:[/bold red] Invalid JSON in {pipeline_file}.")
        raise typer.Exit(code=1)

@app.command()
def logs(
    follow: bool = typer.Option(False, "--follow", "-f", help="Follow log output"),
    lines: int = typer.Option(50, "--lines", "-n", help="Number of lines to show")
):
    """
    Stream logs from the running Python Service.
    Reads from .logs/python_service.log
    """
    import subprocess
    import shutil
    
    log_file = project_root / ".logs" / "python_service.log"
    
    if not log_file.exists():
        console.print(f"[yellow]Log file not found at {log_file}[/yellow]")
        console.print("Has the server been started with the new logging configuration?")
        # Try to create it to avoid tail error if it's just about to be created
        return

    console.print(f"[bold blue]Streaming logs from:[/bold blue] {log_file}")
    
    cmd = ["tail", f"-n{lines}"]
    if follow:
        cmd.append("-f")
    cmd.append(str(log_file))
    
    try:
        # Use subprocess to stream directly to stdout
        subprocess.run(cmd)
    except KeyboardInterrupt:
        console.print("\n[dim]Log stream stopped.[/dim]")
    except Exception as e:
        console.print(f"[bold red]Error streaming logs:[/bold red] {e}")

if __name__ == "__main__":
    app()
