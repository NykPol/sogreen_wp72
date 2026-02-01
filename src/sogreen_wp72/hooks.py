"""Project hooks for registering custom OmegaConf resolvers."""
from kedro.framework.hooks import hook_impl
from omegaconf import OmegaConf


class ProjectHooks:
    """A hook to register custom OmegaConf resolvers."""

    @hook_impl
    def register_config_loader(self, conf_paths, env, extra_params):
        """Register a custom resolver to access parameters in catalog.
        
        This allows using ${params:key} in catalog.yml to reference
        parameters from parameters.yml files without duplication.
        """
        return None  # Use default config loader
    
    @hook_impl  
    def after_context_created(self, context):
        """Register custom resolver after context is created."""
        # Register a resolver to access parameters
        if not OmegaConf.has_resolver("params"):
            OmegaConf.register_new_resolver(
                "params",
                lambda key: context.params.get(key),
                replace=True
            )
