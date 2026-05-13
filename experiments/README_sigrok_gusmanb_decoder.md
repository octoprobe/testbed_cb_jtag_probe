# gusmanb: How sigrok decoders are integrated

## The load path is:

1. During publish, the project copies the source decoder tree from LogicAnalyzer.csproj into the application’s runtime output under a decoders folder. The actual copy source is LogicAnalyzer.csproj, and the destination is LogicAnalyzer.csproj. So at runtime it is not reading directly from Software/decoders in-place; it is reading the published copy of that tree.

2. The bridge defines that runtime folder as DecoderPath in SigrokPythonEngine.cs. During initialization it also writes an embedded helper module called sigrokdecode.py into that same folder at SigrokPythonEngine.cs and appends DecoderPath to Python’s import path at SigrokPythonEngine.cs. That is what makes each decoder directory importable from Python.

3. The first time someone accesses the provider’s decoder list, the lazy property in SigrokProvider.cs calls GetDecoders at SigrokProvider.cs. That method enumerates all subdirectories under DecoderPath at SigrokProvider.cs, and only keeps folders that contain a pd.py file. In sigrok terms, each such folder is one decoder module.

4. For each valid folder, it generates a tiny C# wrapper class from the template in CodeTemplates.cs. The wrapper only overrides decoderName, which is the Python module name to import. All wrappers are compiled together in memory into a temporary assembly by GetDecoders.

5. Each generated wrapper is instantiated. The real Python import happens in the base-class constructor at SigrokDecoderBase.cs: it executes import at SigrokDecoderBase.cs, creates the Python Decoder object at SigrokDecoderBase.cs, and binds the C# object back into Python at SigrokDecoderBase.cs. After that, the C# object can read metadata like channels, options, inputs, outputs, and categories from the Python decoder.

The variable that eventually holds all decoders is the private field in SigrokProvider.cs: decoders. That is the long-lived cache for the provider.

There is also one temporary accumulator during loading: loadedAnalyzers in SigrokProvider.cs. GetDecoders fills that list, returns it as an array at SigrokProvider.cs, and that returned array is assigned to decoders the first time the Decoders property runs.

So, in short:

- Temporary during construction: loadedAnalyzers
- Final cached variable with all loaded decoders: decoders
- Public access point callers use: Decoders

If you want, I can trace one concrete decoder folder from Software/decoders all the way to its instantiated C# wrapper and show the exact names involved.

## I’m tracing the `jtag` decoder end to end

I’m tracing the `jtag` decoder end to end: source files, published module name, generated wrapper, and the Python class instance that the bridge creates.

For jtag, the trace is very direct.

At the source level, the module is the folder Software/decoders/jtag. Its __init__.py does `from .pd import Decoder`, so importing `jtag` exposes the Python class `jtag.Decoder`. The actual decoder metadata lives in pd.py: `id = 'jtag'`, `name = 'JTAG'`, `longname = 'Joint Test Action Group (IEEE 1149.1)'`, `inputs = ['logic']`, `outputs = ['jtag']`, required channels at pd.py, and optional channels at pd.py.

On the C# side, `SigrokProvider.GetDecoders()` scans every subdirectory under the runtime decoders folder in SigrokProvider.cs. Since `jtag` contains a pd.py, it qualifies. The provider then generates one wrapper class from the template in CodeTemplates.cs. For `jtag`, that generated class is effectively:

```csharp
public class Decoderjtag : SigrokDecoderBase
{
    protected override string decoderName => "jtag";
}
```

That matters because the base constructor in SigrokDecoderBase.cs uses `decoderName` to import Python. For this instance, it executes `import jtag` at SigrokDecoderBase.cs, creates `jtag.Decoder()` at SigrokDecoderBase.cs, then attaches the current C# object back into Python via `decoder.cObj = this.ToPython()` at SigrokDecoderBase.cs. After that, the bridge pulls metadata from the Python object and exposes it through C# properties like `DecoderName`, `Inputs`, `Outputs`, `Channels`, and options.

So the concrete path for `jtag` is:

1. Software/decoders/jtag/pd.py defines `class Decoder`.
2. The app publishes that folder into its runtime `decoders/jtag` directory.
3. `SigrokProvider` sees the `jtag` directory and generates `Decoderjtag`.
4. Instantiating `Decoderjtag` causes `import jtag` and `jtag.Decoder()`.
5. That instance is added to `loadedAnalyzers` in SigrokProvider.cs, and then ends up in the cached `decoders` field in SigrokProvider.cs.

For `jtag` specifically, the user-visible names after loading are not the folder name. `GetDecoder("jtag")` would not match, because `GetDecoder` compares against `DecoderName`, and `DecoderName` returns `decoder.longname`, which here is `Joint Test Action Group (IEEE 1149.1)` from pd.py. The short sigrok name is available separately through `DecoderShortName`, which would be `JTAG` from pd.py.

If you want, I can next trace how `jtag`’s `outputs = ['jtag']` flows into downstream stacked decoders during execution.


## which C# executable owns the decoder bridge

I’m identifying which C# executable owns the decoder bridge and then checking whether the decoder path can be redirected through config or command-line handling.

I found only one application instantiating the decoder bridge so far; I’m reading its startup and window initialization to confirm ownership and how configuration is handled.

Searched for regex `python.cfg|DecoderPath|BasePath|GetCommandLineArgs|args\)|StartWithClassicDesktopLifetime\(args\)` (`**/Software/LogicAnalyzer/LogicAnalyzer/**`), 11 results

Read [](file:///workspaces/logicanalyzer/Software/LogicAnalyzer/LogicAnalyzer/Program.cs)

Read [](file:///workspaces/logicanalyzer/Software/LogicAnalyzer/LogicAnalyzer/MainWindow.axaml.cs#130-130), lines 130 to 175

The ownership is now narrow: the GUI app `LogicAnalyzer` creates `SigrokProvider`; the terminal and CLI projects parse command lines, but they do not use the sigrok bridge.The decoders are owned by the GUI application in Software/LogicAnalyzer/LogicAnalyzer, not by the CLI tools.

The startup entry point is Program.cs, which launches the Avalonia desktop app. Inside the main window initialization, that app creates the decoder bridge with `new SigrokProvider()` in MainWindow.axaml.cs. Right after that it passes the provider into the decoder UI manager with `sgManager.Initialize(decoderProvider)` in MainWindow.axaml.cs. I did not find any other C# application in the workspace constructing `SigrokProvider`, so the sigrok decoder system is effectively part of the `LogicAnalyzer` desktop app.

On configuration: the decoder set itself is not currently configurable through a config file or command-line parameter. The runtime decoder location is hardcoded as `Path.Combine(BasePath, "decoders")` in SigrokPythonEngine.cs, and `SigrokProvider` always enumerates that directory in SigrokProvider.cs. There is no code path that reads a decoder-directory setting from a JSON file, app settings, environment variable, or command-line argument.

There is one related configuration file, but it is only for Python, not for choosing decoders: SigrokPythonEngine.cs reads `python.cfg` from the app base directory to find the Python library path. The UI error message in MainWindow.axaml.cs confirms that purpose. So today:

- `python.cfg` can influence which Python runtime gets loaded.
- The decoder directory cannot be redirected by config.
- The GUI app does receive `args` in Program.cs, but there is no parser or handling for decoder-related command-line options.

One more practical detail: the actual decoder files are packaged by the `LogicAnalyzer` project itself during publish, via the `CopyDecoders` target in LogicAnalyzer.csproj. That target copies Software/decoders into the published app’s `decoders` folder, which is exactly the folder the bridge scans at runtime.

If you want, I can show the smallest code change needed to make the decoder path configurable by `python.cfg`, a new `decoders.cfg`, or a command-line switch.
