import importlib
import pkgutil

telliot_plugins = {
    name: importlib.import_module(name) for finder, name, ispkg in pkgutil.iter_modules() if name.startswith("telliot_")
}
telliot_plugins.pop("telliot_core")
