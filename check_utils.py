import inspect
import importlib
import pkgutil

# First, try to import the module
try:
    import quotexpy
    print("Successfully imported quotexpy")
    
    # Check the utils module
    print("\nContents of quotexpy.utils:")
    import quotexpy.utils
    for item in dir(quotexpy.utils):
        if not item.startswith('__'):
            print(f"- {item}")
    
    # Check all modules in utils
    print("\nAll modules in quotexpy.utils:")
    for _, name, _ in pkgutil.iter_modules(quotexpy.utils.__path__):
        print(f"- {name}")
        
    # Check if there's a run or async_run function elsewhere
    print("\nSearching for run/async functions:")
    for module_name in dir(quotexpy):
        if not module_name.startswith('__'):
            try:
                module = getattr(quotexpy, module_name)
                if inspect.ismodule(module):
                    for func_name in dir(module):
                        if 'run' in func_name.lower() and not func_name.startswith('__'):
                            print(f"- Found in quotexpy.{module_name}: {func_name}")
            except:
                pass
    
except ImportError as e:
    print(f"Error importing quotexpy: {e}") 