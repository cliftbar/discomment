import yaml

from config.dc_config import DCServerConfig, DCAccountConfig

with open("env.yml") as env:
    env_vals: dict = yaml.safe_load(env)

    server_conf: DCServerConfig = DCServerConfig(**env_vals["server"])
    account_conf: DCAccountConfig = DCAccountConfig(**env_vals["account"])
