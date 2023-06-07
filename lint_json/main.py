import argparse
import json
from pathlib import Path

CODEBLOCK_PREFIXES = [
    "```json",
    "```json-doc",
]


def is_markdown_file(filename):
    return Path(filename).suffix == ".md"


def find_json_codeblocks(filename):
    with open(filename) as f:
        lines = f.readlines()

    # List of tuple: (starting line, codeblock string)
    codeblock_strings = []
    within_codeblock = False

    # Line idx start at 1 instead of 0
    for line_idx, line in enumerate(lines, start=1):
        stripped_line = line.strip()

        if stripped_line in CODEBLOCK_PREFIXES and not within_codeblock:
            current_starting_line_idx = line_idx
            current_codeblock_string = []
            within_codeblock = True
            continue

        if stripped_line == "```" and within_codeblock:
            codeblock_strings.append(
                (
                    current_starting_line_idx,
                    "".join(current_codeblock_string),
                )
            )
            within_codeblock = False
            continue

        if within_codeblock:
            current_codeblock_string.append(line)

    return codeblock_strings


def parse_json_codeblock(codeblock_string):
    try:
        json.loads(codeblock_string)
    except json.decoder.JSONDecodeError as e:
        return str(e)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("filenames", nargs="*")
    args = parser.parse_args()

    exit_code = 0

    for filename in args.filenames:
        if is_markdown_file(filename):
            json_codeblocks = find_json_codeblocks(filename)

            for line_idx, json_codeblock in json_codeblocks:
                if error := parse_json_codeblock(json_codeblock):
                    exit_code = 1
                    print(f"{filename}:{line_idx}: {error}")

    exit(exit_code)


if __name__ == "__main__":
    main()
