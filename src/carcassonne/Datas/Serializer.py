import re


PLACEMENT_RE = re.compile(r"^(?P<target>\d+)(?P<side>[NESW])(?P<rot>[0-3])$")
MEEPLE_SET = {"N", "E", "S", "W"}



