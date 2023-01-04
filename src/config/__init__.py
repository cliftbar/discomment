from pathlib import Path

from config.dc_config import DCServerConfig, DCAccountConfig, init_config, DCConfig

conf: DCConfig = init_config(Path("env.yml"))
server_conf: DCServerConfig = conf.server
account_conf: DCAccountConfig = conf.account
