import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_generate():
    print("\nTesting /api/specs/generate...")
    payload = {
        "requirements_text": "We need a project management tool. Users can create projects, add tasks, and assign members.",
        "options": {
            "include_examples": True
        }
    }
    start = time.time()
    response = requests.post(f"{BASE_URL}/api/specs/generate", json=payload)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Trace ID: {data['trace_id']}")
        print(f"Modules: {len(data['spec']['modules'])}")
        return data['trace_id'], data['spec']
    else:
        print(f"Error: {response.text}")
        return None, None

def test_refine(trace_id, existing_spec):
    print("\nTesting /api/specs/refine...")
    payload = {
        "trace_id": trace_id,
        "existing_spec": existing_spec,
        "refinement_instructions": "Add email notifications for task assignment."
    }
    response = requests.post(f"{BASE_URL}/api/specs/refine", json=payload)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"New Trace ID: {data['trace_id']}")
        print(f"Version: {data['version']}")
        return data['trace_id']
    else:
        print(f"Error: {response.text}")
        return None

def test_history(trace_id):
    print(f"\nTesting /api/specs/{trace_id}/history...")
    response = requests.get(f"{BASE_URL}/api/specs/{trace_id}/history")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Versions found: {len(data['versions'])}")
        for v in data['versions']:
            print(f" - Version {v['version']}: {v['timestamp']}")
    else:
        print(f"Error: {response.text}")

if __name__ == "__main__":
    print(f"Checking health...")
    try:
        health = requests.get(f"{BASE_URL}/health")
        print(f"Health: {health.json()}")
    except Exception as e:
        print(f"Backend not reachable: {e}")
        exit(1)

    trace_id, spec = test_generate()
    if trace_id and spec:
        test_refine(trace_id, spec)
        test_history(trace_id)
