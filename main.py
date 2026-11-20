from app.generator import generate

req = {"project_name": "demo-app", "region": "mumbai"}

files = generate(req)
print("Generated:", ", ".join(files))
