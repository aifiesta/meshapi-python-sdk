"""Live tests: Templates CRUD."""

from __future__ import annotations

import uuid

import pytest
from meshapi import MeshAPI, MeshAPIError
from meshapi._types import CreateTemplateParams, UpdateTemplateParams


def test_templates_crud_lifecycle(client: MeshAPI) -> None:
    name = f"py-livetest-{uuid.uuid4().hex[:8]}"
    template_id = None

    try:
        # Create
        tmpl = client.templates.create(
            CreateTemplateParams(
                name=name,
                description="Python SDK live test template",
                system="You are a helpful assistant.",
                variables=["topic"],
            )
        )
        template_id = tmpl.id
        assert tmpl.id, "template id should be non-empty"
        assert tmpl.owner, "template owner should be non-empty"

        # List — created template must appear
        templates = client.templates.list()
        ids = [t.id for t in templates]
        assert template_id in ids, "created template not found in list"

        # Get
        got = client.templates.get(template_id)
        assert got.id == template_id
        assert got.name == name

        # Update
        updated = client.templates.update(
            template_id,
            UpdateTemplateParams(description="Updated by Python SDK live test"),
        )
        assert updated.description == "Updated by Python SDK live test"

        # Delete
        client.templates.delete(template_id)
        template_id = None

        # Verify 404 after delete
        with pytest.raises(MeshAPIError) as exc_info:
            client.templates.get(tmpl.id)
        assert exc_info.value.status == 404

    finally:
        if template_id:
            try:
                client.templates.delete(template_id)
            except Exception:
                pass
