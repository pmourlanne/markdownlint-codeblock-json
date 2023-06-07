import argparse
import json
from pathlib import Path

CODEBLOCK_PREFIXES = [
    "```json",
    "```json-doc",
]


def is_markdown_file(filename):
    return Path(filename).suffix == ".md"


def remove_comments(line):
    stripped_line = line.strip()

    if stripped_line.startswith('...'):
        return None

    inside_quotes = False
    found_comment = False
    for character_idx, character in enumerate(line):
        if character == '"':
            inside_quotes = not inside_quotes
            continue

        if character == "#" and not inside_quotes:
            found_comment = True
            break

    if found_comment:
        return f"{line[:character_idx]}\n"

    return line


def find_json_codeblocks(filename, *, allow_comments=False):
    """
    When the `allow_comments` flag is true, we do two things:
        - We ignore lines starting with `...`
        - We ignore everything after a `#` that is not between double quotes

    For example, the following JSON:
    ```
        {
            "count": 95,  # Total number of orders
            "next": "http://api-sandbox.hokodo.co/v1/payment/orders/?limit=10&offset=60#heading",
            "previous": null,
            "results": [
                {
                    ... # 51st order in the list
                },
                {
                    ... # 52nd order in the list
                }
                ...
            ]
        }
    ```
    will be transformed into:
    ```
        {
            "count": 95,
            "next": "http://api-sandbox.hokodo.co/v1/payment/orders/?limit=10&offset=60#heading",
            "previous": null,
            "results": [
                {
                },
                {
                }
            ]
        }
    ```
    """

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
            if allow_comments:
                line = remove_comments(line)
                if line is None:
                    continue

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
    parser.add_argument("--allow-comments", action="store_true")
    args = parser.parse_args()

    exit_code = 0

    for filename in args.filenames:
        if is_markdown_file(filename):
            json_codeblocks = find_json_codeblocks(filename, allow_comments=args.allow_comments)

            for line_idx, json_codeblock in json_codeblocks:
                if error := parse_json_codeblock(json_codeblock):
                    exit_code = 1
                    print(f"{filename}:{line_idx}: {error}")

    exit(exit_code)


if __name__ == "__main__":
    main()
