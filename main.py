import sys

from app.pipeline import run

path = sys.argv[1] if len(sys.argv) > 1 else "samples/shop-site.yaml"

result = run(path)
print(result["report"])
print("Files:", ", ".join(result["files"]))
