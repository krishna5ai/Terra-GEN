from app.generator import generate

req = {
    "project_name": "demo-app",
    "region": "mumbai",
    "components": ["ec2", "rds", "s3"],   # vpc is added automatically
    "instance_type": "t3.micro",
    "db_engine": "mysql",
}

result = generate(req)
print("Components:", ", ".join(result["components"]))
print("Files     :", ", ".join(result["files"]))
