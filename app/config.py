from dynaconf import Dynaconf

settings = Dynaconf(envvar_prefix="GAME", settings_files=["settings.toml", ".secrets.toml"])
