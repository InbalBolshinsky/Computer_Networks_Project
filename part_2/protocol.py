from dataclasses import dataclass

@dataclass
class ParsedMessage:
    cmd: str
    args: str

def parse_line(line: str) -> ParsedMessage:
    line = line.strip()
    if not line:
        return ParsedMessage(cmd="", args="")

    parts = line.split(" ", 1)
    cmd = parts[0].upper()
    args = parts[1] if len(parts) > 1 else ""
    return ParsedMessage(cmd=cmd, args=args)