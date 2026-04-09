import json
import os
import re
import tempfile


def _slugify(value):
    normalized = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return normalized or "assistant"


def _assistant_file(root_directory, assistant_id):
    return os.path.join(root_directory, assistant_id, "assistant.json")


def _assistant_vector_directory(assistant_id):
    base_directory = os.path.join(tempfile.gettempdir(), "minor_project_assistant_dbs")
    os.makedirs(base_directory, exist_ok=True)
    return os.path.join(base_directory, assistant_id)


def assistant_exists(root_directory, assistant_name):
    assistant_id = _slugify(assistant_name)
    return os.path.exists(_assistant_file(root_directory, assistant_id))


def ensure_assistant(root_directory, assistant_name):
    assistant_id = _slugify(assistant_name)
    assistant_directory = os.path.join(root_directory, assistant_id)
    persist_directory = _assistant_vector_directory(assistant_id)
    os.makedirs(assistant_directory, exist_ok=True)
    os.makedirs(persist_directory, exist_ok=True)

    assistant_payload = {
        "assistant_id": assistant_id,
        "assistant_name": assistant_name.strip() or assistant_id,
        "persist_directory": persist_directory,
        "collection_name": "knowledge_base",
    }

    with open(_assistant_file(root_directory, assistant_id), "w", encoding="utf-8") as handle:
        json.dump(assistant_payload, handle, indent=2)

    return assistant_payload


def get_assistant_store(root_directory, assistant_name):
    assistant_id = _slugify(assistant_name)
    assistant_directory = os.path.join(root_directory, assistant_id)
    metadata_path = _assistant_file(root_directory, assistant_id)

    if not os.path.exists(metadata_path):
        raise FileNotFoundError(
            f"Assistant '{assistant_name}' does not exist. Create it before querying."
        )

    with open(metadata_path, "r", encoding="utf-8") as handle:
        assistant_payload = json.load(handle)

    assistant_payload["persist_directory"] = assistant_payload.get("persist_directory") or _assistant_vector_directory(assistant_id)
    return assistant_payload


def list_assistants(root_directory):
    if not os.path.exists(root_directory):
        return []

    assistants = []
    for entry in sorted(os.listdir(root_directory)):
        metadata_path = _assistant_file(root_directory, entry)
        if not os.path.exists(metadata_path):
            continue

        with open(metadata_path, "r", encoding="utf-8") as handle:
            assistants.append(json.load(handle))

    return assistants
