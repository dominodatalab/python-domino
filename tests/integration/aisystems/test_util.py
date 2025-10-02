import domino.aisystems.tracing.inittracing as inittracing

def reset_prod_tracing():
        inittracing._is_prod_tracing_initialized = False

