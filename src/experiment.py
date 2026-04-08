# This file is about: (running episodes, parsing output, creating dataframes and saving the results...). That is experiment logic
from io_module.parser import Parser


def run_and_parse_output(env, episode, file):
    env.run_episode(episode)
    return Parser(file).parse_episode(episode)
