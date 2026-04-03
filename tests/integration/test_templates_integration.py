"""Integration tests — templates CRUD."""

import os
import uuid

import pytest

from meshapi import MeshAPI
from meshapi._errors import MeshAPIError
from meshapi._types import CreateTemplateParams, TemplateSummary, UpdateTemplateParams

BASE_URL = os.getenv("MESHAPI_BASE_URL", "http://localhost:8000")
TOKEN = os.getenv("MESHAPI_TOKEN", "rsk_01KN96KQWDPF2X1E9CP8567JY4")


@pytest.fixture(scope="module")
def client():
    with MeshAPI(base_url=BASE_URL, token=TOKEN) as c:
        yield c


@pytest.fixture
def created_template(client: MeshAPI):
    unique_name = f"sdk-test-{uuid.uuid4().hex[:8]}"
    tmpl = client.templates.create(
        CreateTemplateParams(
            name=unique_name,
            description="Integration test template",
            system="You are a test assistant.",
        )
    )
    yield tmpl
    # Cleanup
    try:
        client.templates.delete(tmpl.id)
    except MeshAPIError:
        pass


def test_template_create(created_template: TemplateSummary):
    assert created_template.id
    assert created_template.owner
    assert created_template.system == "You are a test assistant."


def test_template_list_includes_created(client: MeshAPI, created_template: TemplateSummary):
    templates = client.templates.list()
    ids = [t.id for t in templates]
    assert created_template.id in ids


def test_template_get(client: MeshAPI, created_template: TemplateSummary):
    tmpl = client.templates.get(created_template.id)
    assert tmpl.id == created_template.id
    assert tmpl.name == created_template.name


def test_template_update(client: MeshAPI, created_template: TemplateSummary):
    updated = client.templates.update(
        created_template.id,
        UpdateTemplateParams(description="Updated description"),
    )
    assert updated.description == "Updated description"
    assert updated.id == created_template.id


def test_template_delete(client: MeshAPI):
    unique_name = f"sdk-del-{uuid.uuid4().hex[:8]}"
    tmpl = client.templates.create(CreateTemplateParams(name=unique_name))
    client.templates.delete(tmpl.id)
    with pytest.raises(MeshAPIError) as exc_info:
        client.templates.get(tmpl.id)
    assert exc_info.value.status == 404
