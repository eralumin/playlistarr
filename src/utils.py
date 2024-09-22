import os


def get_env_variable(var_name, default=None):
    value = os.getenv(var_name)

    if value is None or value == "":
        if default is not None:
            return default

        raise EnvironmentError(
            f"The environment variable {var_name} is not set. Please configure it properly."
        )

    return value
