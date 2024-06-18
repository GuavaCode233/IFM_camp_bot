import re

user = "<@601014917746786335>"
print(re.match(r"^<@(\d+)>", user) is None)