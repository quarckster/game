from dynaconf import Dynaconf

settings = Dynaconf(
    envvar_prefix="GAME", environments=True, settings_files=["settings.toml", ".secrets.toml"]
)
