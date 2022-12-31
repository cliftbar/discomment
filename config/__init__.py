import yaml

with open("env.yml") as env:
    env_vals: dict = yaml.safe_load(env)
